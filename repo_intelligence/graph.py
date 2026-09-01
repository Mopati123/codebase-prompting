"""Deterministic repository graph construction v2.

Builds reproducible file, symbol, import, test-to-code, and conservative Python
symbol-call relationships without requiring an LLM.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Iterable

IGNORE_DIRS={".git",".venv","venv","node_modules","dist","build","__pycache__",".pytest_cache",".mypy_cache"}
TEXT_EXTS={".py",".js",".jsx",".ts",".tsx",".json",".md",".toml",".yaml",".yml"}
JS_IMPORT=re.compile(r"""(?:from\s+['\"]([^'\"]+)['\"]|import\s+['\"]([^'\"]+)['\"]|require\(\s*['\"]([^'\"]+)['\"]\s*\))""")


def _sha(data:bytes)->str:
    return "sha256:"+hashlib.sha256(data).hexdigest()


def _canon(v:object)->str:
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False)


def _iter_files(root:Path)->Iterable[Path]:
    for base,dirs,files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in IGNORE_DIRS)
        for name in sorted(files):
            p=Path(base)/name
            if p.suffix.lower() in TEXT_EXTS and p.is_file() and not p.is_symlink():
                yield p


def _module_for(root:Path,path:Path)->str:
    rel=path.relative_to(root).with_suffix("")
    parts=list(rel.parts)
    if parts and parts[-1]=="__init__": parts=parts[:-1]
    return ".".join(parts)


def _resolve_py_import(root:Path,current:Path,module:str,level:int)->str|None:
    current_mod=_module_for(root,current)
    base=current_mod.split(".")[:-1]
    if level:
        keep=max(0,len(base)-level+1)
        base=base[:keep]
    target=".".join([*base,*([module] if module else [])]).strip(".") if level else module
    if not target: return None
    candidates=[
        root/Path(*target.split(".")).with_suffix(".py"),
        root/Path(*target.split("."))/"__init__.py",
    ]
    for c in candidates:
        if c.exists(): return c.relative_to(root).as_posix()
    return None


def _symbol_id(file_path:str,name:str)->str:
    return f"{file_path}::{name}"


def _called_names(node:ast.AST)->set[str]:
    names=set()
    for child in ast.walk(node):
        if isinstance(child,ast.Call):
            fn=child.func
            if isinstance(fn,ast.Name):
                names.add(fn.id)
            elif isinstance(fn,ast.Attribute):
                names.add(fn.attr)
    return names


def _parse_python(root:Path,path:Path,text:str)->tuple[list[dict],list[str],list[dict]]:
    symbols=[]; deps=[]; call_candidates=[]
    try: tree=ast.parse(text)
    except SyntaxError: return symbols,deps,call_candidates

    local_names={
        node.name
        for node in tree.body
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))
    }
    imported_symbols:dict[str,tuple[str,str]]={}

    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            symbols.append({
                "name":node.name,
                "kind":"class" if isinstance(node,ast.ClassDef) else "function",
                "line":getattr(node,"lineno",None),
            })
        elif isinstance(node,ast.Import):
            for alias in node.names:
                d=_resolve_py_import(root,path,alias.name,0)
                if d: deps.append(d)
        elif isinstance(node,ast.ImportFrom):
            d=_resolve_py_import(root,path,node.module or "",node.level)
            if d:
                deps.append(d)
                for alias in node.names:
                    if alias.name!="*":
                        imported_symbols[alias.asname or alias.name]=(d,alias.name)

    rel=path.relative_to(root).as_posix()
    for node in tree.body:
        if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            continue
        caller=_symbol_id(rel,node.name)
        for name in sorted(_called_names(node)):
            if name in local_names:
                call_candidates.append({"from":caller,"to":_symbol_id(rel,name),"type":"calls"})
            elif name in imported_symbols:
                dep_file,dep_name=imported_symbols[name]
                call_candidates.append({"from":caller,"to":_symbol_id(dep_file,dep_name),"type":"calls"})

    return (
        sorted(symbols,key=lambda x:(x["name"],x["kind"],x["line"] or 0)),
        sorted(set(deps)),
        sorted(call_candidates,key=lambda x:(x["from"],x["to"],x["type"])),
    )


def _parse_js_like(root:Path,path:Path,text:str)->list[str]:
    out=[]
    for m in JS_IMPORT.finditer(text):
        spec=next((g for g in m.groups() if g),None)
        if not spec or not spec.startswith("."): continue
        base=(path.parent/spec).resolve()
        for c in [
            base,base.with_suffix(".js"),base.with_suffix(".jsx"),
            base.with_suffix(".ts"),base.with_suffix(".tsx"),
            base/"index.js",base/"index.ts",
        ]:
            try:
                if c.exists() and c.is_file() and root.resolve() in c.resolve().parents:
                    out.append(c.relative_to(root).as_posix()); break
            except OSError:
                pass
    return sorted(set(out))


def _is_test_file(path:str)->bool:
    p=Path(path)
    return (
        any(part in {"test","tests","spec","specs"} for part in p.parts[:-1])
        or p.name.startswith("test_")
        or p.name.endswith("_test.py")
        or p.name.endswith(".spec.js")
        or p.name.endswith(".spec.ts")
        or p.name.endswith(".test.js")
        or p.name.endswith(".test.ts")
    )


def build_repository_graph(root:str|Path)->dict:
    root=Path(root).resolve()
    if not root.is_dir(): raise ValueError("root must be an existing directory")

    files=[]; edges=[]; symbols=[]; symbol_edges=[]
    deps_by_file:dict[str,list[str]]={}

    for path in _iter_files(root):
        rel=path.relative_to(root).as_posix()
        raw=path.read_bytes()
        try: text=raw.decode("utf-8")
        except UnicodeDecodeError: continue

        files.append({
            "path":rel,
            "bytes":len(raw),
            "sha256":_sha(raw),
            "extension":path.suffix.lower(),
            "is_test":_is_test_file(rel),
        })

        deps=[]
        if path.suffix.lower()==".py":
            syms,deps,calls=_parse_python(root,path,text)
            for s in syms:
                symbols.append({"id":_symbol_id(rel,s["name"]),"file":rel,**s})
            symbol_edges.extend(calls)
        elif path.suffix.lower() in {".js",".jsx",".ts",".tsx"}:
            deps=_parse_js_like(root,path,text)

        deps_by_file[rel]=deps
        for dep in deps:
            edges.append({"from":rel,"to":dep,"type":"imports"})

    known_symbols={s["id"] for s in symbols}
    symbol_edges=[
        e for e in symbol_edges
        if e["from"] in known_symbols and e["to"] in known_symbols
    ]

    test_files={f["path"] for f in files if f["is_test"]}
    for test_file in sorted(test_files):
        for dep in deps_by_file.get(test_file,[]):
            if dep not in test_files:
                edges.append({"from":test_file,"to":dep,"type":"tests"})

    components=[]
    for f in files:
        path=f["path"]
        parts=Path(path).parts
        component=parts[0] if len(parts)>1 else "."
        components.append({"file":path,"component":component})

    files=sorted(files,key=lambda x:x["path"])
    edges=sorted({(e["from"],e["to"],e["type"]) for e in edges})
    edges=[{"from":a,"to":b,"type":t} for a,b,t in edges]
    symbols=sorted(symbols,key=lambda x:(x["file"],x["line"] or 0,x["name"]))
    symbol_edges=sorted(symbol_edges,key=lambda x:(x["from"],x["to"],x["type"]))
    components=sorted(components,key=lambda x:(x["component"],x["file"]))

    core={
        "schema_version":"2.0",
        "root_name":root.name,
        "files":files,
        "components":components,
        "symbols":symbols,
        "edges":edges,
        "symbol_edges":symbol_edges,
    }
    core["graph_sha256"]=_sha(_canon(core).encode())
    return core
