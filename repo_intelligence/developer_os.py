"""Deterministic governed Developer OS planning primitives.

This module composes repository intelligence into a proposal-only developer
execution plan. It never performs repository IO through OpenHands and never
mints execution authority; HPL must separately admit each consequential effect.
"""
from __future__ import annotations

import hashlib
import json

from .scope import build_openhands_scope


STAGES=("repo.read","test.execute","repo.patch","test.execute")


def _canon(v:object)->str:
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False)


def _sha(v:object)->str:
    return "sha256:"+hashlib.sha256(_canon(v).encode("utf-8")).hexdigest()


def build_developer_plan(graph:dict,impact:dict,change_request:str)->dict:
    if not isinstance(change_request,str) or not change_request.strip():
        raise ValueError("change_request must be non-empty text")
    if impact.get("unknown_paths"):
        raise ValueError("cannot build developer plan with unknown changed paths")

    read_scope=build_openhands_scope(graph,impact,"repo.read")
    test_scope=build_openhands_scope(graph,impact,"test.execute")
    patch_scope=build_openhands_scope(graph,impact,"repo.patch")

    stages=[
        {
            "ordinal":0,
            "name":"inspect",
            "capability":"repo.read",
            "scope_sha256":read_scope["scope_sha256"],
            "requires_execution_authority":False,
            "must_reconcile":True,
        },
        {
            "ordinal":1,
            "name":"baseline_tests",
            "capability":"test.execute",
            "scope_sha256":test_scope["scope_sha256"],
            "requires_execution_authority":False,
            "must_reconcile":True,
        },
        {
            "ordinal":2,
            "name":"patch",
            "capability":"repo.patch",
            "scope_sha256":patch_scope["scope_sha256"],
            "requires_execution_authority":True,
            "must_reconcile":True,
        },
        {
            "ordinal":3,
            "name":"retest",
            "capability":"test.execute",
            "scope_sha256":test_scope["scope_sha256"],
            "requires_execution_authority":False,
            "must_reconcile":True,
        },
        {
            "ordinal":4,
            "name":"recompute_repository_intelligence",
            "capability":"repository.recompute",
            "scope_sha256":None,
            "requires_execution_authority":False,
            "must_reconcile":True,
        },
        {
            "ordinal":5,
            "name":"evidence_finalize",
            "capability":"evidence.finalize",
            "scope_sha256":None,
            "requires_execution_authority":False,
            "must_reconcile":True,
        },
    ]

    core={
        "schema_version":"1.0",
        "authority_semantics":"proposal_plan_only",
        "execution_authorized":False,
        "change_request_sha256":"sha256:"+hashlib.sha256(change_request.strip().encode("utf-8")).hexdigest(),
        "graph_sha256":graph.get("graph_sha256"),
        "impact_sha256":impact.get("impact_sha256"),
        "scopes":{
            "repo.read":read_scope,
            "test.execute":test_scope,
            "repo.patch":patch_scope,
        },
        "stages":stages,
        "invariants":{
            "patch_requires_hpl_authority":True,
            "no_stage_skips_reconciliation":True,
            "retest_required_after_patch":True,
            "repository_intelligence_recompute_required":True,
            "evidence_finalize_required":True,
        },
    }
    core["plan_sha256"]=_sha(core)
    return core


def reconcile_developer_run(plan:dict,stage_receipts:list[dict])->dict:
    expected=[s["name"] for s in plan.get("stages",[])]
    observed=[str(r.get("stage","")) for r in stage_receipts if isinstance(r,dict)]
    missing=[stage for stage in expected if stage not in observed]
    failed=[
        str(r.get("stage",""))
        for r in stage_receipts
        if isinstance(r,dict) and r.get("ok") is not True
    ]
    patch_receipts=[
        r for r in stage_receipts
        if isinstance(r,dict) and r.get("stage")=="patch"
    ]
    patch_authorized=all(r.get("execution_token_present") is True for r in patch_receipts) if patch_receipts else False

    ok=(not missing and not failed and patch_authorized)
    core={
        "schema_version":"1.0",
        "plan_sha256":plan.get("plan_sha256"),
        "observed_stages":observed,
        "missing_stages":missing,
        "failed_stages":failed,
        "patch_execution_token_verified":patch_authorized,
        "reconciled":ok,
    }
    core["reconciliation_sha256"]=_sha(core)
    return core
