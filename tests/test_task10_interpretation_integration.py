from __future__ import annotations

import csv
from dataclasses import replace
import hashlib
import inspect
import json
from pathlib import Path
import subprocess

import pytest

from research.run_task10_dependency_interpretation import (
    _build_manifest,
    _run_task10_from_bundle,
    assert_clean_committed_task10_worktree,
    build_parser,
    run_task10,
)
from research.task10_interpretation_contract import (
    TASK9_EVIDENCE_PACKAGE_FILENAME,
    TASK10_LOGICAL_FILENAMES,
)
from research.task10_interpretation_io import _load_task9_evidence_bytes
from tests.test_task10_interpretation_io import make_synthetic_task9_evidence_zip


def _synthetic_bundle():
    package = make_synthetic_task9_evidence_zip()
    bundle = _load_task9_evidence_bytes(
        package, expected_sha256=hashlib.sha256(package).hexdigest()
    )
    main = {
        timeframe: tuple({**row, "status": "DEFINED"} for row in rows)
        for timeframe, rows in bundle.main_raw_by_tf.items()
    }
    partial = {
        timeframe: tuple({**row, "status": "DEFINED"} for row in rows)
        for timeframe, rows in bundle.partial_by_tf.items()
    }
    cross = tuple(
        {
            **row,
            "n_undefined_tf": 0,
            "rho_min": 0.25,
            "rho_max": 0.25,
            "rho_range": 0.0,
        }
        for row in bundle.cross_tf
    )
    return replace(
        bundle,
        main_raw_by_tf=main,
        partial_by_tf=partial,
        cross_tf=cross,
    )


def _artifact_bytes(directory: Path) -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in directory.iterdir()}


def test_private_synthetic_pipeline_is_byte_deterministic_and_scope_locked(tmp_path: Path):
    bundle = _synthetic_bundle()
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_zip = tmp_path / "first.zip"
    second_zip = tmp_path / "second.zip"

    first_manifest = _run_task10_from_bundle(
        bundle,
        first_dir,
        implementation_commit="a" * 40,
        output_zip=first_zip,
    )
    second_manifest = _run_task10_from_bundle(
        bundle,
        second_dir,
        implementation_commit="a" * 40,
        output_zip=second_zip,
    )

    assert set(_artifact_bytes(first_dir)) == set(TASK10_LOGICAL_FILENAMES)
    assert _artifact_bytes(first_dir) == _artifact_bytes(second_dir)
    assert first_zip.read_bytes() == second_zip.read_bytes()
    assert first_manifest == second_manifest
    assert first_manifest["task10_implementation_commit"] == "a" * 40
    assert first_manifest["task9_evidence_package_filename"] == (
        TASK9_EVIDENCE_PACKAGE_FILENAME
    )
    assert first_manifest["task9_evidence_package_sha256"] == bundle.evidence_zip_sha256
    assert first_manifest["main_relationship_dossier_count"] == 78
    assert first_manifest["partial_delta_eligible_pair_count"] == 66
    assert first_manifest["control_feature_non_applicable_pair_count"] == 12
    assert first_manifest["feature_dossier_count"] == 13
    assert first_manifest["supplementary_evidence_row_count"] == 960
    assert first_manifest["future_ablation_hypothesis_count"] == 0
    for field in (
        "raw_cross_tf_pooling",
        "new_association_statistics_computed",
        "ranking_performed",
        "cutoff_applied",
        "threshold_applied",
        "score_computed",
        "outcome_used",
        "ablation_executed",
        "causal_replay_executed",
        "feature_removal_recommended",
    ):
        assert first_manifest[field] is False

    supplementary_path = first_dir / "TASK10_SUPPLEMENTARY_EVIDENCE.csv"
    with supplementary_path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 960
    assert len(json.loads((first_dir / "TASK10_MAIN_RELATIONSHIP_DOSSIERS.json").read_text())) == 78
    assert len(json.loads((first_dir / "TASK10_FEATURE_DOSSIERS.json").read_text())) == 13
    assert json.loads((first_dir / "TASK10_FUTURE_ABLATION_HYPOTHESES.json").read_text()) == []


def test_public_pipeline_signature_and_cli_expose_no_synthetic_or_scope_overrides():
    public_parameters = inspect.signature(run_task10).parameters
    assert "expected_sha256" not in public_parameters
    assert "implementation_commit" not in public_parameters
    assert "loader" not in public_parameters

    parser = build_parser()
    option_strings = {
        option
        for action in parser._actions
        for option in action.option_strings
    }
    assert option_strings == {
        "-h",
        "--help",
        "--input-evidence",
        "--output-dir",
        "--output-zip",
    }


def test_manifest_rejects_partial_or_control_classification_count_drift():
    with pytest.raises(ValueError, match="locked output counts differ"):
        _build_manifest(
            _synthetic_bundle(),
            implementation_commit="a" * 40,
            main_count=78,
            partial_eligible_count=65,
            control_non_applicable_count=13,
            supplementary_count=960,
            feature_count=13,
            hypothesis_count=0,
        )


def test_public_flow_stops_at_guard_and_persists_exact_guard_sha(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import research.run_task10_dependency_interpretation as runner

    def blocked_guard():
        raise RuntimeError("guard blocked")

    def loader_must_not_run(_path):
        raise AssertionError("loader ran after a failed provenance guard")

    monkeypatch.setattr(runner, "assert_clean_committed_task10_worktree", blocked_guard)
    monkeypatch.setattr(runner, "load_task9_evidence_package", loader_must_not_run)
    with pytest.raises(RuntimeError, match="guard blocked"):
        run_task10(tmp_path / "unused.zip", tmp_path / "blocked")

    guard_sha = "b" * 40
    monkeypatch.setattr(
        runner, "assert_clean_committed_task10_worktree", lambda: guard_sha
    )
    monkeypatch.setattr(
        runner, "load_task9_evidence_package", lambda _path: _synthetic_bundle()
    )
    manifest = run_task10(tmp_path / "synthetic.zip", tmp_path / "allowed")
    written = json.loads(
        (tmp_path / "allowed" / "TASK10_MANIFEST.json").read_text(encoding="utf-8")
    )
    assert manifest["task10_implementation_commit"] == guard_sha
    assert written["task10_implementation_commit"] == guard_sha


def _init_guard_repo(path: Path, *, include_runner: bool = True) -> str:
    required = [
        "research/task10_interpretation_contract.py",
        "research/task10_interpretation_io.py",
        "research/task10_interpretation_reports.py",
    ]
    if include_runner:
        required.append("research/run_task10_dependency_interpretation.py")
    for relative in required:
        target = path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("locked\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Task10 Test"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "task10@example.invalid"], cwd=path, check=True)
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=path, check=True)
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_provenance_guard_accepts_clean_head_and_rejects_dirty_or_missing_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import research.run_task10_dependency_interpretation as runner

    clean = tmp_path / "clean"
    clean.mkdir()
    clean_head = _init_guard_repo(clean)
    monkeypatch.setattr(runner, "_REPOSITORY_ROOT", clean)
    assert assert_clean_committed_task10_worktree() == clean_head

    tracked = clean / "research/task10_interpretation_contract.py"
    tracked.write_text("unstaged\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="tracked worktree is not clean"):
        assert_clean_committed_task10_worktree()
    subprocess.run(["git", "add", str(tracked)], cwd=clean, check=True)
    with pytest.raises(RuntimeError, match="tracked worktree is not clean"):
        assert_clean_committed_task10_worktree()

    missing = tmp_path / "missing"
    missing.mkdir()
    _init_guard_repo(missing, include_runner=False)
    monkeypatch.setattr(runner, "_REPOSITORY_ROOT", missing)
    with pytest.raises(RuntimeError, match="required Task 10 path is absent from HEAD"):
        assert_clean_committed_task10_worktree()
