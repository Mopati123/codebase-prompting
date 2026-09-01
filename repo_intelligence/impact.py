"""Change-impact analysis over a deterministic repository graph v2."""
from __future__ import annotations

import hashlib,json
from collections import deque


def _canon(v:object)->str:
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False)


def _sha(s:str)->str:
    return "sha256:"+hashlib.sha256(s.encode()).hexdigest()


def analyze_change_impact(graph:dict,changed_paths:list[str],max_depth:int=3)->dict:
    if max_depth<0: raise ValueError("max_depth must be >= 0")
    known={f["path"] for f in graph.get("files",[]) if isinstance(f,dict) and "path" in f}
    changed=sorted(set(changed_paths))
    unknown=sorted(p for p in changed if p not in known)

    reverse={p:set() for p in known}
    edge_types:dict[tuple[str,str],set[str]]={}
    for e in graph.get("edges",[]):
        if not isinstance(e,dict): continue
        src=e.get("from"); dst=e.get("to"); typ=e.get("type")
        if src in known and dst in known and typ in {"imports","tests"}:
            reverse[dst].add(src)
            edge_types.setdefault((dst,src),set()).add(str(typ))

    distance={p:0 for p in changed if p in known}
    reasons={p:{"changed"} for p in distance}
    q=deque(sorted(distance))
    while q:
        cur=q.popleft(); d=distance[cur]
        if d>=max_depth: continue
        for dep in sorted(reverse.get(cur,())):
            candidate=d+1
            rel_types=edge_types.get((cur,dep),{"dependency"})
            if dep not in distance or candidate<distance[dep]:
                distance[dep]=candidate
                reasons[dep]=set(rel_types)
                q.append(dep)
            elif candidate==distance[dep]:
                reasons.setdefault(dep,set()).update(rel_types)

    impacted=[
        {"path":p,"distance":distance[p],"reasons":sorted(reasons.get(p,()))}
        for p in sorted(distance,key=lambda x:(distance[x],x))
    ]
    symbols=[
        s for s in graph.get("symbols",[])
        if isinstance(s,dict) and s.get("file") in distance
    ]
    tests=[
        item for item in impacted
        if any(f.get("path")==item["path"] and f.get("is_test") is True for f in graph.get("files",[]))
    ]
    components=sorted({
        c.get("component")
        for c in graph.get("components",[])
        if isinstance(c,dict) and c.get("file") in distance and isinstance(c.get("component"),str)
    })

    core={
        "schema_version":"2.0",
        "graph_sha256":graph.get("graph_sha256"),
        "changed_paths":changed,
        "unknown_paths":unknown,
        "max_depth":max_depth,
        "impacted_files":impacted,
        "impacted_symbols":symbols,
        "impacted_tests":tests,
        "impacted_components":components,
    }
    core["impact_sha256"]=_sha(_canon(core))
    return core
