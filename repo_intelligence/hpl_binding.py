"""HPL/OpenHands binding payload generation for Governed Developer OS v2.

This module translates deterministic Developer OS scopes into HPL-compatible
proposal/request/policy payloads for the already-certified OpenHands capability
surface. It does not call HPL, OpenHands, Git, or the network.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import PurePosixPath


EFFECTS={
    "repo.read":"OPENHANDS_REPO_READ",
    "test.execute":"OPENHANDS_TEST_EXECUTE",
    "repo.patch":"OPENHANDS_REPO_PATCH",
}
MODULE_RE=re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")


def _canon(v:object)->str:
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False)


def _sha_bytes(value:bytes)->str:
    return "sha256:"+hashlib.sha256(value).hexdigest()


def _sha_text(value:str)->str:
    return _sha_bytes(value.encode("utf-8"))


def _validate_relative_path(value:str)->str:
    p=PurePosixPath(value)
    if not value or p.is_absolute() or ".." in p.parts or "." in p.parts:
        raise ValueError("path must be a bounded relative path")
    return p.as_posix()


def python_test_path_to_module(path:str)->str:
    normalized=_validate_relative_path(path)
    if not normalized.endswith(".py"):
        raise ValueError("test.execute v1 requires a Python test module")
    module=normalized[:-3].replace("/",".")
    if not MODULE_RE.fullmatch(module):
        raise ValueError("test module path is not a valid dotted module")
    return module


def _envelope(capability:str,scope:dict,effect_args:dict,*,reason:str,allow_consequential:bool)->dict:
    effect=EFFECTS[capability]
    proposal={
        "proposer":"openhands",
        "intent":reason,
        "requested_capabilities":[capability],
        "inputs":{},
        "expected_effects":[effect],
    }
    request={
        "actor":"openhands",
        "capabilities":[capability],
        "scope":scope,
        "reason":reason,
    }
    policy={
        "allowed_capabilities":[capability],
        "capability_bounds":scope,
        "allow_consequential":allow_consequential,
        "allowed_backends":["CLASSICAL"],
        "budget_steps":1,
        "determinism_mode":"deterministic",
        "effect_type":effect,
        "effect_args":effect_args,
    }
    core={
        "schema_version":"1.0",
        "authority_semantics":"hpl_admission_required",
        "execution_authorized":False,
        "proposal":proposal,
        "request":request,
        "policy":policy,
    }
    core["binding_sha256"]=_sha_text(_canon(core))
    return core


def build_repo_read_binding(
    developer_plan:dict,
    *,
    conversation_id:str,
    path:str,
    timeout_seconds:int=10,
    max_response_bytes:int=1_000_000,
)->dict:
    scope_plan=developer_plan["scopes"]["repo.read"]
    path=_validate_relative_path(path)
    if path not in scope_plan.get("readable_paths",[]):
        raise ValueError("path is outside developer-plan repo.read scope")
    if not conversation_id or len(conversation_id)>64 or any(ch not in "0123456789abcdefABCDEF-" for ch in conversation_id):
        raise ValueError("conversation_id is invalid")
    scope={
        "conversation_id":conversation_id,
        "path":path,
        "timeout_seconds":int(timeout_seconds),
        "max_response_bytes":int(max_response_bytes),
    }
    args={
        "conversation_id":conversation_id,
        "path":path,
        "content_artifact":"openhands_repo_read.bin",
        "receipt_artifact":"openhands_repo_read_receipt.json",
    }
    return _envelope(
        "repo.read",scope,args,
        reason=f"Developer OS bounded read of {path}",
        allow_consequential=False,
    )


def build_test_execute_binding(
    developer_plan:dict,
    *,
    workspace:str,
    test_path:str,
    timeout_seconds:int=120,
    max_response_bytes:int=1_000_000,
)->dict:
    scope_plan=developer_plan["scopes"]["test.execute"]
    test_path=_validate_relative_path(test_path)
    if test_path not in scope_plan.get("test_paths",[]):
        raise ValueError("test path is outside developer-plan test.execute scope")
    module=python_test_path_to_module(test_path)
    workspace=_validate_relative_path(workspace)
    scope={
        "runner":"python_unittest",
        "target":module,
        "workspace":workspace,
        "timeout_seconds":int(timeout_seconds),
        "max_response_bytes":int(max_response_bytes),
    }
    args={
        "runner":"python_unittest",
        "target":module,
        "workspace":workspace,
        "receipt_artifact":"openhands_test_receipt.json",
    }
    return _envelope(
        "test.execute",scope,args,
        reason=f"Developer OS bounded test execution for {module}",
        allow_consequential=False,
    )


def build_repo_patch_binding(
    developer_plan:dict,
    *,
    workspace:str,
    path:str,
    branch:str,
    expected_preimage_sha256:str,
    replacement_text:str,
    timeout_seconds:int=20,
    max_patch_bytes:int=1_000_000,
)->dict:
    scope_plan=developer_plan["scopes"]["repo.patch"]
    path=_validate_relative_path(path)
    if path not in scope_plan.get("writable_paths",[]):
        raise ValueError("path is outside developer-plan repo.patch writable scope")
    workspace=_validate_relative_path(workspace)
    if not branch or branch in {"main","master"}:
        raise ValueError("repo.patch requires a non-protected branch")
    if not isinstance(replacement_text,str):
        raise ValueError("replacement_text must be text")
    if not expected_preimage_sha256.startswith("sha256:") or len(expected_preimage_sha256)!=71:
        raise ValueError("expected_preimage_sha256 must be a sha256: digest")
    replacement_bytes=replacement_text.encode("utf-8")
    if len(replacement_bytes)>int(max_patch_bytes):
        raise ValueError("replacement exceeds max_patch_bytes")
    replacement_sha256=_sha_bytes(replacement_bytes)
    scope={
        "workspace":workspace,
        "path":path,
        "branch":branch,
        "expected_preimage_sha256":expected_preimage_sha256,
        "replacement_sha256":replacement_sha256,
        "timeout_seconds":int(timeout_seconds),
        "max_patch_bytes":int(max_patch_bytes),
    }
    args={
        "workspace":workspace,
        "path":path,
        "branch":branch,
        "replacement_text":replacement_text,
        "receipt_artifact":"openhands_repo_patch_receipt.json",
    }
    return _envelope(
        "repo.patch",scope,args,
        reason=f"Developer OS bounded complete-file replacement for {path}",
        allow_consequential=True,
    )
