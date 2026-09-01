"""Private integration coverage for Task 11 deterministic outputs."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from research.run_task11_hypothesis_registration import (
    _build_manifest,
    _run_task11_from_bundle,
)
from research.task11_hypothesis_contract import (
    OUTPUT_ZIP_FILENAME,
    TASK11_FALSE_SCOPE_FIELDS,
    TASK11_LOGICAL_FILENAMES,
    TASK11_MANIFEST_FIELDS,
)
from research.task11_hypothesis_io import _json_bytes, write_task11_outputs
from research.task11_hypothesis_registry import build_hypothesis_registry
from test_task11_hypothesis_io import (
    load_synthetic_task10,
    make_synthetic_task10_production_zip,
)


def artifact_bytes(directory: Path) -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in directory.iterdir()}


def _manifest_and_registry():
    bundle = load_synthetic_task10(make_synthetic_task10_production_zip())
    registry = build_hypothesis_registry(bundle.main_dossiers)
    registry_bytes = _json_bytes(registry)
    manifest = _build_manifest(
        bundle,
        implementation_commit="a" * 40,
        hypothesis_registry_sha256=hashlib.sha256(registry_bytes).hexdigest(),
        main_pair_count=78,
        hypothesis_count=78,
        duration_control_eligible_count=66,
        control_feature_non_applicable_count=12,
        deterministic_context_pair_count=4,
    )
    return registry, registry_bytes, manifest


def test_build_manifest_rejects_numerically_equal_wrong_type_count():
    bundle = load_synthetic_task10(make_synthetic_task10_production_zip())
    registry = build_hypothesis_registry(bundle.main_dossiers)
    with pytest.raises(ValueError, match="observed counts"):
        _build_manifest(
            bundle,
            implementation_commit="a" * 40,
            hypothesis_registry_sha256=hashlib.sha256(
                _json_bytes(registry)
            ).hexdigest(),
            main_pair_count=78.0,
            hypothesis_count=78,
            duration_control_eligible_count=66,
            control_feature_non_applicable_count=12,
            deterministic_context_pair_count=4,
        )


def test_private_pipeline_is_byte_deterministic_and_scope_locked(tmp_path: Path):
    package = make_synthetic_task10_production_zip()
    bundle = load_synthetic_task10(package)
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_dir = first_root / "logical"
    second_dir = second_root / "logical"
    first_zip = first_root / OUTPUT_ZIP_FILENAME
    second_zip = second_root / OUTPUT_ZIP_FILENAME

    first_manifest = _run_task11_from_bundle(
        bundle,
        first_dir,
        implementation_commit="a" * 40,
        output_zip=first_zip,
    )
    second_manifest = _run_task11_from_bundle(
        bundle,
        second_dir,
        implementation_commit="a" * 40,
        output_zip=second_zip,
    )

    first_artifacts = artifact_bytes(first_dir)
    assert set(first_artifacts) == set(TASK11_LOGICAL_FILENAMES)
    assert first_artifacts == artifact_bytes(second_dir)
    assert first_zip.read_bytes() == second_zip.read_bytes()
    assert first_manifest == second_manifest

    registry_bytes = first_artifacts["TASK11_HYPOTHESIS_REGISTRY.json"]
    manifest_bytes = first_artifacts["TASK11_MANIFEST.json"]
    registry = json.loads(registry_bytes)
    manifest = json.loads(manifest_bytes)
    assert len(registry) == 78
    assert set(manifest) == set(TASK11_MANIFEST_FIELDS)
    assert manifest["hypothesis_registry_sha256"] == hashlib.sha256(
        registry_bytes
    ).hexdigest()
    for field in TASK11_FALSE_SCOPE_FIELDS:
        assert manifest[field] is False
    for payload in (registry_bytes, manifest_bytes):
        assert payload.endswith(b"\n")
        assert not payload.endswith(b"\n\n")
        assert b"NaN" not in payload
        assert b"Infinity" not in payload
        assert _json_bytes(json.loads(payload)) == payload

    with zipfile.ZipFile(first_zip) as archive:
        assert archive.namelist() == sorted(TASK11_LOGICAL_FILENAMES)
        for info in archive.infolist():
            assert info.date_time == (1980, 1, 1, 0, 0, 0)
            assert info.create_system == 3
            assert info.external_attr >> 16 == 0o100644
            assert info.extra == b""


def test_private_pipeline_rejects_noncanonical_zip_before_output(tmp_path: Path):
    bundle = load_synthetic_task10(make_synthetic_task10_production_zip())
    output_dir = tmp_path / "noncanonical-output"
    output_zip = tmp_path / "noncanonical.zip"
    with pytest.raises(ValueError, match="production ZIP basename"):
        _run_task11_from_bundle(
            bundle,
            output_dir,
            implementation_commit="a" * 40,
            output_zip=output_zip,
        )
    assert not output_dir.exists()
    assert not output_zip.exists()


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("hypothesis_count", 77),
        ("logical_file_count", 3),
        ("task11_spec_commit", "0" * 40),
        ("task10_production_package_sha256", "0" * 64),
        ("ranking_performed", True),
        ("score_computed", True),
        ("threshold_applied", True),
        ("ablation_executed", True),
        ("causal_replay_executed", True),
        ("feature_selection_performed", True),
    ],
)
def test_writer_rejects_manifest_drift_before_creating_output(
    tmp_path: Path, field: str, bad_value: object
):
    registry, _, manifest = _manifest_and_registry()
    manifest[field] = bad_value
    rejected_root = tmp_path / "rejected"
    output_dir = rejected_root / "logical"
    output_zip = rejected_root / OUTPUT_ZIP_FILENAME
    with pytest.raises(ValueError, match="manifest"):
        write_task11_outputs(
            output_dir,
            implementation_commit="a" * 40,
            registry=registry,
            manifest=manifest,
            output_zip=output_zip,
        )
    assert not output_dir.exists()
    assert not output_zip.exists()


@pytest.mark.parametrize("mutation", ["missing", "extra"])
def test_writer_rejects_manifest_schema_drift_before_creating_output(
    tmp_path: Path, mutation: str
):
    registry, _, manifest = _manifest_and_registry()
    if mutation == "missing":
        del manifest["task"]
    else:
        manifest["unexpected"] = "value"
    output_dir = tmp_path / "logical"
    output_zip = tmp_path / OUTPUT_ZIP_FILENAME
    with pytest.raises(ValueError, match="manifest"):
        write_task11_outputs(
            output_dir,
            implementation_commit="a" * 40,
            registry=registry,
            manifest=manifest,
            output_zip=output_zip,
        )
    assert not output_dir.exists()
    assert not output_zip.exists()


def test_writer_rejects_registry_hash_mismatch_before_creating_output(tmp_path: Path):
    registry, _, manifest = _manifest_and_registry()
    manifest["hypothesis_registry_sha256"] = "0" * 64
    output_dir = tmp_path / "logical"
    output_zip = tmp_path / OUTPUT_ZIP_FILENAME
    with pytest.raises(ValueError, match="manifest"):
        write_task11_outputs(
            output_dir,
            implementation_commit="a" * 40,
            registry=registry,
            manifest=manifest,
            output_zip=output_zip,
        )
    assert not output_dir.exists()
    assert not output_zip.exists()
