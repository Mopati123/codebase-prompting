"""Architecture-component contract support for repository intelligence v3."""
from __future__ import annotations

import fnmatch
import hashlib
import json
from pathlib import Path


ALLOWED_EDGE_TYPES={"depends_on","configures","deploys"}


class ArchitectureContractError(ValueError):
    pass


def _canon(v:object)->str:
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False)


def _sha(v:object)->str:
    return "sha256:"+hashlib.sha256(_canon(v).encode("utf-8")).hexdigest()


def load_architecture_contract(path:str|Path)->dict:
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_architecture_contract(data)


def validate_architecture_contract(data:dict)->dict:
    if not isinstance(data,dict):
        raise ArchitectureContractError("architecture contract must be an object")
    if data.get("schema_version")!="1.0":
        raise ArchitectureContractError("schema_version must be 1.0")

    components=data.get("components")
    if not isinstance(components,list) or not components:
        raise ArchitectureContractError("components must be a non-empty list")

    names=set()
    normalized=[]
    for item in components:
        if not isinstance(item,dict):
            raise ArchitectureContractError("component entry must be an object")
        name=str(item.get("name","")).strip()
        paths=item.get("paths")
        if not name or name in names:
            raise ArchitectureContractError("component names must be unique and non-empty")
        if not isinstance(paths,list) or not paths or any(not isinstance(p,str) or not p.strip() for p in paths):
            raise ArchitectureContractError(f"component {name} must define non-empty path globs")
        names.add(name)
        normalized.append({"name":name,"paths":sorted(set(p.strip() for p in paths))})

    edges=[]
    for item in data.get("dependencies",[]):
        if not isinstance(item,dict):
            raise ArchitectureContractError("dependency entry must be an object")
        src=str(item.get("from","")).strip()
        dst=str(item.get("to","")).strip()
        typ=str(item.get("type","depends_on")).strip()
        if src not in names or dst not in names:
            raise ArchitectureContractError("dependency endpoints must reference declared components")
        if typ not in ALLOWED_EDGE_TYPES:
            raise ArchitectureContractError(f"unsupported dependency type: {typ}")
        edges.append({"from":src,"to":dst,"type":typ})

    core={
        "schema_version":"1.0",
        "components":sorted(normalized,key=lambda x:x["name"]),
        "dependencies":sorted(edges,key=lambda x:(x["from"],x["to"],x["type"])),
    }
    core["contract_sha256"]=_sha(core)
    return core


def map_files_to_components(files:list[dict],contract:dict)->list[dict]:
    out=[]
    for file_entry in files:
        path=str(file_entry.get("path",""))
        matches=[]
        for component in contract.get("components",[]):
            if any(fnmatch.fnmatch(path,pattern) for pattern in component.get("paths",[])):
                matches.append(component["name"])
        out.append({"file":path,"components":sorted(matches)})
    return sorted(out,key=lambda x:x["file"])
