from pathlib import Path
from unittest import mock

from repo_intelligence.rehearsal import rehearse_admission


def test_admission_rehearsal_composes_full_chain_without_runtime(tmp_path:Path):
    target=tmp_path/"target"
    target.mkdir()
    (target/"README.md").write_text("# target\n",encoding="utf-8")

    fake={
        "schema_version":"1.1",
        "execution_requested":False,
        "binding_sha256":"sha256:"+"a"*64,
        "kernel_head":"a5d2d913e41fd9a80212825921d0919fd8320b3b",
        "kernel_result":{
            "admission":{
                "status":"admitted",
                "plan":{"execution_token":{"token_id":"sha256:test"}},
            },
            "runtime":None,
        },
        "harness_receipt_sha256":"sha256:"+"b"*64,
    }
    with mock.patch("repo_intelligence.rehearsal.invoke_kernel_binding",return_value=fake) as invoke:
        receipt=rehearse_admission(
            target_root=target,
            changed_paths=["README.md"],
            change_request="Inspect README impact",
            inspect_path="README.md",
            conversation_id="123e4567-e89b-12d3-a456-426614174000",
            kernel_root=tmp_path/"kernel",
        )

    assert invoke.call_args.kwargs["execute"] is False
    assert receipt["admitted"] is True
    assert receipt["execution_token_present"] is True
    assert receipt["runtime_executed"] is False
    assert receipt["rehearsal_sha256"].startswith("sha256:")


def test_rehearsal_refuses_inspect_path_outside_scope(tmp_path:Path):
    target=tmp_path/"target"
    target.mkdir()
    (target/"README.md").write_text("# target\n",encoding="utf-8")
    (target/"OTHER.md").write_text("# other\n",encoding="utf-8")
    try:
        rehearse_admission(
            target_root=target,
            changed_paths=["README.md"],
            change_request="Inspect README impact",
            inspect_path="OTHER.md",
            conversation_id="123e4567-e89b-12d3-a456-426614174000",
            kernel_root=tmp_path/"kernel",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
