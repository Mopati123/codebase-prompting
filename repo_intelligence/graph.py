"""Deterministic repository graph construction.

v1 intentionally avoids LLM dependence. It builds a reproducible graph from
repository files, Python imports/symbols, and selected JS/TS imports.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
from dataclasses import dataclass, asdict
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
    candidates=[root/Path(*target.split(".")).with_suffix(".py"),root/Path(*target.split("."))/ "__init__.py"]
    for c in candidates:
        if c.exists(): return c.relative_to(root).as_posix()
    return None


def _parse_python(root:Path,path:Path,text:str)->tuple[list[dict],list[str]]:
    symbols=[]; deps=[]
    try: tree=ast.parse(text)
    except SyntaxError: return symbols,deps
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            symbols.append({"name":node.name,"kind":"class" if isinstance(node,ast.ClassDef) else "function","line":getattr(node,"lineno",None)})
        elif isinstance(node,ast.Import):
            for alias in node.names:
                d=_resolve_py_import(root,path,alias.name,0)
                if d: deps.append(d)
        elif isinstance(node,ast.ImportFrom):
            d=_resolve_py_import(root,path,node.module or "",node.level)
            if d: deps.append(d)
    return sorted(symbols,key=lambda x:(x["name"],x["kind"],x["line"] or 0)),sorted(set(deps))


def _parse_js_like(root:Path,path:Path,text:str)->list[str]:
    out=[]
    for m in JS_IMPORT.finditer(text):
        spec=next((g for g in m.groups() if g),None)
        if not spec or not spec.startswith("."): continue
        base=(path.parent/spec).resolve()
        for c in [base,base.with_suffix(".js"),base.with_suffix(".jsx"),base.with_suffix(".ts"),base.with_suffix(".tsx"),base/"index.js",base/"index.ts"]:
            try:
                if c.exists() and c.is_file() and root.resolve() in c.resolve().parents:
                    out.append(c.relative_to(root).as_posix()); break
            except OSError: pass
    return sorted(set(out))


def build_repository_graph(root:str|Path)->dict:
    root=Path(root).resolve()
    if not root.is_dir(): raise ValueError("root must be an existing directory")
    files=[]; edges=[]; symbols=[]
    for path in _iter_files(root):
        rel=path.relative_to(root).as_posix()
        raw=path.read_bytes()
        try: text=raw.decode("utf-8")
        except UnicodeDecodeError: continue
        entry={"path":rel,"bytes":len(raw),"sha256":_sha(raw),"extension":path.suffix.lower()}
        deps=[]
        if path.suffix.lower()==".py":
            syms,deps=_parse_python(root,path,text)
            for s in syms: symbols.append({"file":rel,**s})
        elif path.suffix.lower() in {".js",".jsx",".ts",".tsx"}:
            deps=_parse_js_like(root,path,text)
        files.append(entry)
        for dep in deps: edges.append({"from":rel,"to":dep,"type":"imports"})
    files=sorted(files,key=lambda x:x["path"])
    edges=sorted(edges,key=lambda x:(x["from"],x["to"],x["type"]))
    symbols=sorted(symbols,key=lambda x:(x["file"],x["line"] or 0,x["name"]))
    core={"schema_version":"1.0","root_name":root.name,"files":files,"symbols":symbols,"edges":edges}
    core["graph_sha256"]=_sha(_canon(core).encode())
    return core
