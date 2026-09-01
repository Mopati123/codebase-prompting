from pathlib import Path
from repo_intelligence.developer_os import build_developer_plan, reconcile_developer_run
from repo_intelligence.graph import build_repository_graph
from repo_intelligence.impact import analyze_change_impact


def _fixture(tmp_path:Path):
    (tmp_path/"src").mkdir()
    (tmp_path/"tests").mkdir()
    (tmp_path/"src"/"calc.py").write_text("def add(a,b):\n    return a+b\n",encoding="utf-8")
    (tmp_path/"tests"/"test_calc.py").write_text(
        "from src.calc import add\n\ndef test_add():\n    assert add(1,2)==3\n",
        encoding="utf-8",
    )
    graph=build_repository_graph(tmp_path)
    impact=analyze_change_impact(graph,["src/calc.py"])
    return graph,impact


def test_developer_plan_is_deterministic_and_proposal_only(tmp_path:Path):
    graph,impact=_fixture(tmp_path)
    p1=build_developer_plan(graph,impact,"Fix calc behavior")
    p2=build_developer_plan(graph,impact,"Fix calc behavior")
    assert p1==p2
    assert p1["authority_semantics"]=="proposal_plan_only"
    assert p1["execution_authorized"] is False
    patch=[s for s in p1["stages"] if s["name"]=="patch"][0]
    assert patch["requires_execution_authority"] is True
    assert p1["invariants"]["retest_required_after_patch"] is True
    assert p1["plan_sha256"].startswith("sha256:")


def test_developer_plan_refuses_unknown_changed_paths(tmp_path:Path):
    graph=build_repository_graph(tmp_path)
    impact=analyze_change_impact(graph,["missing.py"])
    try:
        build_developer_plan(graph,impact,"Fix missing")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def test_developer_run_reconciliation_requires_all_receipts_and_patch_token(tmp_path:Path):
    graph,impact=_fixture(tmp_path)
    plan=build_developer_plan(graph,impact,"Fix calc behavior")
    receipts=[
        {"stage":"inspect","ok":True},
        {"stage":"baseline_tests","ok":True},
        {"stage":"patch","ok":True,"execution_token_present":True},
        {"stage":"retest","ok":True},
        {"stage":"recompute_repository_intelligence","ok":True},
        {"stage":"evidence_finalize","ok":True},
    ]
    result=reconcile_developer_run(plan,receipts)
    assert result["reconciled"] is True
    assert result["patch_execution_token_verified"] is True


def test_reconciliation_refuses_missing_retest(tmp_path:Path):
    graph,impact=_fixture(tmp_path)
    plan=build_developer_plan(graph,impact,"Fix calc behavior")
    receipts=[
        {"stage":"inspect","ok":True},
        {"stage":"baseline_tests","ok":True},
        {"stage":"patch","ok":True,"execution_token_present":True},
        {"stage":"recompute_repository_intelligence","ok":True},
        {"stage":"evidence_finalize","ok":True},
    ]
    result=reconcile_developer_run(plan,receipts)
    assert result["reconciled"] is False
    assert "retest" in result["missing_stages"]
