from pathlib import Path
from unittest import mock
import json
import os

from repo_intelligence.kernel_harness import (
    CERTIFIED_KERNEL_RUNNER_HEAD,
    KernelHarnessError,
    invoke_kernel_binding,
    verify_kernel_checkout,
)


def _binding():
    return {
        "schema_version":"1.0",
        "authority_semantics":"hpl_admission_required",
        "execution_authorized":False,
        "proposal":{},
        "request":{},
        "policy":{},
        "binding_sha256":"sha256:"+"a"*64,
    }


def _tree(tmp_path:Path):
    (tmp_path/".git").mkdir()
    (tmp_path/"src"/"hpl"/"runtime").mkdir(parents=True)
    (tmp_path/"src"/"hpl"/"runtime"/"agentic_runner.py").write_text("x=1\n",encoding="utf-8")


def test_verify_kernel_checkout_requires_exact_head(tmp_path:Path):
    _tree(tmp_path)
    ok=mock.Mock(returncode=0,stdout=CERTIFIED_KERNEL_RUNNER_HEAD+"\n")
    with mock.patch("repo_intelligence.kernel_harness.subprocess.run",return_value=ok):
        assert verify_kernel_checkout(tmp_path)==tmp_path.resolve()


def test_verify_kernel_checkout_refuses_wrong_head(tmp_path:Path):
    (tmp_path/".git").mkdir()
    with mock.patch(
        "repo_intelligence.kernel_harness.subprocess.run",
        return_value=mock.Mock(returncode=0,stdout="0"*40+"\n"),
    ):
        try:
            verify_kernel_checkout(tmp_path)
        except KernelHarnessError:
            pass
        else:
            raise AssertionError("expected KernelHarnessError")


def test_harness_defaults_to_admission_only_and_sets_kernel_pythonpath(tmp_path:Path):
    _tree(tmp_path)
    calls=[]
    def fake_run(cmd,**kwargs):
        calls.append((cmd,kwargs))
        if cmd[:3]==["git","rev-parse","HEAD"]:
            return mock.Mock(returncode=0,stdout=CERTIFIED_KERNEL_RUNNER_HEAD+"\n",stderr="")
        out=Path(cmd[cmd.index("--out")+1])
        out.write_text(json.dumps({"admission":{"status":"admitted"},"runtime":None}),encoding="utf-8")
        return mock.Mock(returncode=0,stdout="",stderr="")

    with mock.patch("repo_intelligence.kernel_harness.subprocess.run",side_effect=fake_run):
        receipt=invoke_kernel_binding(_binding(),kernel_root=tmp_path)

    runner_cmd,kwargs=calls[1]
    assert "--execute" not in runner_cmd
    assert receipt["execution_requested"] is False
    assert receipt["kernel_result"]["runtime"] is None
    assert kwargs["env"]["PYTHONPATH"].split(os.pathsep)[0]==str((tmp_path/"src").resolve())


def test_harness_execute_is_explicit(tmp_path:Path):
    _tree(tmp_path)
    calls=[]
    def fake_run(cmd,**kwargs):
        calls.append(cmd)
        if cmd[:3]==["git","rev-parse","HEAD"]:
            return mock.Mock(returncode=0,stdout=CERTIFIED_KERNEL_RUNNER_HEAD+"\n",stderr="")
        out=Path(cmd[cmd.index("--out")+1])
        out.write_text(json.dumps({"admission":{"status":"admitted"},"runtime":{"status":"completed"}}),encoding="utf-8")
        return mock.Mock(returncode=0,stdout="",stderr="")

    with mock.patch("repo_intelligence.kernel_harness.subprocess.run",side_effect=fake_run):
        receipt=invoke_kernel_binding(_binding(),kernel_root=tmp_path,execute=True)

    assert "--execute" in calls[1]
    assert receipt["execution_requested"] is True
