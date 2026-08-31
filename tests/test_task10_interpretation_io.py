import inspect
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile

import pytest

from research.combined_audit_contract import (
    DETERMINISTIC_RELATIONS,
    FEATURE_ROLE_COLUMNS,
    FEATURE_SPECS,
    TIMEFRAMES,
    DIRECTIONS,
)
from research.combined_audit_io import (
    COMBINED_MANIFEST_FILENAME,
    CROSS_TF_FIELDS,
    CROSS_TF_FILENAME,
    DETERMINISTIC_FIELDS,
    DETERMINISTIC_FILENAME,
    FEATURE_ROLE_FILENAME,
    MAIN_FIELDS,
    PARTIAL_FIELDS,
    SUPPLEMENTARY_FIELDS,
)
from research.task10_interpretation_contract import (
    MAIN_PAIR_KEYS,
    PARTIAL_PAIR_KEYS,
    SUPPLEMENTARY_PAIR_KEYS,
    TASK9_ACTIVITY_INPUT_SHA256,
    TASK9_AUDIT_CODE_COMMIT,
)
from research.task10_interpretation_io import (
    _load_task9_evidence_bytes,
    load_task9_evidence_package,
)


def _csv_bytes(fields, rows):
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode()


def _stat_row(fields, pair, *, evidence_scope=None):
    row = {field: "OK" for field in fields}
    if "feature_x" in fields:
        row.update({"feature_x": pair[0], "feature_y": pair[1]})
    for field in fields:
        if field.startswith("n_") or field in {"total_rows", "verified_rows", "failed_rows", "sign_agreement_count"}:
            row[field] = "1"
        elif field.startswith("rho") or field.startswith("controlled_rho_") or field == "delta_rho":
            row[field] = "0.25"
    if "total_rows" in fields:
        row.update({"total_rows": "1", "verified_rows": "1", "failed_rows": "0", "relation_type": "DETERMINISTIC"})
    if evidence_scope is not None:
        row["evidence_scope"] = evidence_scope
    return row


def make_synthetic_task9_evidence_zip(*, mutate=None, duplicate=None):
    members = {}
    roles = []
    for spec in FEATURE_SPECS.values():
        roles.append({field: getattr(spec, field) for field in FEATURE_ROLE_COLUMNS})
    members[FEATURE_ROLE_FILENAME] = _csv_bytes(FEATURE_ROLE_COLUMNS, roles)

    deterministic = []
    for timeframe in TIMEFRAMES:
        for relation in DETERMINISTIC_RELATIONS:
            row = _stat_row(DETERMINISTIC_FIELDS, ("unused_x", "unused_y"))
            row.update({
                "timeframe": timeframe,
                "relation_id": relation,
                "formula": "locked formula",
                "participating_features": "[]",
                "conditions": "locked conditions",
                "tolerance_policy": "locked tolerance",
            })
            deterministic.append(row)
    members[DETERMINISTIC_FILENAME] = _csv_bytes(DETERMINISTIC_FIELDS, deterministic)

    for timeframe in TIMEFRAMES:
        members[f"MAIN_SPEARMAN_{timeframe}.csv"] = _csv_bytes(
            MAIN_FIELDS, [_stat_row(MAIN_FIELDS, pair) for pair in MAIN_PAIR_KEYS]
        )
        members[f"PARTIAL_SPEARMAN_{timeframe}.csv"] = _csv_bytes(
            PARTIAL_FIELDS, [_stat_row(PARTIAL_FIELDS, pair) for pair in PARTIAL_PAIR_KEYS]
        )
        for direction in DIRECTIONS:
            members[f"SUPPLEMENTARY_{timeframe}_{direction}.csv"] = _csv_bytes(
                SUPPLEMENTARY_FIELDS,
                [_stat_row(SUPPLEMENTARY_FIELDS, pair, evidence_scope="SUPPLEMENTARY_ONLY") for pair in SUPPLEMENTARY_PAIR_KEYS],
            )

    cross = []
    for pair in MAIN_PAIR_KEYS:
        row = _stat_row(CROSS_TF_FIELDS, pair)
        row["controlled_eligible"] = "True"
        row["sign_agreement_tie"] = "False"
        row["sign_agreement_modal_signs"] = '["POSITIVE"]'
        cross.append(row)
    members[CROSS_TF_FILENAME] = _csv_bytes(CROSS_TF_FIELDS, cross)
    manifest = {
        "analysis_feature_count": 13,
        "audit_code_commit": TASK9_AUDIT_CODE_COMMIT,
        "audit_version": "1.0",
        "broker_company": "Synthetic Broker",
        "broker_server": "Synthetic Server",
        "control_variable": "active_bar_count",
        "deterministic_float_abs_tol": 1e-12,
        "deterministic_float_rel_tol": 1e-12,
        "input_leg_csv_filenames_by_tf": {tf: f"{tf}.csv" for tf in TIMEFRAMES},
        "input_zip_sha256": TASK9_ACTIVITY_INPUT_SHA256,
        "timeframes": list(TIMEFRAMES),
        "input_lock_status": "FINAL LOCK / PASS",
        "input_locked_leg_source_commit": "b43ed7a6d1d8538d8860934abbb24b0c9561a317",
        "input_snapshot_filenames_by_tf": {tf: f"snapshot-{tf}.csv" for tf in TIMEFRAMES},
        "status_gate_passed": True,
        "required_schema_gate_passed_by_tf": {tf: True for tf in TIMEFRAMES},
        "numeric_finiteness_gate_passed_by_tf": {tf: True for tf in TIMEFRAMES},
        "snapshot_hash_gate_passed_by_tf": {tf: True for tf in TIMEFRAMES},
        "snapshot_sha256_by_tf": {tf: "0" * 64 for tf in TIMEFRAMES},
        "symbols_by_tf": {tf: "SYNTH" for tf in TIMEFRAMES},
        "raw_cross_tf_pooling": False,
        "report_filenames": sorted([*members, COMBINED_MANIFEST_FILENAME]),
    }
    members[COMBINED_MANIFEST_FILENAME] = json.dumps(manifest).encode()
    if mutate:
        mutate(members, manifest)
        members[COMBINED_MANIFEST_FILENAME] = json.dumps(manifest).encode()
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in members.items():
            archive.writestr(name, data)
        if duplicate:
            archive.writestr(duplicate, members[duplicate])
    return output.getvalue()


def test_public_loader_rejects_noncanonical_sha_before_zip_parse(tmp_path: Path):
    package = tmp_path / "bad.zip"
    package.write_bytes(b"not-a-zip")

    with pytest.raises(ValueError, match="Task 9 Evidence SHA-256 mismatch"):
        load_task9_evidence_package(package)


def test_public_loader_has_no_sha_override():
    assert "expected_sha256" not in inspect.signature(
        load_task9_evidence_package
    ).parameters


def test_private_synthetic_seam_loads_complete_locked_shape():
    package = make_synthetic_task9_evidence_zip()

    bundle = _load_task9_evidence_bytes(
        package, expected_sha256=hashlib.sha256(package).hexdigest()
    )

    assert len(bundle.feature_roles) == 47
    assert len(bundle.deterministic_rows) == 44
    assert tuple(bundle.main_raw_by_tf) == TIMEFRAMES
    assert len(bundle.main_raw_by_tf["M5"]) == 78
    assert len(bundle.partial_by_tf["H1"]) == 66
    assert len(bundle.supplementary_by_tf_direction[("M15", "BEARISH")]) == 120
    assert len(bundle.cross_tf) == 78
    assert bundle.feature_roles[0]["formula"] == FEATURE_SPECS["active_bar_count"].formula


def test_private_synthetic_seam_rejects_sha_before_zip_parse():
    with pytest.raises(ValueError, match="Task 9 Evidence SHA-256 mismatch"):
        _load_task9_evidence_bytes(b"not-a-zip", expected_sha256="0" * 64)


def test_loader_rejects_duplicate_zip_member():
    package = make_synthetic_task9_evidence_zip(duplicate="MAIN_SPEARMAN_M5.csv")

    with pytest.raises(ValueError, match="duplicate ZIP members"):
        _load_task9_evidence_bytes(
            package, expected_sha256=hashlib.sha256(package).hexdigest()
        )


def test_loader_rejects_nonfinite_source_statistic():
    def mutate(members, _manifest):
        rows = list(csv.DictReader(io.StringIO(members["MAIN_SPEARMAN_M5.csv"].decode())))
        rows[0]["rho_raw"] = "NaN"
        members["MAIN_SPEARMAN_M5.csv"] = _csv_bytes(MAIN_FIELDS, rows)

    package = make_synthetic_task9_evidence_zip(mutate=mutate)

    with pytest.raises(ValueError, match="rho_raw.*non-finite"):
        _load_task9_evidence_bytes(
            package, expected_sha256=hashlib.sha256(package).hexdigest()
        )


def test_loader_rejects_wrong_main_pair_set():
    def mutate(members, _manifest):
        rows = list(csv.DictReader(io.StringIO(members["MAIN_SPEARMAN_M5.csv"].decode())))
        rows[0]["feature_y"] = "close_ols_slope"
        members["MAIN_SPEARMAN_M5.csv"] = _csv_bytes(MAIN_FIELDS, rows)

    package = make_synthetic_task9_evidence_zip(mutate=mutate)

    with pytest.raises(ValueError, match="pair set"):
        _load_task9_evidence_bytes(
            package, expected_sha256=hashlib.sha256(package).hexdigest()
        )


def test_loader_rejects_task9_manifest_provenance_drift():
    def mutate(_members, manifest):
        manifest["audit_code_commit"] = "0" * 40

    package = make_synthetic_task9_evidence_zip(mutate=mutate)

    with pytest.raises(ValueError, match="audit_code_commit"):
        _load_task9_evidence_bytes(
            package, expected_sha256=hashlib.sha256(package).hexdigest()
        )


def test_loader_rejects_forged_task9_input_source_commit():
    def mutate(_members, manifest):
        manifest["input_locked_leg_source_commit"] = "0" * 40

    package = make_synthetic_task9_evidence_zip(mutate=mutate)

    with pytest.raises(ValueError, match="input_locked_leg_source_commit"):
        _load_task9_evidence_bytes(
            package, expected_sha256=hashlib.sha256(package).hexdigest()
        )
