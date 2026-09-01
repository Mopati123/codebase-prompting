from pathlib import Path
from repo_intelligence.graph import build_repository_graph
from repo_intelligence.impact import analyze_change_impact


def test_graph_and_impact_are_deterministic(tmp_path:Path):
    (tmp_path/"a.py").write_text("from b import f\n\ndef g():\n    return f()\n",encoding="utf-8")
    (tmp_path/"b.py").write_text("def f():\n    return 1\n",encoding="utf-8")
    g1=build_repository_graph(tmp_path); g2=build_repository_graph(tmp_path)
    assert g1==g2
    assert {"from":"a.py","to":"b.py","type":"imports"} in g1["edges"]
    assert {"from":"a.py::g","to":"b.py::f","type":"calls"} in g1["symbol_edges"]
    impact=analyze_change_impact(g1,["b.py"])
    assert impact["impacted_files"]==[
        {"path":"b.py","distance":0,"reasons":["changed"]},
        {"path":"a.py","distance":1,"reasons":["imports"]},
    ]


def test_test_mapping_and_component_impact(tmp_path:Path):
    (tmp_path/"src").mkdir()
    (tmp_path/"tests").mkdir()
    (tmp_path/"src"/"calc.py").write_text("def add(a,b):\n    return a+b\n",encoding="utf-8")
    (tmp_path/"tests"/"test_calc.py").write_text(
        "from src.calc import add\n\ndef test_add():\n    assert add(1,2)==3\n",
        encoding="utf-8",
    )
    graph=build_repository_graph(tmp_path)
    assert {"from":"tests/test_calc.py","to":"src/calc.py","type":"tests"} in graph["edges"]
    impact=analyze_change_impact(graph,["src/calc.py"])
    assert impact["impacted_tests"]==[
        {"path":"tests/test_calc.py","distance":1,"reasons":["imports","tests"]}
    ]
    assert impact["impacted_components"]==["src","tests"]


def test_local_symbol_call_edge(tmp_path:Path):
    (tmp_path/"mod.py").write_text(
        "def helper():\n    return 1\n\ndef caller():\n    return helper()\n",
        encoding="utf-8",
    )
    graph=build_repository_graph(tmp_path)
    assert {"from":"mod.py::caller","to":"mod.py::helper","type":"calls"} in graph["symbol_edges"]


def test_unknown_changed_path_is_reported(tmp_path:Path):
    (tmp_path/"x.py").write_text("x=1\n",encoding="utf-8")
    graph=build_repository_graph(tmp_path)
    impact=analyze_change_impact(graph,["missing.py"])
    assert impact["unknown_paths"]==["missing.py"]
