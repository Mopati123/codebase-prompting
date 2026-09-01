from __future__ import annotations
import argparse,json
from pathlib import Path

from .architecture import load_architecture_contract, map_files_to_components
from .graph import build_repository_graph
from .impact import analyze_change_impact
from .scope import build_openhands_scope
from .developer_os import build_developer_plan
from .hpl_binding import build_repo_read_binding, build_test_execute_binding


def _write(path:str,data:dict)->None:
    Path(path).write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(path)


def main()->None:
    p=argparse.ArgumentParser(prog="repo-intel")
    sub=p.add_subparsers(dest="cmd",required=True)

    g=sub.add_parser("graph")
    g.add_argument("root")
    g.add_argument("--architecture")
    g.add_argument("--out",default="repository-graph.json")

    i=sub.add_parser("impact")
    i.add_argument("graph")
    i.add_argument("changed",nargs="+")
    i.add_argument("--depth",type=int,default=3)
    i.add_argument("--out",default="change-impact.json")

    s=sub.add_parser("openhands-scope")
    s.add_argument("graph")
    s.add_argument("impact")
    s.add_argument("--operation",required=True,choices=["repo.read","test.execute","repo.patch"])
    s.add_argument("--out",default="openhands-scope.json")

    d=sub.add_parser("developer-plan")
    d.add_argument("graph")
    d.add_argument("impact")
    d.add_argument("--change-request",required=True)
    d.add_argument("--out",default="developer-plan.json")

    b=sub.add_parser("hpl-read-binding")
    b.add_argument("developer_plan")
    b.add_argument("--conversation-id",required=True)
    b.add_argument("--path",required=True)
    b.add_argument("--out",default="hpl-read-binding.json")

    t=sub.add_parser("hpl-test-binding")
    t.add_argument("developer_plan")
    t.add_argument("--workspace",required=True)
    t.add_argument("--test-path",required=True)
    t.add_argument("--out",default="hpl-test-binding.json")

    a=p.parse_args()

    if a.cmd=="graph":
        data=build_repository_graph(a.root)
        if a.architecture:
            contract=load_architecture_contract(a.architecture)
            data["architecture_contract"]=contract
            data["architecture_membership"]=map_files_to_components(data["files"],contract)
    elif a.cmd=="impact":
        graph=json.loads(Path(a.graph).read_text(encoding="utf-8"))
        data=analyze_change_impact(graph,a.changed,a.depth)
    elif a.cmd=="openhands-scope":
        graph=json.loads(Path(a.graph).read_text(encoding="utf-8"))
        impact=json.loads(Path(a.impact).read_text(encoding="utf-8"))
        data=build_openhands_scope(graph,impact,a.operation)
    elif a.cmd=="developer-plan":
        graph=json.loads(Path(a.graph).read_text(encoding="utf-8"))
        impact=json.loads(Path(a.impact).read_text(encoding="utf-8"))
        data=build_developer_plan(graph,impact,a.change_request)
    elif a.cmd=="hpl-read-binding":
        plan=json.loads(Path(a.developer_plan).read_text(encoding="utf-8"))
        data=build_repo_read_binding(plan,conversation_id=a.conversation_id,path=a.path)
    else:
        plan=json.loads(Path(a.developer_plan).read_text(encoding="utf-8"))
        data=build_test_execute_binding(plan,workspace=a.workspace,test_path=a.test_path)

    _write(a.out,data)


if __name__=="__main__":
    main()
