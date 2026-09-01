"""Cross-repository Governed Developer OS harness v3.

This harness invokes the certified kernel-side Agentic Runner as a separate
process. It pins the kernel repository to an exact commit before invocation.
Default mode is admission-only; external effects require explicit execute=True.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


CERTIFIED_KERNEL_RUNNER_HEAD="a5d2d913e41fd9a80212825921d0919fd8320b3b"


class KernelHarnessError(RuntimeError):
    pass


def _canon(v:object)->str:
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False)


def _sha(v:object)->str:
    return "sha256:"+hashlib.sha256(_canon(v).encode("utf-8")).hexdigest()


def verify_kernel_checkout(
    kernel_root:str|Path,
    *,
    expected_head:str=CERTIFIED_KERNEL_RUNNER_HEAD,
)->Path:
    root=Path(kernel_root).resolve()
    if not root.is_dir() or not (root/".git").exists():
        raise KernelHarnessError("kernel_root must be an ordinary git worktree")
    result=subprocess.run(
        ["git","rev-parse","HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode!=0:
        raise KernelHarnessError("unable to resolve kernel HEAD")
    actual=result.stdout.strip()
    if actual!=expected_head:
        raise KernelHarnessError(
            f"kernel HEAD mismatch: expected {expected_head}, actual {actual}"
        )
    runner=root/"src"/"hpl"/"runtime"/"agentic_runner.py"
    if not runner.is_file():
        raise KernelHarnessError("certified kernel runner file is missing")
    return root


def invoke_kernel_binding(
    binding:dict,
    *,
    kernel_root:str|Path,
    python_executable:str="python",
    execute:bool=False,
    trace_dir:str|Path|None=None,
    timeout_seconds:int=60,
    expected_kernel_head:str=CERTIFIED_KERNEL_RUNNER_HEAD,
)->dict:
    root=verify_kernel_checkout(kernel_root,expected_head=expected_kernel_head)
    if not isinstance(binding,dict) or not str(binding.get("binding_sha256","")).startswith("sha256:"):
        raise KernelHarnessError("binding must contain a deterministic binding_sha256")

    with tempfile.TemporaryDirectory(prefix="developer-os-kernel-") as tmp:
        tmp_path=Path(tmp)
        binding_path=tmp_path/"binding.json"
        result_path=tmp_path/"kernel-result.json"
        binding_path.write_text(
            json.dumps(binding,indent=2,sort_keys=True)+"\n",
            encoding="utf-8",
        )

        cmd=[
            python_executable,
            "-m",
            "hpl.runtime.agentic_runner",
            str(binding_path),
            "--out",
            str(result_path),
        ]
        if trace_dir is not None:
            cmd.extend(["--trace-dir",str(Path(trace_dir).resolve())])
        if execute:
            cmd.append("--execute")

        env=None
        # The caller owns environment configuration for OpenHands/HPL. We avoid
        # injecting credentials or service endpoints here.
        result=subprocess.run(
            cmd,
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=int(timeout_seconds),
            env=env,
        )
        if not result_path.is_file():
            raise KernelHarnessError(
                f"kernel runner produced no result (exit={result.returncode})"
            )
        payload=json.loads(result_path.read_text(encoding="utf-8"))
        if not isinstance(payload,dict):
            raise KernelHarnessError("kernel runner result must be an object")

    core={
        "schema_version":"1.0",
        "authority_semantics":"kernel_runner_separate_process",
        "execution_requested":bool(execute),
        "binding_sha256":binding["binding_sha256"],
        "kernel_head":expected_kernel_head,
        "kernel_result":payload,
        "kernel_exit_code":result.returncode,
    }
    core["harness_receipt_sha256"]=_sha(core)
    return core
