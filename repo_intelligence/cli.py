from __future__ import annotations
import argparse,json
from pathlib import Path
from .graph import build_repository_graph
from .impact import analyze_change_impact


def main()->None:
    p=argparse.ArgumentParser(prog="repo-intel")
    sub=p.add_subparsers(dest="cmd",required=True)
    g=sub.add_parser("graph"); g.add_argument("root"); g.add_argument("--out",default="repository-graph.json")
    i=sub.add_parser("impact"); i.add_argument("graph"); i.add_argument("changed",nargs="+"); i.add_argument("--depth",type=int,default=3); i.add_argument("--out",default="change-impact.json")
    a=p.parse_args()
    if a.cmd=="graph": data=build_repository_graph(a.root)
    else: data=analyze_change_impact(json.loads(Path(a.graph).read_text(encoding="utf-8")),a.changed,a.depth)
    Path(a.out).write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(a.out)

if __name__=="__main__": main()
