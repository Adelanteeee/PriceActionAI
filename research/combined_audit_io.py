"""Strict package I/O gates for the Final-Locked Combined Activity audit."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import subprocess
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import MappingProxyType
from typing import Any

from research.combined_audit_contract import (
    DETERMINISTIC_FLOAT_ABS_TOL,
    DETERMINISTIC_FLOAT_REL_TOL,
    DIRECTIONS,
    FEATURE_ROLE_COLUMNS,
    MAIN_FEATURES,
    RAW_DIRECTION_SENSITIVE,
    TIMEFRAMES,
)


FINAL_LOCK_STATUS = "FINAL LOCK / PASS"
MANIFEST_MEMBER = "manifest.json"

FEATURE_ROLE_FILENAME = "FEATURE_ROLE_MATRIX.csv"
DETERMINISTIC_FILENAME = "DETERMINISTIC_IDENTITY_REPORT.csv"
CROSS_TF_FILENAME = "CROSS_TF_RELATIONSHIP_REPORT.csv"
COMBINED_MANIFEST_FILENAME = "COMBINED_AUDIT_MANIFEST.json"

DETERMINISTIC_FIELDS = (
    "timeframe",
    "relation_id",
    "relation_type",
    "formula",
    "participating_features",
    "conditions",
    "tolerance_policy",
    "total_rows",
    "verified_rows",
    "failed_rows",
)
MAIN_FIELDS = (
    "feature_x",
    "feature_y",
    "n_total",
    "n_valid_pairwise",
    "n_missing_x",
    "n_missing_y",
    "rho_raw",
    "status",
)
PARTIAL_FIELDS = (
    "feature_x",
    "feature_y",
    "rho_raw_for_delta",
    "rho_duration_controlled",
    "delta_rho",
    "n_valid_triple",
    "status",
)
SUPPLEMENTARY_FIELDS = (
    "feature_x",
    "feature_y",
    "n_total",
    "n_valid_pairwise",
    "n_missing_x",
    "n_missing_y",
    "rho_raw",
    "raw_status",
    "rho_raw_for_delta",
    "rho_duration_controlled",
    "delta_rho",
    "n_valid_triple",
    "controlled_status",
    "evidence_scope",
)
CROSS_TF_FIELDS = (
    "feature_x",
    "feature_y",
    "controlled_eligible",
    *(f"rho_{tf}" for tf in TIMEFRAMES),
    *(f"controlled_rho_{tf}" for tf in TIMEFRAMES),
    *(f"n_valid_{tf}" for tf in TIMEFRAMES),
    "n_positive_tf",
    "n_negative_tf",
    "n_zero_tf",
    "n_undefined_tf",
    "sign_agreement_count",
    "sign_agreement_tie",
    "sign_agreement_modal_signs",
    "rho_min",
    "rho_max",
    "rho_range",
)

IDENTITY_COLUMNS = (
    "signed_close_displacement",
    "aligned_close_steps",
    "opposing_close_steps",
    "flat_close_steps",
    "gap_path_contribution",
    "gross_body_magnitude",
    "gross_candle_range",
    "gross_forward_shadow",
    "gross_backward_shadow",
    "gross_shadow_magnitude",
    "gross_overlap_magnitude",
    "gross_overlap_capacity",
    "directional_close_ols_slope",
    "gross_tick_activity",
)

TRACEABILITY_COLUMNS = (
    "leg_no",
    "direction",
    "start_index",
    "end_index",
    "start_time",
    "end_time",
    "start_kind",
    "end_kind",
    "start_price",
    "end_price",
    "owned_candle_count",
)

REQUIRED_LEG_COLUMN_ORDER = (
    MAIN_FEATURES + RAW_DIRECTION_SENSITIVE + IDENTITY_COLUMNS + TRACEABILITY_COLUMNS
)
REQUIRED_LEG_COLUMNS = frozenset(REQUIRED_LEG_COLUMN_ORDER)

INTEGER_COLUMNS = frozenset(
    {
        "leg_no",
        "start_index",
        "end_index",
        "active_bar_count",
        "owned_candle_count",
        "aligned_close_steps",
        "opposing_close_steps",
        "flat_close_steps",
        "gross_tick_activity",
    }
)
STRING_COLUMNS = frozenset(
    {"direction", "start_time", "end_time", "start_kind", "end_kind"}
)
FLOAT_COLUMNS = REQUIRED_LEG_COLUMNS - INTEGER_COLUMNS - STRING_COLUMNS

_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_FINITE_DECIMAL_RE = re.compile(
    r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z"
)


@dataclass(frozen=True, slots=True)
class AuditInputBundle:
    """Fully validated, deeply immutable input package contents."""

    manifest: Mapping[str, object]
    rows_by_tf: Mapping[str, tuple[Mapping[str, object], ...]]
    input_zip_sha256: str
    snapshot_sha256_by_tf: Mapping[str, str]


class _DuplicateJSONKey(ValueError):
    pass


def sha256_bytes(data: bytes) -> str:
    """Return the lowercase SHA-256 digest for ``data``."""

    return hashlib.sha256(data).hexdigest()


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJSONKey(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _deep_freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _deep_freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_deep_freeze(item) for item in value)
    return value


def _require_mapping(value: object, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{location} must be a JSON object")
    return value


def _require_nonblank_string(mapping: Mapping[str, Any], key: str, location: str) -> str:
    if key not in mapping:
        raise ValueError(f"{location}: manifest missing required field {key!r}")
    value = mapping[key]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{location}: manifest field {key!r} must be a nonblank string")
    return value


def _validate_member_name(tf: str, role: str, name: str) -> None:
    raw_parts = name.split("/")
    unsafe = (
        not name
        or "\\" in name
        or name.startswith("/")
        or name.endswith("/")
        or any(part in {"", ".", ".."} for part in raw_parts)
    )
    if unsafe:
        raise ValueError(f"{tf}: unsafe manifest {role} ZIP member name {name!r}")


def _member_counts(archive: zipfile.ZipFile) -> dict[str, int]:
    counts: dict[str, int] = {}
    for info in archive.infolist():
        counts[info.filename] = counts.get(info.filename, 0) + 1
    return counts


def _read_unique_member(
    archive: zipfile.ZipFile,
    counts: Mapping[str, int],
    *,
    tf: str,
    role: str,
    name: str,
) -> bytes:
    count = counts.get(name, 0)
    if count == 0:
        raise ValueError(f"{tf}: missing ZIP member for manifest {role}: {name!r}")
    if count > 1:
        raise ValueError(f"{tf}: duplicate ZIP member for manifest {role}: {name!r}")
    return archive.read(name)


def _load_manifest(archive: zipfile.ZipFile, counts: Mapping[str, int]) -> dict[str, Any]:
    count = counts.get(MANIFEST_MEMBER, 0)
    if count == 0:
        raise ValueError(f"package is missing required {MANIFEST_MEMBER} manifest")
    if count > 1:
        raise ValueError(f"package contains duplicate {MANIFEST_MEMBER} members")
    raw = archive.read(MANIFEST_MEMBER)
    try:
        manifest = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_json_keys,
        )
    except _DuplicateJSONKey as exc:
        raise ValueError(f"{MANIFEST_MEMBER}: {exc}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{MANIFEST_MEMBER} must contain valid JSON: {exc}") from exc
    return _require_mapping(manifest, MANIFEST_MEMBER)


def _validate_manifest(manifest: dict[str, Any]) -> dict[str, dict[str, str]]:
    status = _require_nonblank_string(manifest, "status", "manifest")
    if status != FINAL_LOCK_STATUS:
        raise ValueError(
            f"manifest status must be {FINAL_LOCK_STATUS!r}, got {status!r}"
        )

    _require_nonblank_string(manifest, "current_commit", "manifest")
    _require_nonblank_string(manifest, "broker_company", "manifest")
    _require_nonblank_string(manifest, "broker_server", "manifest")

    if "timeframes" not in manifest:
        raise ValueError("manifest missing required field 'timeframes'")
    timeframes = _require_mapping(manifest["timeframes"], "manifest timeframes")
    missing = [tf for tf in TIMEFRAMES if tf not in timeframes]
    if missing:
        raise ValueError(f"manifest missing timeframe metadata: {missing}")
    unexpected = sorted(set(timeframes) - set(TIMEFRAMES))
    if unexpected:
        raise ValueError(f"manifest has unexpected timeframe metadata: {unexpected}")

    validated: dict[str, dict[str, str]] = {}
    csv_names: set[str] = set()
    snapshot_names: set[str] = set()
    for tf in TIMEFRAMES:
        metadata = _require_mapping(timeframes[tf], f"manifest timeframes[{tf!r}]")
        symbol = _require_nonblank_string(metadata, "symbol", f"manifest {tf}")
        metadata_tf = _require_nonblank_string(metadata, "timeframe", f"manifest {tf}")
        csv_name = _require_nonblank_string(metadata, "csv", f"manifest {tf}")
        snapshot_name = _require_nonblank_string(
            metadata, "snapshot_file", f"manifest {tf}"
        )
        snapshot_sha = _require_nonblank_string(
            metadata, "snapshot_sha256", f"manifest {tf}"
        )
        if metadata_tf != tf:
            raise ValueError(
                f"{tf}: manifest timeframe must be {tf!r}, got {metadata_tf!r}"
            )
        if _SHA256_RE.fullmatch(snapshot_sha) is None:
            raise ValueError(
                f"{tf}: manifest snapshot_sha256 must be a 64-character lowercase SHA-256"
            )
        _validate_member_name(tf, "csv", csv_name)
        _validate_member_name(tf, "snapshot_file", snapshot_name)
        if csv_name in csv_names:
            raise ValueError(f"{tf}: duplicate manifest csv metadata value {csv_name!r}")
        if snapshot_name in snapshot_names:
            raise ValueError(
                f"{tf}: duplicate manifest snapshot_file metadata value {snapshot_name!r}"
            )
        csv_names.add(csv_name)
        snapshot_names.add(snapshot_name)
        validated[tf] = {
            "symbol": symbol,
            "timeframe": metadata_tf,
            "csv": csv_name,
            "snapshot_file": snapshot_name,
            "snapshot_sha256": snapshot_sha,
        }
    return validated


def _decode_csv(tf: str, csv_name: str, data: bytes) -> tuple[list[str], list[dict]]:
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{tf}: Leg CSV {csv_name!r} must be UTF-8: {exc}") from exc
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""))
        header = list(reader.fieldnames or [])
        duplicates = sorted(
            name for name, count in Counter(header).items() if count > 1
        )
        if duplicates:
            raise ValueError(f"{tf}: duplicate Leg CSV columns: {duplicates}")
        rows = list(reader)
    except csv.Error as exc:
        raise ValueError(f"{tf}: malformed Leg CSV {csv_name!r}: {exc}") from exc
    return header, rows


def _numeric_error(
    tf: str,
    data_row: int,
    column: str,
    raw_value: object,
    detail: str,
) -> ValueError:
    return ValueError(
        f"{tf}: data row {data_row}, column {column!r}, "
        f"raw value {raw_value!r}: {detail}"
    )


def _parse_numeric(tf: str, data_row: int, column: str, raw_value: object) -> object:
    if not isinstance(raw_value, str):
        raise _numeric_error(tf, data_row, column, raw_value, "missing numeric cell")
    text = raw_value.strip()
    if not text:
        return None
    try:
        decimal_value = Decimal(text)
    except InvalidOperation as exc:
        raise _numeric_error(
            tf, data_row, column, raw_value, "malformed numeric text"
        ) from exc
    if not decimal_value.is_finite():
        raise _numeric_error(
            tf, data_row, column, raw_value, "non-finite numeric value"
        )
    if _FINITE_DECIMAL_RE.fullmatch(text) is None:
        raise _numeric_error(tf, data_row, column, raw_value, "malformed numeric text")

    if column in INTEGER_COLUMNS:
        if decimal_value != decimal_value.to_integral_value():
            raise _numeric_error(
                tf, data_row, column, raw_value, "integer field is fractional"
            )
        return int(decimal_value)

    value = float(decimal_value)
    if not math.isfinite(value):
        raise _numeric_error(
            tf, data_row, column, raw_value, "non-finite float conversion"
        )
    return value


def _parse_rows(tf: str, raw_rows: Sequence[Mapping[str, object]]) -> tuple[Mapping, ...]:
    parsed_rows = []
    for data_row, raw_row in enumerate(raw_rows, start=1):
        parsed: dict[str, object] = {}
        for column in REQUIRED_LEG_COLUMN_ORDER:
            raw_value = raw_row.get(column)
            if column in STRING_COLUMNS:
                if not isinstance(raw_value, str):
                    raise ValueError(
                        f"{tf}: data row {data_row}, column {column!r}, "
                        f"raw value {raw_value!r}: missing string cell"
                    )
                if column == "direction" and raw_value not in DIRECTIONS:
                    raise ValueError(
                        f"{tf}: data row {data_row}, column {column!r}, "
                        f"raw value {raw_value!r}: expected exact "
                        "'BULLISH' or 'BEARISH'"
                    )
                parsed[column] = raw_value
            else:
                parsed[column] = _parse_numeric(
                    tf, data_row, column, raw_value
                )
        parsed_rows.append(MappingProxyType(parsed))
    return tuple(parsed_rows)


def load_locked_activity_package(path: Path) -> AuditInputBundle:
    """Load a locked Activity ZIP only after every package gate succeeds."""

    package_path = Path(path)
    package_bytes = package_path.read_bytes()
    input_zip_sha256 = sha256_bytes(package_bytes)

    try:
        archive_context = zipfile.ZipFile(io.BytesIO(package_bytes))
    except zipfile.BadZipFile as exc:
        raise ValueError(f"input package is not a valid ZIP: {exc}") from exc

    with archive_context as archive:
        counts = _member_counts(archive)
        manifest = _load_manifest(archive, counts)
        metadata_by_tf = _validate_manifest(manifest)

        csv_bytes_by_tf: dict[str, bytes] = {}
        snapshot_sha256_by_tf: dict[str, str] = {}
        for tf in TIMEFRAMES:
            metadata = metadata_by_tf[tf]
            csv_bytes_by_tf[tf] = _read_unique_member(
                archive,
                counts,
                tf=tf,
                role="csv",
                name=metadata["csv"],
            )
            snapshot_bytes = _read_unique_member(
                archive,
                counts,
                tf=tf,
                role="snapshot_file",
                name=metadata["snapshot_file"],
            )
            actual_snapshot_sha = sha256_bytes(snapshot_bytes)
            if actual_snapshot_sha != metadata["snapshot_sha256"]:
                raise ValueError(
                    f"{tf}: snapshot SHA-256 mismatch for "
                    f"{metadata['snapshot_file']!r}: expected "
                    f"{metadata['snapshot_sha256']}, got {actual_snapshot_sha}"
                )
            snapshot_sha256_by_tf[tf] = actual_snapshot_sha

    decoded_by_tf: dict[str, tuple[list[str], list[dict]]] = {}
    for tf in TIMEFRAMES:
        metadata = metadata_by_tf[tf]
        decoded_by_tf[tf] = _decode_csv(tf, metadata["csv"], csv_bytes_by_tf[tf])

    # Package-wide schema validation deliberately precedes numeric parsing, so
    # no report consumer can observe partially parsed rows.
    for tf in TIMEFRAMES:
        header, _ = decoded_by_tf[tf]
        missing = sorted(REQUIRED_LEG_COLUMNS - set(header))
        if missing:
            raise ValueError(f"{tf}: missing required Leg CSV columns: {missing}")

    rows_by_tf = {
        tf: _parse_rows(tf, decoded_by_tf[tf][1])
        for tf in TIMEFRAMES
    }
    return AuditInputBundle(
        manifest=_deep_freeze(manifest),
        rows_by_tf=MappingProxyType(rows_by_tf),
        input_zip_sha256=input_zip_sha256,
        snapshot_sha256_by_tf=MappingProxyType(snapshot_sha256_by_tf),
    )


def write_csv(
    path: Path,
    rows: Sequence[Mapping[str, object]],
    *,
    fieldnames: Sequence[str],
) -> None:
    """Write UTF-8 CSV with caller-supplied field order and stable newlines."""

    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=tuple(fieldnames),
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(output.getvalue().encode("utf-8"))


def write_json(path: Path, payload: object) -> None:
    """Write sorted UTF-8 JSON while refusing non-finite float extensions."""

    data = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(data)


def _audit_code_commit() -> str:
    """Return the repository HEAD independently of the checked-out branch name."""

    repository = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    commit = result.stdout.strip()
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise RuntimeError(f"git returned an invalid audit code commit: {commit!r}")
    return commit


def _combined_deterministic_rows(
    reports_by_tf: Mapping[str, Sequence[Mapping[str, object]]],
) -> list[dict[str, object]]:
    combined: list[dict[str, object]] = []
    for tf in TIMEFRAMES:
        for row in reports_by_tf[tf]:
            combined.append(
                {
                    "timeframe": tf,
                    "relation_id": row["relation_id"],
                    "relation_type": row["relation_type"],
                    "formula": row["formula"],
                    "participating_features": row["participating_features"],
                    "conditions": (
                        f"condition={row['condition']}; "
                        f"undefined_when={row['undefined_when']}; "
                        f"undefined_result={row['undefined_result']}"
                    ),
                    "tolerance_policy": row["tolerance_policy"],
                    "total_rows": row["total_rows"],
                    "verified_rows": row["verified_rows"],
                    "failed_rows": row["failed_rows"],
                }
            )
    return combined


def _combined_supplementary_rows(
    report: Mapping[str, object],
) -> list[dict[str, object]]:
    partial_by_pair = {
        (row["feature_x"], row["feature_y"]): row
        for row in report["partial"]
    }
    combined: list[dict[str, object]] = []
    for raw in report["raw"]:
        pair = (raw["feature_x"], raw["feature_y"])
        partial = partial_by_pair.get(pair)
        combined.append(
            {
                "feature_x": raw["feature_x"],
                "feature_y": raw["feature_y"],
                "n_total": raw["n_total"],
                "n_valid_pairwise": raw["n_valid_pairwise"],
                "n_missing_x": raw["n_missing_x"],
                "n_missing_y": raw["n_missing_y"],
                "rho_raw": raw["rho_raw"],
                "raw_status": raw["status"],
                "rho_raw_for_delta": (
                    partial["rho_raw_for_delta"] if partial is not None else None
                ),
                "rho_duration_controlled": (
                    partial["rho_duration_controlled"] if partial is not None else None
                ),
                "delta_rho": partial["delta_rho"] if partial is not None else None,
                "n_valid_triple": (
                    partial["n_valid_triple"] if partial is not None else None
                ),
                "controlled_status": partial["status"] if partial is not None else None,
                "evidence_scope": "SUPPLEMENTARY_ONLY",
            }
        )
    return combined


def combined_audit_report_filenames() -> list[str]:
    """Return every logical artifact name in deterministic order."""

    names = {
        FEATURE_ROLE_FILENAME,
        DETERMINISTIC_FILENAME,
        CROSS_TF_FILENAME,
        COMBINED_MANIFEST_FILENAME,
        *(f"MAIN_SPEARMAN_{tf}.csv" for tf in TIMEFRAMES),
        *(f"PARTIAL_SPEARMAN_{tf}.csv" for tf in TIMEFRAMES),
        *(
            f"SUPPLEMENTARY_{tf}_{direction}.csv"
            for tf in TIMEFRAMES
            for direction in DIRECTIONS
        ),
    }
    return sorted(names)


def _combined_audit_manifest(bundle: AuditInputBundle) -> dict[str, object]:
    input_manifest = bundle.manifest
    metadata_by_tf = input_manifest["timeframes"]
    passed_by_tf = {tf: True for tf in TIMEFRAMES}
    return {
        "analysis_feature_count": len(MAIN_FEATURES),
        "audit_code_commit": _audit_code_commit(),
        "audit_version": "1.0",
        "broker_company": input_manifest["broker_company"],
        "broker_server": input_manifest["broker_server"],
        "control_variable": "active_bar_count",
        "deterministic_float_abs_tol": DETERMINISTIC_FLOAT_ABS_TOL,
        "deterministic_float_rel_tol": DETERMINISTIC_FLOAT_REL_TOL,
        "input_leg_csv_filenames_by_tf": {
            tf: metadata_by_tf[tf]["csv"] for tf in TIMEFRAMES
        },
        "input_lock_status": input_manifest["status"],
        "input_locked_leg_source_commit": input_manifest["current_commit"],
        "input_snapshot_filenames_by_tf": {
            tf: metadata_by_tf[tf]["snapshot_file"] for tf in TIMEFRAMES
        },
        "input_zip_sha256": bundle.input_zip_sha256,
        "numeric_finiteness_gate_passed_by_tf": dict(passed_by_tf),
        "raw_cross_tf_pooling": False,
        "report_filenames": combined_audit_report_filenames(),
        "required_schema_gate_passed_by_tf": dict(passed_by_tf),
        "snapshot_hash_gate_passed_by_tf": dict(passed_by_tf),
        "snapshot_sha256_by_tf": {
            tf: bundle.snapshot_sha256_by_tf[tf] for tf in TIMEFRAMES
        },
        "status_gate_passed": True,
        "symbols_by_tf": {
            tf: metadata_by_tf[tf]["symbol"] for tf in TIMEFRAMES
        },
        "timeframes": list(TIMEFRAMES),
    }


def write_combined_audit_outputs(
    output_dir: Path,
    *,
    bundle: AuditInputBundle,
    feature_roles: Sequence[Mapping[str, object]],
    deterministic: Mapping[str, Sequence[Mapping[str, object]]],
    main_reports: Mapping[str, Sequence[Mapping[str, object]]],
    partial_reports: Mapping[str, Sequence[Mapping[str, object]]],
    supplementary: Mapping[tuple[str, str], Mapping[str, object]],
    cross_tf: Sequence[Mapping[str, object]],
) -> None:
    """Write the complete deterministic logical artifact directory."""

    destination = Path(output_dir)
    write_csv(
        destination / FEATURE_ROLE_FILENAME,
        feature_roles,
        fieldnames=FEATURE_ROLE_COLUMNS,
    )
    write_csv(
        destination / DETERMINISTIC_FILENAME,
        _combined_deterministic_rows(deterministic),
        fieldnames=DETERMINISTIC_FIELDS,
    )
    for tf in TIMEFRAMES:
        write_csv(
            destination / f"MAIN_SPEARMAN_{tf}.csv",
            main_reports[tf],
            fieldnames=MAIN_FIELDS,
        )
        write_csv(
            destination / f"PARTIAL_SPEARMAN_{tf}.csv",
            partial_reports[tf],
            fieldnames=PARTIAL_FIELDS,
        )
        for direction in DIRECTIONS:
            write_csv(
                destination / f"SUPPLEMENTARY_{tf}_{direction}.csv",
                _combined_supplementary_rows(supplementary[(tf, direction)]),
                fieldnames=SUPPLEMENTARY_FIELDS,
            )
    write_csv(destination / CROSS_TF_FILENAME, cross_tf, fieldnames=CROSS_TF_FIELDS)
    write_json(
        destination / COMBINED_MANIFEST_FILENAME,
        _combined_audit_manifest(bundle),
    )


def write_output_bundle(path: Path, members: Mapping[str, bytes | str]) -> None:
    """Write a deterministic ZIP from in-memory named report artifacts."""

    prepared: list[tuple[str, bytes]] = []
    for name, value in members.items():
        _validate_member_name("output", "bundle", name)
        if isinstance(value, str):
            data = value.encode("utf-8")
        elif isinstance(value, bytes):
            data = value
        else:
            raise TypeError(f"output bundle member {name!r} must be bytes or str")
        prepared.append((name, data))

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        output_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for name, data in sorted(prepared):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
