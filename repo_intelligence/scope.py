"""Machine-readable OpenHands proposal-scope generation.

The result is not execution authority. It is a deterministic candidate scope
that a separate HPL admission decision may accept, narrow, or refuse.
"""
from __future__ import annotations

import hashlib
import json


ALLOWED_OPERATIONS={"repo.read","test.execute","repo.patch"}


def _canon(v:object)->str:
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False)


def _sha(v:object)->str:
    return "sha256:"+hashlib.sha256(_canon(v).encode("utf-8")).hexdigest()


def build_openhands_scope(graph:dict,impact:dict,operation:str)->dict:
    if operation not in ALLOWED_OPERATIONS:
        raise ValueError(f"unsupported OpenHands operation: {operation}")

    impacted=[x for x in impact.get("impacted_files",[]) if isinstance(x,dict)]
    paths=sorted({str(x.get("path","")) for x in impacted if str(x.get("path","")).strip()})
    tests=sorted({
        str(x.get("path",""))
        for x in impact.get("impacted_tests",[])
        if isinstance(x,dict) and str(x.get("path","")).strip()
    })
    changed=sorted(set(str(x) for x in impact.get("changed_paths",[]) if str(x).strip()))

    if operation=="repo.patch":
        writable=changed
        readable=paths
        executable_tests=tests
    elif operation=="test.execute":
        writable=[]
        readable=paths
        executable_tests=tests
    else:
        writable=[]
        readable=paths
        executable_tests=[]

    core={
        "schema_version":"1.0",
        "authority_semantics":"proposal_scope_only",
        "operation":operation,
        "graph_sha256":graph.get("graph_sha256"),
        "impact_sha256":impact.get("impact_sha256"),
        "readable_paths":readable,
        "writable_paths":writable,
        "test_paths":executable_tests,
        "impacted_components":sorted(set(impact.get("impacted_components",[]))),
        "unknown_paths":sorted(set(impact.get("unknown_paths",[]))),
        "execution_authorized":False,
    }
    core["scope_sha256"]=_sha(core)
    return core
