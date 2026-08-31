"""Strict reader for the frozen Task 9 combined-audit evidence package."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import MappingProxyType
from typing import Any

from research.combined_audit_contract import (
    DETERMINISTIC_RELATIONS,
    FEATURE_ROLE_COLUMNS,
    FEATURE_SPECS,
    MAIN_FEATURES,
    RAW_DIRECTION_SENSITIVE,
    TIMEFRAMES,
    DIRECTIONS,
)
from research.combined_audit_io import (
    COMBINED_MANIFEST_FILENAME,
    CROSS_TF_FIELDS,
    CROSS_TF_FILENAME,
    DETERMINISTIC_FIELDS,
    DETERMINISTIC_FILENAME,
    MAIN_FIELDS,
    PARTIAL_FIELDS,
    SUPPLEMENTARY_FIELDS,
    FEATURE_ROLE_FILENAME,
)
from research.task10_interpretation_contract import (
    MAIN_PAIR_KEYS,
    PARTIAL_PAIR_KEYS,
    SUPPLEMENTARY_PAIR_KEYS,
    TASK9_ACTIVITY_INPUT_SHA256,
    TASK9_AUDIT_CODE_COMMIT,
    TASK9_EVIDENCE_SHA256,
)


_FINITE_DECIMAL_RE = re.compile(
    r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z"
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")

_EXPECTED_MEMBERS = frozenset(
    {
        FEATURE_ROLE_FILENAME,
        DETERMINISTIC_FILENAME,
        CROSS_TF_FILENAME,
        COMBINED_MANIFEST_FILENAME,
        *(f"MAIN_SPEARMAN_{tf}.csv" for tf in TIMEFRAMES),
        *(f"PARTIAL_SPEARMAN_{tf}.csv" for tf in TIMEFRAMES),
        *(f"SUPPLEMENTARY_{tf}_{direction}.csv" for tf in TIMEFRAMES for direction in DIRECTIONS),
    }
)

_ROLE_REQUIRED_KEYS = frozenset(
    {"feature", "formula", "analysis_role", "direction_semantics"}
)
assert _ROLE_REQUIRED_KEYS <= set(FEATURE_ROLE_COLUMNS)
_TASK9_LOCKED_LEG_SOURCE_COMMIT = "b43ed7a6d1d8538d8860934abbb24b0c9561a317"


@dataclass(frozen=True, slots=True)
class Task9EvidenceBundle:
    """Validated, immutable Task 9 source artifacts keyed by their source scope."""

    feature_roles: tuple[Mapping[str, object], ...]
    deterministic_rows: tuple[Mapping[str, object], ...]
    main_raw_by_tf: Mapping[str, tuple[Mapping[str, object], ...]]
    partial_by_tf: Mapping[str, tuple[Mapping[str, object], ...]]
    supplementary_by_tf_direction: Mapping[
        tuple[str, str], tuple[Mapping[str, object], ...]
    ]
    cross_tf: tuple[Mapping[str, object], ...]
    manifest: Mapping[str, object]
    evidence_zip_sha256: str

    @property
    def feature_role_rows(self) -> tuple[Mapping[str, object], ...]:
        return self.feature_roles

    @property
    def deterministic_identity_rows(self) -> tuple[Mapping[str, object], ...]:
        return self.deterministic_rows

    @property
    def main_by_tf(self) -> Mapping[str, tuple[Mapping[str, object], ...]]:
        return self.main_raw_by_tf

    @property
    def cross_tf_rows(self) -> tuple[Mapping[str, object], ...]:
        return self.cross_tf


class _DuplicateJSONKey(ValueError):
    pass


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJSONKey(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _member_counts(archive: zipfile.ZipFile) -> dict[str, int]:
    counts: dict[str, int] = {}
    for info in archive.infolist():
        name = info.filename
        if (
            not name
            or "\\" in name
            or name.startswith("/")
            or name.endswith("/")
            or any(part in {"", ".", ".."} for part in name.split("/"))
        ):
            raise ValueError(f"Task 9 Evidence contains unsafe ZIP member name {name!r}")
        counts[name] = counts.get(name, 0) + 1
    duplicates = sorted(name for name, count in counts.items() if count > 1)
    if duplicates:
        raise ValueError(f"Task 9 Evidence contains duplicate ZIP members: {duplicates}")
    return counts


def _read_members(package_bytes: bytes) -> dict[str, bytes]:
    try:
        archive_context = zipfile.ZipFile(io.BytesIO(package_bytes))
    except zipfile.BadZipFile as exc:
        raise ValueError(f"Task 9 Evidence is not a valid ZIP: {exc}") from exc
    with archive_context as archive:
        counts = _member_counts(archive)
        names = set(counts)
        if names != _EXPECTED_MEMBERS:
            missing = sorted(_EXPECTED_MEMBERS - names)
            unexpected = sorted(names - _EXPECTED_MEMBERS)
            raise ValueError(
                "Task 9 Evidence ZIP members do not match the locked set: "
                f"missing={missing}, unexpected={unexpected}"
            )
        return {name: archive.read(name) for name in _EXPECTED_MEMBERS}


def _decode_csv(name: str, data: bytes, expected_fields: Sequence[str]) -> list[dict[str, str]]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{name} must be UTF-8: {exc}") from exc
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""))
        header = tuple(reader.fieldnames or ())
        duplicate_columns = sorted(
            column for column, count in Counter(header).items() if count > 1
        )
        if duplicate_columns:
            raise ValueError(f"{name} contains duplicate CSV columns: {duplicate_columns}")
        if header != tuple(expected_fields):
            raise ValueError(
                f"{name} CSV schema does not match locked source schema: "
                f"expected {tuple(expected_fields)!r}, got {header!r}"
            )
        rows = list(reader)
    except csv.Error as exc:
        raise ValueError(f"{name} contains malformed CSV: {exc}") from exc
    for number, row in enumerate(rows, start=1):
        if None in row:
            raise ValueError(f"{name}: row {number} has more cells than locked schema")
        if any(value is None for value in row.values()):
            raise ValueError(f"{name}: row {number} has fewer cells than locked schema")
    return rows


def _decode_manifest(data: bytes) -> dict[str, Any]:
    try:
        manifest = json.loads(
            data.decode("utf-8"), object_pairs_hook=_reject_duplicate_json_keys
        )
    except _DuplicateJSONKey as exc:
        raise ValueError(f"{COMBINED_MANIFEST_FILENAME}: {exc}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"{COMBINED_MANIFEST_FILENAME} must contain valid UTF-8 JSON: {exc}"
        ) from exc
    if not isinstance(manifest, dict):
        raise ValueError(f"{COMBINED_MANIFEST_FILENAME} must be a JSON object")
    return manifest


def _number(name: str, row_number: int, column: str, raw: object, *, integer: bool = False) -> int | float | None:
    if not isinstance(raw, str):
        raise ValueError(f"{name}: row {row_number}, column {column!r} is not text")
    value = raw.strip()
    if not value:
        return None
    try:
        decimal = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{name}: row {row_number}, column {column!r} has malformed numeric value {raw!r}") from exc
    if not decimal.is_finite() or _FINITE_DECIMAL_RE.fullmatch(value) is None:
        raise ValueError(f"{name}: row {row_number}, column {column!r} has non-finite or malformed numeric value {raw!r}")
    if integer:
        if decimal != decimal.to_integral_value():
            raise ValueError(f"{name}: row {row_number}, column {column!r} must be integral")
        return int(decimal)
    result = float(decimal)
    if not math.isfinite(result):
        raise ValueError(f"{name}: row {row_number}, column {column!r} has non-finite float conversion")
    return result


def _require_nonblank(name: str, row_number: int, column: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name}: row {row_number}, column {column!r} must be nonblank text")
    return value


def _parse_stat_rows(name: str, rows: Sequence[Mapping[str, str]], fields: Sequence[str]) -> tuple[Mapping[str, object], ...]:
    parsed: list[Mapping[str, object]] = []
    integer_fields = {field for field in fields if field.startswith("n_") or field in {"total_rows", "verified_rows", "failed_rows", "sign_agreement_count"}}
    for number, raw in enumerate(rows, start=1):
        row: dict[str, object] = {}
        for field in fields:
            value = raw[field]
            if field in integer_fields:
                parsed_value = _number(name, number, field, value, integer=True)
                if parsed_value is not None and parsed_value < 0:
                    raise ValueError(f"{name}: row {number}, column {field!r} must be nonnegative")
                row[field] = parsed_value
            elif (
                field.startswith("rho")
                or field.startswith("controlled_rho_")
                or field == "delta_rho"
            ):
                parsed_value = _number(name, number, field, value)
                if parsed_value is not None and not -1 <= parsed_value <= 1:
                    raise ValueError(f"{name}: row {number}, column {field!r} must be in [-1, 1]")
                row[field] = parsed_value
            else:
                row[field] = value
        parsed.append(MappingProxyType(row))
    return tuple(parsed)


def _validate_feature_roles(rows: Sequence[Mapping[str, str]]) -> tuple[Mapping[str, object], ...]:
    if len(rows) != len(FEATURE_SPECS):
        raise ValueError(f"{FEATURE_ROLE_FILENAME} must contain exactly {len(FEATURE_SPECS)} rows")
    expected = {feature: spec for feature, spec in FEATURE_SPECS.items()}
    observed = [row["feature"] for row in rows]
    if len(set(observed)) != len(observed) or set(observed) != set(expected):
        raise ValueError(f"{FEATURE_ROLE_FILENAME} feature set does not match the locked Task 9 contract")
    parsed: list[Mapping[str, object]] = []
    for number, raw in enumerate(rows, start=1):
        feature = _require_nonblank(FEATURE_ROLE_FILENAME, number, "feature", raw["feature"])
        spec = expected[feature]
        row: dict[str, object] = {}
        for field in FEATURE_ROLE_COLUMNS:
            value = raw[field]
            if field in {"pairwise_eligible", "controlled_eligible", "stratified_audit_eligible"}:
                if value not in {"True", "False"}:
                    raise ValueError(f"{FEATURE_ROLE_FILENAME}: row {number}, column {field!r} must be True or False")
                row[field] = value == "True"
            else:
                _require_nonblank(FEATURE_ROLE_FILENAME, number, field, value)
                row[field] = value
        if tuple(row[field] for field in FEATURE_ROLE_COLUMNS) != tuple(getattr(spec, field) for field in FEATURE_ROLE_COLUMNS):
            raise ValueError(f"{FEATURE_ROLE_FILENAME}: row {number} does not match locked Task 9 feature metadata")
        parsed.append(MappingProxyType(row))
    return tuple(parsed)


def _pair_set(name: str, rows: Sequence[Mapping[str, object]], expected_pairs: Sequence[tuple[str, str]]) -> None:
    pairs = [(row["feature_x"], row["feature_y"]) for row in rows]
    if len(pairs) != len(expected_pairs) or len(set(pairs)) != len(pairs) or set(pairs) != set(expected_pairs):
        raise ValueError(f"{name} pair set does not match the locked Task 9 contract")
    if any(set(pair) & set(RAW_DIRECTION_SENSITIVE) for pair in pairs) and len(expected_pairs) == len(MAIN_PAIR_KEYS):
        raise ValueError(f"{name} must not contain raw-direction-sensitive features")


def _validate_deterministic(rows: Sequence[Mapping[str, str]]) -> tuple[Mapping[str, object], ...]:
    if len(rows) != len(TIMEFRAMES) * len(DETERMINISTIC_RELATIONS):
        raise ValueError(f"{DETERMINISTIC_FILENAME} must contain exactly 44 rows")
    parsed = _parse_stat_rows(DETERMINISTIC_FILENAME, rows, DETERMINISTIC_FIELDS)
    observed = {(row["timeframe"], row["relation_id"]) for row in parsed}
    expected = {(tf, relation) for tf in TIMEFRAMES for relation in DETERMINISTIC_RELATIONS}
    if observed != expected or len(observed) != len(parsed):
        raise ValueError(f"{DETERMINISTIC_FILENAME} relation/timeframe set does not match locked Task 9 contract")
    for number, row in enumerate(parsed, start=1):
        if row["relation_type"] != "DETERMINISTIC":
            raise ValueError(f"{DETERMINISTIC_FILENAME}: row {number} must be DETERMINISTIC")
        if row["verified_rows"] + row["failed_rows"] != row["total_rows"] or row["failed_rows"] != 0:
            raise ValueError(f"{DETERMINISTIC_FILENAME}: row {number} has invalid locked identity coverage")
    return parsed


def _validate_manifest(manifest: Mapping[str, object]) -> None:
    required = {
        "analysis_feature_count", "audit_code_commit", "audit_version", "broker_company",
        "broker_server", "control_variable", "deterministic_float_abs_tol",
        "deterministic_float_rel_tol", "input_leg_csv_filenames_by_tf",
        "input_lock_status", "input_locked_leg_source_commit",
        "input_snapshot_filenames_by_tf", "input_zip_sha256",
        "numeric_finiteness_gate_passed_by_tf", "raw_cross_tf_pooling",
        "report_filenames", "required_schema_gate_passed_by_tf",
        "snapshot_hash_gate_passed_by_tf", "snapshot_sha256_by_tf", "status_gate_passed",
        "symbols_by_tf", "timeframes",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise ValueError(f"{COMBINED_MANIFEST_FILENAME} missing required provenance fields: {missing}")
    if manifest["audit_code_commit"] != TASK9_AUDIT_CODE_COMMIT:
        raise ValueError(f"{COMBINED_MANIFEST_FILENAME} audit_code_commit does not match locked Task 9 provenance")
    if manifest["input_zip_sha256"] != TASK9_ACTIVITY_INPUT_SHA256:
        raise ValueError(f"{COMBINED_MANIFEST_FILENAME} input_zip_sha256 does not match locked Task 9 provenance")
    if manifest["analysis_feature_count"] != len(MAIN_FEATURES):
        raise ValueError(f"{COMBINED_MANIFEST_FILENAME} analysis_feature_count must be {len(MAIN_FEATURES)}")
    if manifest["timeframes"] != list(TIMEFRAMES) or manifest["input_lock_status"] != "FINAL LOCK / PASS":
        raise ValueError(f"{COMBINED_MANIFEST_FILENAME} does not preserve locked Task 9 timeframe/status provenance")
    if manifest["status_gate_passed"] is not True:
        raise ValueError(f"{COMBINED_MANIFEST_FILENAME} status_gate_passed must be true")
    if manifest["audit_version"] != "1.0" or manifest["control_variable"] != "active_bar_count":
        raise ValueError(f"{COMBINED_MANIFEST_FILENAME} audit version/control provenance is invalid")
    if manifest["deterministic_float_abs_tol"] != 1e-12 or manifest["deterministic_float_rel_tol"] != 1e-12:
        raise ValueError(f"{COMBINED_MANIFEST_FILENAME} deterministic tolerance provenance is invalid")
    if manifest["raw_cross_tf_pooling"] is not False:
        raise ValueError(f"{COMBINED_MANIFEST_FILENAME} must record raw_cross_tf_pooling as false")
    if not isinstance(manifest["broker_company"], str) or not manifest["broker_company"].strip() or not isinstance(manifest["broker_server"], str) or not manifest["broker_server"].strip():
        raise ValueError(f"{COMBINED_MANIFEST_FILENAME} contains blank source provenance")
    if manifest["input_locked_leg_source_commit"] != _TASK9_LOCKED_LEG_SOURCE_COMMIT:
        raise ValueError(
            f"{COMBINED_MANIFEST_FILENAME} input_locked_leg_source_commit "
            "does not match locked Task 9 provenance"
        )
    if manifest["report_filenames"] != sorted(_EXPECTED_MEMBERS):
        raise ValueError(f"{COMBINED_MANIFEST_FILENAME} report_filenames does not match locked Task 9 members")
    for field in ("input_leg_csv_filenames_by_tf", "input_snapshot_filenames_by_tf", "snapshot_sha256_by_tf", "symbols_by_tf"):
        value = manifest[field]
        if not isinstance(value, dict) or set(value) != set(TIMEFRAMES):
            raise ValueError(f"{COMBINED_MANIFEST_FILENAME} {field} must cover every locked timeframe")
    snapshots = manifest["snapshot_sha256_by_tf"]
    if any(not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None for value in snapshots.values()):
        raise ValueError(f"{COMBINED_MANIFEST_FILENAME} snapshot_sha256_by_tf must contain lowercase SHA-256 values")
    for field in ("required_schema_gate_passed_by_tf", "numeric_finiteness_gate_passed_by_tf", "snapshot_hash_gate_passed_by_tf"):
        gates = manifest[field]
        if not isinstance(gates, dict) or set(gates) != set(TIMEFRAMES) or any(value is not True for value in gates.values()):
            raise ValueError(f"{COMBINED_MANIFEST_FILENAME} {field} must record passed gates for every locked timeframe")


def _load_task9_evidence_bytes(package_bytes: bytes, *, expected_sha256: str) -> Task9EvidenceBundle:
    """Private synthetic-test seam; production calls the strict path wrapper below."""

    actual_sha = hashlib.sha256(package_bytes).hexdigest()
    if actual_sha != expected_sha256:
        raise ValueError(f"Task 9 Evidence SHA-256 mismatch: expected {expected_sha256}, got {actual_sha}")
    members = _read_members(package_bytes)
    manifest = _decode_manifest(members[COMBINED_MANIFEST_FILENAME])
    _validate_manifest(manifest)

    roles = _validate_feature_roles(_decode_csv(FEATURE_ROLE_FILENAME, members[FEATURE_ROLE_FILENAME], FEATURE_ROLE_COLUMNS))
    deterministic = _validate_deterministic(_decode_csv(DETERMINISTIC_FILENAME, members[DETERMINISTIC_FILENAME], DETERMINISTIC_FIELDS))
    main_by_tf: dict[str, tuple[Mapping[str, object], ...]] = {}
    partial_by_tf: dict[str, tuple[Mapping[str, object], ...]] = {}
    supplementary: dict[tuple[str, str], tuple[Mapping[str, object], ...]] = {}
    for tf in TIMEFRAMES:
        main_name = f"MAIN_SPEARMAN_{tf}.csv"
        main = _parse_stat_rows(main_name, _decode_csv(main_name, members[main_name], MAIN_FIELDS), MAIN_FIELDS)
        _pair_set(main_name, main, MAIN_PAIR_KEYS)
        main_by_tf[tf] = main
        partial_name = f"PARTIAL_SPEARMAN_{tf}.csv"
        partial = _parse_stat_rows(partial_name, _decode_csv(partial_name, members[partial_name], PARTIAL_FIELDS), PARTIAL_FIELDS)
        _pair_set(partial_name, partial, PARTIAL_PAIR_KEYS)
        partial_by_tf[tf] = partial
        for direction in DIRECTIONS:
            name = f"SUPPLEMENTARY_{tf}_{direction}.csv"
            rows = _parse_stat_rows(name, _decode_csv(name, members[name], SUPPLEMENTARY_FIELDS), SUPPLEMENTARY_FIELDS)
            if any(row["evidence_scope"] != "SUPPLEMENTARY_ONLY" for row in rows):
                raise ValueError(f"{name} must retain SUPPLEMENTARY_ONLY evidence scope")
            _pair_set(name, rows, SUPPLEMENTARY_PAIR_KEYS)
            supplementary[(tf, direction)] = rows
    cross = _parse_stat_rows(CROSS_TF_FILENAME, _decode_csv(CROSS_TF_FILENAME, members[CROSS_TF_FILENAME], CROSS_TF_FIELDS), CROSS_TF_FIELDS)
    _pair_set(CROSS_TF_FILENAME, cross, MAIN_PAIR_KEYS)
    for number, row in enumerate(cross, start=1):
        if row["controlled_eligible"] not in {"True", "False"} or row["sign_agreement_tie"] not in {"True", "False", ""}:
            raise ValueError(f"{CROSS_TF_FILENAME}: row {number} has invalid boolean source fields")
    return Task9EvidenceBundle(
        feature_roles=roles,
        deterministic_rows=deterministic,
        main_raw_by_tf=MappingProxyType(main_by_tf),
        partial_by_tf=MappingProxyType(partial_by_tf),
        supplementary_by_tf_direction=MappingProxyType(supplementary),
        cross_tf=cross,
        manifest=_freeze(manifest),
        evidence_zip_sha256=actual_sha,
    )


def load_task9_evidence_package(path: Path) -> Task9EvidenceBundle:
    """Load only the canonical, final-locked Task 9 Evidence ZIP."""

    package_bytes = Path(path).read_bytes()
    return _load_task9_evidence_bytes(package_bytes, expected_sha256=TASK9_EVIDENCE_SHA256)


__all__ = ["Task9EvidenceBundle", "load_task9_evidence_package"]
