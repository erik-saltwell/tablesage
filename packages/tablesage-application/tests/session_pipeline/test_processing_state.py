from __future__ import annotations

import os
import shutil
from collections.abc import Callable
from pathlib import Path

from tablesage_application.session_pipeline import processing_state
from tablesage_application.session_pipeline.processing_state import CompletionRecord, ProcessingState


def _set_section(name: str, value: object) -> Callable[[ProcessingState], None]:
    def apply(state: ProcessingState) -> None:
        state.sections[name] = value

    return apply


def test_missing_document_loads_empty(tmp_path: Path) -> None:
    state = processing_state.load(tmp_path)

    assert state == ProcessingState()
    assert not processing_state.exists(tmp_path)


def test_update_writes_the_document_and_keeps_the_previous_version(tmp_path: Path) -> None:
    processing_state.update(tmp_path, _set_section("a", {"v": 1}), reason="test")
    processing_state.update(tmp_path, _set_section("a", {"v": 2}), reason="test")

    assert processing_state.load(tmp_path).sections["a"] == {"v": 2}
    backup = ProcessingState.model_validate_json(processing_state.backup_path(tmp_path).read_bytes())
    assert backup.sections["a"] == {"v": 1}


def test_update_that_changes_nothing_writes_nothing(tmp_path: Path) -> None:
    processing_state.update(tmp_path, _set_section("a", 1), reason="test")
    before = processing_state.state_path(tmp_path).stat().st_mtime_ns

    processing_state.update(tmp_path, _set_section("a", 1), reason="test")

    assert processing_state.state_path(tmp_path).stat().st_mtime_ns == before
    assert not processing_state.backup_path(tmp_path).exists()


def test_unreadable_document_falls_back_to_its_backup(tmp_path: Path) -> None:
    processing_state.update(tmp_path, _set_section("a", 1), reason="test")
    processing_state.update(tmp_path, _set_section("a", 2), reason="test")
    processing_state.state_path(tmp_path).write_text("{ not json", encoding="utf-8")

    assert processing_state.load(tmp_path).sections["a"] == 1


def test_unreadable_document_and_backup_load_empty(tmp_path: Path) -> None:
    processing_state.state_path(tmp_path).write_text("{ not json", encoding="utf-8")
    processing_state.backup_path(tmp_path).write_text("also not json", encoding="utf-8")

    assert processing_state.load(tmp_path) == ProcessingState()


def test_delete_removes_document_and_backup(tmp_path: Path) -> None:
    processing_state.update(tmp_path, _set_section("a", 1), reason="test")
    processing_state.update(tmp_path, _set_section("a", 2), reason="test")

    processing_state.delete(tmp_path)

    assert not processing_state.state_path(tmp_path).exists()
    assert not processing_state.backup_path(tmp_path).exists()


def test_records_round_trip(tmp_path: Path) -> None:
    record = CompletionRecord(
        completed_at=processing_state.now(), inputs={"artifact:transcript": processing_state.InputFingerprint(sha256="x")}
    )

    def apply(state: ProcessingState) -> None:
        state.records["cleaned_transcript"] = record

    processing_state.update(tmp_path, apply, reason="test")

    assert processing_state.load(tmp_path).records["cleaned_transcript"] == record


def test_file_fingerprint_is_the_content_hash_and_missing_is_none(tmp_path: Path) -> None:
    first = tmp_path / "a.txt"
    second = tmp_path / "b.txt"
    first.write_text("same", encoding="utf-8")
    second.write_text("same", encoding="utf-8")

    first_print = processing_state.file_fingerprint(first)
    second_print = processing_state.file_fingerprint(second)

    assert first_print is not None and second_print is not None
    assert first_print.sha256 == second_print.sha256
    assert processing_state.file_fingerprint(tmp_path / "missing.txt") is None


def test_copied_file_with_a_new_mtime_still_matches(tmp_path: Path) -> None:
    source = tmp_path / "a.txt"
    source.write_text("content", encoding="utf-8")
    recorded = processing_state.file_fingerprint(source)
    assert recorded is not None and recorded.mtime_ns is not None
    later = recorded.mtime_ns + 5_000_000_000
    copy = tmp_path / "copy" / "a.txt"
    copy.parent.mkdir()
    shutil.copyfile(source, copy)
    os.utime(copy, ns=(later, later))

    assert processing_state.file_matches(copy, recorded)


def test_changed_content_does_not_match_and_missing_file_does_not_match(tmp_path: Path) -> None:
    path = tmp_path / "a.txt"
    path.write_text("content", encoding="utf-8")
    recorded = processing_state.file_fingerprint(path)
    assert recorded is not None

    path.write_text("edited!", encoding="utf-8")
    assert not processing_state.file_matches(path, recorded)
    path.unlink()
    assert not processing_state.file_matches(path, recorded)


def test_value_fingerprint_ignores_key_order_but_not_values() -> None:
    assert processing_state.value_fingerprint({"a": 1, "b": 2}) == processing_state.value_fingerprint({"b": 2, "a": 1})
    assert processing_state.value_fingerprint({"a": 1}) != processing_state.value_fingerprint({"a": 2})


def test_needs_legacy_import_only_for_folders_with_old_artifacts_and_no_document(tmp_path: Path) -> None:
    assert not processing_state.needs_legacy_import(tmp_path)
    (tmp_path / "transcript.json").write_text("{}", encoding="utf-8")
    assert processing_state.needs_legacy_import(tmp_path)
    processing_state.update(tmp_path, _set_section("a", 1), reason="test")
    assert not processing_state.needs_legacy_import(tmp_path)
