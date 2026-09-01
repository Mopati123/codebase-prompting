"""Admission-only end-to-end Developer OS rehearsal v4."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .developer_os import build_developer_plan
from .graph import build_repository_graph
from .hpl_binding import build_repo_read_binding
from .impact import analyze_change_impact
from .kernel_harness import invoke_kernel_binding


def _canon(v:object)->str:
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False)


def _sha(v:object)->str:
    return "sha256:"+hashlib.sha256(_canon(v).encode("utf-8")).hexdigest()


def rehearse_admission(
    *,
    target_root:str|Path,
    changed_paths:list[str],
    change_request:str,
    inspect_path:str,
    conversation_id:str,
    kernel_root:str|Path,
    impact_depth:int=3,
)->dict:
    graph=build_repository_graph(target_root)
    impact=analyze_change_impact(graph,changed_paths,max_depth=impact_depth)
    plan=build_developer_plan(graph,impact,change_request)
    binding=build_repo_read_binding(
        plan,
        conversation_id=conversation_id,
        path=inspect_path,
    )
    harness=invoke_kernel_binding(
        binding,
        kernel_root=kernel_root,
        execute=False,
    )

    admission=harness.get("kernel_result",{}).get("admission",{})
    admitted=isinstance(admission,dict) and admission.get("status")=="admitted"
    runtime=harness.get("kernel_result",{}).get("runtime")
    if runtime is not None:
        raise RuntimeError("admission-only rehearsal unexpectedly produced runtime execution")

    core={
        "schema_version":"1.0",
        "mode":"admission_only",
        "execution_requested":False,
        "graph_sha256":graph["graph_sha256"],
        "impact_sha256":impact["impact_sha256"],
        "developer_plan_sha256":plan["plan_sha256"],
        "binding_sha256":binding["binding_sha256"],
        "kernel_harness_receipt_sha256":harness["harness_receipt_sha256"],
        "kernel_head":harness["kernel_head"],
        "admitted":admitted,
        "execution_token_present":bool(
            isinstance(admission,dict)
            and isinstance(admission.get("plan"),dict)
            and isinstance(admission["plan"].get("execution_token"),dict)
        ),
        "runtime_executed":False,
    }
    core["rehearsal_sha256"]=_sha(core)
    return core
