from pathlib import Path
from repo_intelligence.developer_os import build_developer_plan
from repo_intelligence.graph import build_repository_graph
from repo_intelligence.hpl_binding import (
    build_repo_patch_binding,
    build_repo_read_binding,
    build_test_execute_binding,
    python_test_path_to_module,
)
from repo_intelligence.impact import analyze_change_impact


def _plan(tmp_path:Path):
    (tmp_path/"src").mkdir()
    (tmp_path/"tests").mkdir()
    (tmp_path/"src"/"calc.py").write_text("def add(a,b):\n    return a+b\n",encoding="utf-8")
    (tmp_path/"tests"/"test_calc.py").write_text(
        "from src.calc import add\n\ndef test_add():\n    assert add(1,2)==3\n",
        encoding="utf-8",
    )
    graph=build_repository_graph(tmp_path)
    impact=analyze_change_impact(graph,["src/calc.py"])
    return build_developer_plan(graph,impact,"Fix calc")


def test_read_binding_matches_hpl_shape(tmp_path:Path):
    plan=_plan(tmp_path)
    binding=build_repo_read_binding(
        plan,conversation_id="123e4567-e89b-12d3-a456-426614174000",path="src/calc.py"
    )
    assert binding["request"]["actor"]=="openhands"
    assert binding["request"]["capabilities"]==["repo.read"]
    assert binding["policy"]["effect_type"]=="OPENHANDS_REPO_READ"
    assert binding["policy"]["allow_consequential"] is False
    assert binding["execution_authorized"] is False


def test_test_binding_uses_fixed_unittest_runner(tmp_path:Path):
    plan=_plan(tmp_path)
    binding=build_test_execute_binding(
        plan,workspace="codebase-prompting",test_path="tests/test_calc.py"
    )
    assert binding["policy"]["effect_args"]["runner"]=="python_unittest"
    assert binding["policy"]["effect_args"]["target"]=="tests.test_calc"
    assert binding["policy"]["effect_type"]=="OPENHANDS_TEST_EXECUTE"


def test_patch_binding_is_consequential_and_digest_bound(tmp_path:Path):
    plan=_plan(tmp_path)
    binding=build_repo_patch_binding(
        plan,
        workspace="codebase-prompting",
        path="src/calc.py",
        branch="feat/fix-calc",
        expected_preimage_sha256="sha256:"+"a"*64,
        replacement_text="def add(a,b):\n    return a+b\n",
    )
    assert binding["policy"]["effect_type"]=="OPENHANDS_REPO_PATCH"
    assert binding["policy"]["allow_consequential"] is True
    scope=binding["request"]["scope"]
    assert scope["replacement_sha256"].startswith("sha256:")
    assert binding["execution_authorized"] is False


def test_patch_binding_refuses_dependency_scope_expansion(tmp_path:Path):
    plan=_plan(tmp_path)
    try:
        build_repo_patch_binding(
            plan,
            workspace="codebase-prompting",
            path="tests/test_calc.py",
            branch="feat/fix-calc",
            expected_preimage_sha256="sha256:"+"a"*64,
            replacement_text="x=1\n",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def test_python_test_path_to_module():
    assert python_test_path_to_module("tests/test_example.py")=="tests.test_example"
