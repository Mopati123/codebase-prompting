from pathlib import Path
import json
from repo_intelligence.graph import build_repository_graph
from repo_intelligence.impact import analyze_change_impact


def test_graph_and_impact_are_deterministic(tmp_path:Path):
    (tmp_path/"a.py").write_text("from b import f\n\ndef g():\n    return f()\n",encoding="utf-8")
    (tmp_path/"b.py").write_text("def f():\n    return 1\n",encoding="utf-8")
    g1=build_repository_graph(tmp_path); g2=build_repository_graph(tmp_path)
    assert g1==g2
    assert {"from":"a.py","to":"b.py","type":"imports"} in g1["edges"]
    impact=analyze_change_impact(g1,["b.py"])
    assert impact["impacted_files"]==[{"path":"b.py","distance":0},{"path":"a.py","distance":1}]


def test_unknown_changed_path_is_reported(tmp_path:Path):
    (tmp_path/"x.py").write_text("x=1\n",encoding="utf-8")
    graph=build_repository_graph(tmp_path)
    impact=analyze_change_impact(graph,["missing.py"])
    assert impact["unknown_paths"]==["missing.py"]
