import uuid
from pathlib import Path

import pytest
from pydantic import ValidationError
from tablesage_application.paths import ARTIFACTS, LEDGER_PAIR_MARKER, ArtifactName
from tablesage_application.session_pipeline.artifacts import delete_artifact, exportable_artifacts, session_artifacts
from tablesage_application.session_pipeline.generate_ledger import Ledger, LedgerContent, LedgerGenerationResponse, Narration
from tablesage_application.session_pipeline.generate_recap_summary import can_generate_recap_summary
from tablesage_application.session_pipeline.scene_breakdown import (
    LedgerRange,
    Scene,
    SceneBreakdownContent,
    load_current_scene_breakdown,
    persist_ledger_pair,
)


def _scene(*ranges: tuple[int, int]) -> Scene:
    return Scene(
        title="The gate",
        location="City gate",
        participants=["Zaria"],
        situation="Enter the city.",
        outcome="The gate opens.",
        carry_forward=[],
        signature_detail=None,
        ledger_ranges=[LedgerRange(start_index=start, end_index=end) for start, end in ranges],
    )


def _ledger(count: int = 1) -> Ledger:
    return Ledger(
        session_id=uuid.UUID(int=1),
        session_name="Session One",
        starting_situation="At the gate.",
        utterances=[Narration(type="narration", source="Game Master", fact="The gate opens.") for _ in range(count)],
    )


def _content(*scenes: Scene) -> SceneBreakdownContent:
    return SceneBreakdownContent(ending_situation="Inside the city.", scenes=list(scenes))


def test_interleaved_scenes_partition_entries_once() -> None:
    content = _content(_scene((0, 1), (4, 4)), _scene((2, 3), (5, 5)))
    content.validate_coverage(6)
    LedgerGenerationResponse(
        starting_situation="At the gate.", ledger=LedgerContent(utterances=_ledger(6).utterances), scene_breakdown=content
    )


@pytest.mark.parametrize(
    "scenes,count",
    [
        ([_scene((0, 0))], 2),  # trailing gap
        ([_scene((1, 1))], 2),  # initial gap
        ([_scene((0, 2)), _scene((2, 3))], 4),  # overlap
        ([_scene((0, 2))], 2),  # outside Ledger
        ([_scene((0, 0), (0, 0))], 1),  # duplicate within scene
        ([], 1),
    ],
)
def test_invalid_coverage_rejects_the_whole_candidate(scenes: list[Scene], count: int) -> None:
    with pytest.raises(ValidationError):
        LedgerGenerationResponse(
            starting_situation="At the gate.", ledger=LedgerContent(utterances=_ledger(count).utterances), scene_breakdown=_content(*scenes)
        )


def test_empty_session_and_nullable_signature_are_supported() -> None:
    _content().validate_coverage(0)
    assert _scene((0, 0)).signature_detail is None
    data = _scene((0, 0)).model_dump()
    del data["signature_detail"]
    with pytest.raises(ValidationError, match="signature_detail"):
        Scene.model_validate(data)
    with pytest.raises(ValidationError):
        LedgerRange(start_index=True, end_index=1)
    with pytest.raises(ValidationError):
        LedgerRange(start_index=1, end_index=0)


def test_generation_canonicalizes_order_without_changing_assignments() -> None:
    response = LedgerGenerationResponse(
        starting_situation="At the gate.",
        ledger=LedgerContent(utterances=_ledger(3).utterances),
        scene_breakdown=_content(_scene((1, 1)), _scene((2, 2), (0, 0))),
    )
    assert [[span.start_index for span in scene.ledger_ranges] for scene in response.scene_breakdown.scenes] == [[0, 2], [1]]
    with pytest.raises(ValueError, match="ordered"):
        _content(_scene((1, 1)), _scene((0, 0))).validate_coverage(2)


def test_pair_persistence_keeps_sibling_provenance_and_downstream_outputs(tmp_path: Path) -> None:
    (tmp_path / "recap_summary.md").write_text("old recap")
    (tmp_path / "summary.md").write_text("old summary")
    saved = persist_ledger_pair(_ledger(), _content(_scene((0, 0))), tmp_path)
    assert load_current_scene_breakdown(tmp_path) == saved
    assert saved.starting_situation == _ledger().starting_situation
    assert can_generate_recap_summary(tmp_path) == (True, None)
    assert (tmp_path / "ledger.md").exists()
    assert not (tmp_path / "scene_breakdown.md").exists()
    assert (tmp_path / "summary.md").read_text() == "old summary"
    assert (tmp_path / "recap_summary.md").read_text() == "old recap"
    assert session_artifacts(tmp_path)[ArtifactName.SCENE_BREAKDOWN]
    assert not ARTIFACTS[ArtifactName.SCENE_BREAKDOWN].should_show_in_ui
    assert ArtifactName.SCENE_BREAKDOWN not in exportable_artifacts(tmp_path)
    # The digest records joint-generation provenance, but sibling edits do not
    # make Scene Breakdown unusable.
    with (tmp_path / "ledger.json").open("a") as stream:
        stream.write("\n")
    assert can_generate_recap_summary(tmp_path) == (True, None)


@pytest.mark.parametrize("failure_target", ["ledger.md", "scene_breakdown.json"])
def test_failed_replacement_restores_pair_and_preserves_downstream_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_target: str,
) -> None:
    persist_ledger_pair(_ledger(), _content(_scene((0, 0))), tmp_path)
    (tmp_path / "recap_summary.md").write_text("old recap")
    (tmp_path / "summary.md").write_text("old summary")
    originals = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    replace, unlink = Path.replace, Path.unlink

    def fail_replace(self: Path, target: Path) -> Path:
        if target.name == failure_target:
            raise OSError("disk failure")
        return replace(self, target)

    def fail_unlink(self: Path, missing_ok: bool = False) -> None:
        if self.name == failure_target:
            raise OSError("disk failure")
        unlink(self, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "replace", fail_replace)
    monkeypatch.setattr(Path, "unlink", fail_unlink)
    with pytest.raises(OSError, match="disk failure"):
        persist_ledger_pair(_ledger(2), _content(_scene((0, 1))), tmp_path)
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == originals
    assert load_current_scene_breakdown(tmp_path).scenes[0].ledger_ranges[0].end_index == 0


def test_interruption_blocks_consumers_until_regeneration(tmp_path: Path) -> None:
    persist_ledger_pair(_ledger(), _content(_scene((0, 0))), tmp_path)
    (tmp_path / LEDGER_PAIR_MARKER).write_text("interrupted")
    assert not session_artifacts(tmp_path)[ArtifactName.LEDGER]
    assert can_generate_recap_summary(tmp_path)[0] is False
    persist_ledger_pair(_ledger(), _content(_scene((0, 0))), tmp_path)
    assert can_generate_recap_summary(tmp_path) == (True, None)
    delete_artifact(tmp_path, ArtifactName.LEDGER)
    assert not (tmp_path / "scene_breakdown.json").exists()


@pytest.mark.parametrize("field,value", [("session_name", "Other session"), ("starting_situation", "A different opening.")])
def test_sibling_metadata_may_diverge_after_a_hand_edit(tmp_path: Path, field: str, value: str) -> None:
    saved = persist_ledger_pair(_ledger(), _content(_scene((0, 0))), tmp_path)
    changed = saved.model_copy(update={field: value})
    (tmp_path / "scene_breakdown.json").write_text(changed.model_dump_json())
    assert load_current_scene_breakdown(tmp_path) == changed


def test_invalid_pair_never_changes_existing_outputs(tmp_path: Path) -> None:
    persist_ledger_pair(_ledger(), _content(_scene((0, 0))), tmp_path)
    originals = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    with pytest.raises(ValueError):
        persist_ledger_pair(_ledger(2), _content(_scene((0, 0))), tmp_path)
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == originals


def test_interrupt_immediately_after_rename_restores_changed_target(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    persist_ledger_pair(_ledger(), _content(_scene((0, 0))), tmp_path)
    originals = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    replace = Path.replace

    def interrupted_replace(self: Path, target: Path) -> Path:
        result = replace(self, target)
        if target.name == "scene_breakdown.json":
            raise KeyboardInterrupt
        return result

    monkeypatch.setattr(Path, "replace", interrupted_replace)
    with pytest.raises(KeyboardInterrupt):
        persist_ledger_pair(_ledger(2), _content(_scene((0, 1))), tmp_path)
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == originals
