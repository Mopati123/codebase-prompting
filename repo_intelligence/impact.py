"""Change-impact analysis over a deterministic repository graph."""
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
    for e in graph.get("edges",[]):
        if isinstance(e,dict) and e.get("type")=="imports" and e.get("from") in known and e.get("to") in known:
            reverse[e["to"]].add(e["from"])
    distance={p:0 for p in changed if p in known}
    q=deque(sorted(distance))
    while q:
        cur=q.popleft(); d=distance[cur]
        if d>=max_depth: continue
        for dep in sorted(reverse.get(cur,())):
            if dep not in distance:
                distance[dep]=d+1; q.append(dep)
    impacted=[{"path":p,"distance":distance[p]} for p in sorted(distance,key=lambda x:(distance[x],x))]
    symbols=[s for s in graph.get("symbols",[]) if isinstance(s,dict) and s.get("file") in distance]
    core={"schema_version":"1.0","graph_sha256":graph.get("graph_sha256"),"changed_paths":changed,"unknown_paths":unknown,"max_depth":max_depth,"impacted_files":impacted,"impacted_symbols":symbols}
    core["impact_sha256"]=_sha(_canon(core))
    return core
