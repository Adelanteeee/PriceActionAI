import csv
import hashlib
import io
import json
import math
import zipfile
from pathlib import Path

import pytest

from research.combined_audit_io import (
    load_locked_activity_package,
    write_csv,
    write_json,
    write_output_bundle,
)


TIMEFRAMES = ("M5", "M15", "M30", "H1")

# Kept independent of the production constant so schema tests can catch an
# accidentally incomplete REQUIRED_LEG_COLUMNS definition.
REQUIRED_COLUMNS = (
    "active_bar_count",
    "net_thrust",
    "gross_close_path",
    "net_close_displacement",
    "directional_efficiency",
    "directional_continuity_ratio",
    "close_confirmation_ratio",
    "gap_path_share",
    "body_strength_ratio",
    "shadow_position_imbalance",
    "overlap_ratio",
    "normalized_directional_close_ols_slope",
    "mean_tick_activity",
    "close_ols_slope",
    "gross_upper_shadow",
    "gross_lower_shadow",
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

INTEGER_COLUMNS = {
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

STRING_COLUMNS = {
    "direction",
    "start_time",
    "end_time",
    "start_kind",
    "end_kind",
}


def _csv_bytes(tf, *, drop_columns=(), overrides=(), extra_columns=()):
    fieldnames = [name for name in REQUIRED_COLUMNS if name not in drop_columns]
    fieldnames.extend(extra_columns)
    rows = []
    for data_row in range(1, 4):
        row = {}
        for column in fieldnames:
            if column in INTEGER_COLUMNS:
                row[column] = str(data_row)
            elif column == "direction":
                row[column] = "BULLISH" if data_row % 2 else "BEARISH"
            elif column in {"start_time", "end_time"}:
                row[column] = f"2026-01-0{data_row}T00:00:00Z"
            elif column in {"start_kind", "end_kind"}:
                row[column] = "SWING"
            elif column in extra_columns:
                row[column] = f"extra-{tf}-{data_row}"
            else:
                row[column] = f"{data_row}.25"
        rows.append(row)

    for override_row, column, value in overrides:
        rows[override_row - 1][column] = value

    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def make_synthetic_activity_zip(
    tmp_path,
    *,
    status="FINAL LOCK / PASS",
    drop_columns_by_tf=None,
    cell_override=None,
    csv_names=None,
    mutate_manifest=None,
    missing_members=(),
    extra_members=None,
    duplicate_member=None,
):
    drop_columns_by_tf = drop_columns_by_tf or {}
    csv_names = csv_names or {tf: f"{tf}.csv" for tf in TIMEFRAMES}
    missing_members = set(missing_members)
    extra_members = extra_members or {}

    snapshots = {tf: f"snapshot,{tf}\n1,{tf}\n".encode() for tf in TIMEFRAMES}
    manifest = {
        "status": status,
        "current_commit": "b43ed7a6d1d8538d8860934abbb24b0c9561a317",
        "broker_company": "LiteFinance Global LLC",
        "broker_server": "LiteFinance-MT5-Live",
        # Reversed deliberately: output order must follow the locked contract,
        # not incidental JSON object order.
        "timeframes": {
            tf: {
                "symbol": "XAUUSD_o",
                "timeframe": tf,
                "csv": csv_names[tf],
                "snapshot_file": f"snapshots/{tf}_snapshot.csv",
                "snapshot_sha256": hashlib.sha256(snapshots[tf]).hexdigest(),
            }
            for tf in reversed(TIMEFRAMES)
        },
    }
    if mutate_manifest is not None:
        mutate_manifest(manifest)

    members = {"manifest.json": json.dumps(manifest).encode()}
    for tf in TIMEFRAMES:
        overrides = []
        if cell_override is not None and cell_override[0] == tf:
            _, data_row, column, value = cell_override
            overrides.append((data_row, column, value))
        members[csv_names[tf]] = _csv_bytes(
            tf,
            drop_columns=drop_columns_by_tf.get(tf, ()),
            overrides=overrides,
            extra_columns=("unexpected_metric",),
        )
        members[f"snapshots/{tf}_snapshot.csv"] = snapshots[tf]
    members.update(extra_members)

    package = tmp_path / "synthetic_activity.zip"
    with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in members.items():
            if name not in missing_members:
                archive.writestr(name, data)
        if duplicate_member is not None:
            with pytest.warns(UserWarning, match="Duplicate name"):
                archive.writestr(duplicate_member, members[duplicate_member])
    return package


def test_loader_requires_final_lock_status(tmp_path):
    package = make_synthetic_activity_zip(tmp_path, status="LOCK CANDIDATE")

    with pytest.raises(ValueError, match="FINAL LOCK / PASS"):
        load_locked_activity_package(package)


def test_loader_uses_manifest_csv_names_and_preserves_tf_separation(tmp_path):
    csv_names = {tf: f"locked/legs-{tf}.csv" for tf in TIMEFRAMES}
    package = make_synthetic_activity_zip(
        tmp_path,
        csv_names=csv_names,
        extra_members={"M5.csv": b"this,is,not,the,locked,csv\n"},
    )

    bundle = load_locked_activity_package(package)

    assert tuple(bundle.rows_by_tf) == TIMEFRAMES
    assert bundle.rows_by_tf["M5"] is not bundle.rows_by_tf["M15"]
    assert bundle.rows_by_tf["M5"][0]["leg_no"] == 1
    assert tuple(bundle.rows_by_tf["M5"][0]) == REQUIRED_COLUMNS
    assert "unexpected_metric" not in bundle.rows_by_tf["M5"][0]


def test_loader_rejects_missing_required_columns_in_sorted_order(tmp_path):
    package = make_synthetic_activity_zip(
        tmp_path,
        drop_columns_by_tf={"M15": {"mean_tick_activity", "gross_backward_shadow"}},
    )

    with pytest.raises(ValueError) as exc:
        load_locked_activity_package(package)

    assert str(exc.value) == (
        "M15: missing required Leg CSV columns: "
        "['gross_backward_shadow', 'mean_tick_activity']"
    )


def test_loader_checks_all_schemas_before_parsing_any_numeric_rows(tmp_path):
    package = make_synthetic_activity_zip(
        tmp_path,
        drop_columns_by_tf={"M15": {"mean_tick_activity"}},
        cell_override=("M5", 1, "overlap_ratio", "not-a-number"),
    )

    with pytest.raises(ValueError, match="M15: missing required Leg CSV columns"):
        load_locked_activity_package(package)


@pytest.mark.parametrize(
    "bad_text",
    [
        "NaN",
        "nan",
        "NAN",
        "Inf",
        "+Inf",
        "-Inf",
        "Infinity",
        "+Infinity",
        "-Infinity",
        "infinity",
    ],
)
def test_loader_rejects_non_finite_numeric_text(tmp_path, bad_text):
    package = make_synthetic_activity_zip(
        tmp_path,
        cell_override=("M30", 2, "mean_tick_activity", bad_text),
    )

    with pytest.raises(ValueError) as exc:
        load_locked_activity_package(package)

    message = str(exc.value)
    assert "M30" in message
    assert "data row 2" in message
    assert "mean_tick_activity" in message
    assert repr(bad_text) in message


def test_loader_rejects_malformed_numeric_text_with_cell_location(tmp_path):
    package = make_synthetic_activity_zip(
        tmp_path,
        cell_override=("H1", 3, "overlap_ratio", "not-a-number"),
    )

    with pytest.raises(ValueError) as exc:
        load_locked_activity_package(package)

    message = str(exc.value)
    assert "H1" in message
    assert "data row 3" in message
    assert "overlap_ratio" in message
    assert "'not-a-number'" in message


def test_loader_rejects_fractional_integer_with_cell_location(tmp_path):
    package = make_synthetic_activity_zip(
        tmp_path,
        cell_override=("M5", 2, "active_bar_count", " 1.5 "),
    )

    with pytest.raises(ValueError) as exc:
        load_locked_activity_package(package)

    message = str(exc.value)
    assert "M5" in message
    assert "data row 2" in message
    assert "active_bar_count" in message
    assert "' 1.5 '" in message


def test_loader_accepts_exact_integral_numeric_syntax(tmp_path):
    package = make_synthetic_activity_zip(
        tmp_path,
        cell_override=("M5", 1, "active_bar_count", "2.000e0"),
    )

    bundle = load_locked_activity_package(package)

    assert bundle.rows_by_tf["M5"][0]["active_bar_count"] == 2
    assert isinstance(bundle.rows_by_tf["M5"][0]["active_bar_count"], int)


def test_loader_maps_whitespace_only_numeric_cell_to_none(tmp_path):
    package = make_synthetic_activity_zip(
        tmp_path,
        cell_override=("M5", 1, "overlap_ratio", " \t "),
    )

    bundle = load_locked_activity_package(package)

    assert bundle.rows_by_tf["M5"][0]["overlap_ratio"] is None


def test_loader_records_input_and_snapshot_hashes(tmp_path):
    package = make_synthetic_activity_zip(tmp_path)

    bundle = load_locked_activity_package(package)

    assert bundle.input_zip_sha256 == hashlib.sha256(package.read_bytes()).hexdigest()
    assert tuple(bundle.snapshot_sha256_by_tf) == TIMEFRAMES
    assert bundle.snapshot_sha256_by_tf["M30"] == bundle.manifest["timeframes"]["M30"][
        "snapshot_sha256"
    ]


def test_loader_rejects_snapshot_hash_mismatch(tmp_path):
    def corrupt_hash(manifest):
        manifest["timeframes"]["M30"]["snapshot_sha256"] = "0" * 64

    package = make_synthetic_activity_zip(tmp_path, mutate_manifest=corrupt_hash)

    with pytest.raises(ValueError, match="M30.*snapshot SHA-256 mismatch"):
        load_locked_activity_package(package)


@pytest.mark.parametrize(
    "missing_path",
    [
        ("status",),
        ("current_commit",),
        ("broker_company",),
        ("broker_server",),
        ("timeframes",),
        ("timeframes", "M15", "csv"),
        ("timeframes", "M15", "snapshot_file"),
        ("timeframes", "M15", "snapshot_sha256"),
    ],
)
def test_loader_rejects_missing_manifest_sections(tmp_path, missing_path):
    def remove_path(manifest):
        target = manifest
        for component in missing_path[:-1]:
            target = target[component]
        del target[missing_path[-1]]

    package = make_synthetic_activity_zip(tmp_path, mutate_manifest=remove_path)

    with pytest.raises(ValueError, match="manifest"):
        load_locked_activity_package(package)


def test_loader_rejects_malformed_manifest_json(tmp_path):
    package = tmp_path / "malformed.zip"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("manifest.json", b"{not valid JSON")

    with pytest.raises(ValueError, match="manifest.json.*valid JSON"):
        load_locked_activity_package(package)


def test_loader_rejects_duplicate_manifest_json_keys(tmp_path):
    package = tmp_path / "duplicate-key.zip"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr(
            "manifest.json",
            b'{"status":"FINAL LOCK / PASS","status":"LOCK CANDIDATE"}',
        )

    with pytest.raises(ValueError, match="duplicate JSON key.*status"):
        load_locked_activity_package(package)


def test_loader_rejects_missing_timeframe_metadata(tmp_path):
    def remove_tf(manifest):
        del manifest["timeframes"]["M30"]

    package = make_synthetic_activity_zip(tmp_path, mutate_manifest=remove_tf)

    with pytest.raises(ValueError, match="missing timeframe metadata.*M30"):
        load_locked_activity_package(package)


def test_loader_rejects_duplicate_timeframe_metadata_value(tmp_path):
    def duplicate_tf_value(manifest):
        manifest["timeframes"]["M15"]["timeframe"] = "M5"

    package = make_synthetic_activity_zip(tmp_path, mutate_manifest=duplicate_tf_value)

    with pytest.raises(ValueError, match="M15.*timeframe.*M5"):
        load_locked_activity_package(package)


def test_loader_rejects_unsafe_manifest_member_name(tmp_path):
    csv_names = {tf: f"{tf}.csv" for tf in TIMEFRAMES}
    csv_names["M5"] = "../M5.csv"
    package = make_synthetic_activity_zip(tmp_path, csv_names=csv_names)

    with pytest.raises(ValueError, match=r"M5.*unsafe.*\.\./M5.csv"):
        load_locked_activity_package(package)


def test_loader_rejects_missing_manifest_referenced_member(tmp_path):
    package = make_synthetic_activity_zip(tmp_path, missing_members={"M15.csv"})

    with pytest.raises(ValueError, match="M15.*missing ZIP member.*M15.csv"):
        load_locked_activity_package(package)


def test_loader_rejects_duplicate_manifest_referenced_member(tmp_path):
    package = make_synthetic_activity_zip(tmp_path, duplicate_member="M30.csv")

    with pytest.raises(ValueError, match="M30.*duplicate ZIP member.*M30.csv"):
        load_locked_activity_package(package)


def test_loaded_bundle_is_deeply_immutable(tmp_path):
    package = make_synthetic_activity_zip(tmp_path)
    bundle = load_locked_activity_package(package)

    with pytest.raises(TypeError):
        bundle.rows_by_tf["M5"][0]["leg_no"] = 999
    with pytest.raises(TypeError):
        bundle.manifest["timeframes"]["M5"]["csv"] = "other.csv"
    with pytest.raises(TypeError):
        bundle.snapshot_sha256_by_tf["M5"] = "0" * 64


def test_write_csv_uses_explicit_field_order_and_stable_bytes(tmp_path):
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    rows = [
        {"alpha": 1, "beta": None, "ignored": "not-a-feature"},
        {"beta": "é", "alpha": 2, "ignored": "also-ignored"},
    ]

    write_csv(first, rows, fieldnames=("beta", "alpha"))
    write_csv(second, rows, fieldnames=("beta", "alpha"))

    expected = "beta,alpha\n,1\né,2\n".encode("utf-8")
    assert first.read_bytes() == expected
    assert second.read_bytes() == expected


def test_write_json_is_sorted_stable_and_rejects_nonfinite(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    payload = {"z": [2, 1], "a": {"é": True}}

    write_json(first, payload)
    write_json(second, payload)

    expected = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")
    assert first.read_bytes() == expected
    assert second.read_bytes() == expected

    rejected = tmp_path / "rejected.json"
    with pytest.raises(ValueError):
        write_json(rejected, {"value": math.nan})
    assert not rejected.exists()


def test_write_output_bundle_is_byte_stable_and_has_fixed_metadata(tmp_path):
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"

    write_output_bundle(first, {"z.json": "{}", "nested/a.csv": b"a\n1\n"})
    write_output_bundle(second, {"nested/a.csv": b"a\n1\n", "z.json": "{}"})

    assert first.read_bytes() == second.read_bytes()
    with zipfile.ZipFile(first) as archive:
        assert archive.namelist() == ["nested/a.csv", "z.json"]
        assert all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in archive.infolist())
        assert archive.read("nested/a.csv") == b"a\n1\n"
