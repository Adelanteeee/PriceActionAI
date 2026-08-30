import csv
import hashlib
import io
import json
import re
import sys
import zipfile

from research.run_combined_leg_feature_audit import main


TIMEFRAMES = ("M5", "M15", "M30", "H1")
DIRECTIONS = ("BULLISH", "BEARISH")
LOCKED_SOURCE_COMMIT = "b43ed7a6d1d8538d8860934abbb24b0c9561a317"

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


def _locked_leg_csv(tf_index):
    rows = []
    for index in range(8):
        direction = DIRECTIONS[index % 2]
        direction_sign = 1 if direction == "BULLISH" else -1
        active = index + 2
        gross_close_path = float(active * 2 + tf_index)
        gross_candle_range = float(active * 3 + tf_index)
        forward_shadow = float(active * 0.4 + tf_index * 0.1)
        backward_shadow = float(active * 0.6 + tf_index * 0.2)
        shadow_magnitude = forward_shadow + backward_shadow
        overlap_capacity = float(active * 2 + tf_index * 0.5)
        close_slope = float((index + 1) * 0.1 + tf_index * 0.01)
        directional_slope = direction_sign * close_slope
        mean_candle_range = gross_candle_range / active
        signed_displacement = float(direction_sign * (index + 1.25 + tf_index))
        mean_tick_activity = float(10 * (index + 1) + tf_index)
        row = {
            "active_bar_count": active,
            "net_thrust": float(index * 1.7 + tf_index + 2),
            "gross_close_path": gross_close_path,
            "net_close_displacement": abs(signed_displacement),
            "directional_efficiency": float((index + 1) / 10),
            "directional_continuity_ratio": (active - 1) / active,
            "close_confirmation_ratio": float((index + 2) / 12),
            "gap_path_share": 0.25,
            "body_strength_ratio": 0.5,
            "shadow_position_imbalance": (
                backward_shadow - forward_shadow
            ) / shadow_magnitude,
            "overlap_ratio": 0.35,
            "normalized_directional_close_ols_slope": (
                directional_slope / mean_candle_range
            ),
            "mean_tick_activity": mean_tick_activity,
            "close_ols_slope": close_slope,
            "gross_upper_shadow": float(index * 1.1 + tf_index + 1),
            "gross_lower_shadow": float((8 - index) * 0.9 + tf_index),
            "signed_close_displacement": signed_displacement,
            "aligned_close_steps": active - 1,
            "opposing_close_steps": 1,
            "flat_close_steps": 0,
            "gap_path_contribution": gross_close_path * 0.25,
            "gross_body_magnitude": gross_candle_range * 0.5,
            "gross_candle_range": gross_candle_range,
            "gross_forward_shadow": forward_shadow,
            "gross_backward_shadow": backward_shadow,
            "gross_shadow_magnitude": shadow_magnitude,
            "gross_overlap_magnitude": overlap_capacity * 0.35,
            "gross_overlap_capacity": overlap_capacity,
            "directional_close_ols_slope": directional_slope,
            "gross_tick_activity": mean_tick_activity * active,
            "leg_no": index + 1,
            "direction": direction,
            "start_index": index * 10,
            "end_index": index * 10 + active,
            "start_time": f"2026-01-{index + 1:02d}T00:00:00Z",
            "end_time": f"2026-01-{index + 1:02d}T01:00:00Z",
            "start_kind": "SWING",
            "end_kind": "SWING",
            "start_price": float(1900 + index + tf_index),
            "end_price": float(1901 + index + tf_index),
            "owned_candle_count": active + 1,
        }
        rows.append(row)

    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=REQUIRED_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def make_four_tf_synthetic_locked_package(tmp_path):
    snapshots = {
        tf: f"time,close\n2026-01-01T00:00:00Z,{1900 + tf_index}\n".encode()
        for tf_index, tf in enumerate(TIMEFRAMES)
    }
    manifest = {
        "status": "FINAL LOCK / PASS",
        "current_commit": LOCKED_SOURCE_COMMIT,
        "broker_company": "Synthetic Broker LLC",
        "broker_server": "Synthetic-Test-Server",
        "timeframes": {
            tf: {
                "symbol": f"SYNTH_{tf}",
                "timeframe": tf,
                "csv": f"legs/{tf}.csv",
                "snapshot_file": f"snapshots/{tf}.csv",
                "snapshot_sha256": hashlib.sha256(snapshots[tf]).hexdigest(),
            }
            for tf in reversed(TIMEFRAMES)
        },
    }

    package = tmp_path / "synthetic_locked_activity.zip"
    with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        for tf_index, tf in enumerate(TIMEFRAMES):
            archive.writestr(f"legs/{tf}.csv", _locked_leg_csv(tf_index))
            archive.writestr(f"snapshots/{tf}.csv", snapshots[tf])
    return package


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _artifact_bytes(output_dir):
    return {path.name: path.read_bytes() for path in output_dir.iterdir()}


def test_end_to_end_synthetic_package_writes_all_required_artifacts(tmp_path):
    input_zip = make_four_tf_synthetic_locked_package(tmp_path)
    input_before = input_zip.read_bytes()
    input_stat_before = input_zip.stat()
    output_dir = tmp_path / "out"

    modules_before = set(sys.modules)
    rc = main(["--input-zip", str(input_zip), "--output-dir", str(output_dir)])

    assert rc == 0
    assert input_zip.read_bytes() == input_before
    assert input_zip.stat().st_mtime_ns == input_stat_before.st_mtime_ns
    assert not any(
        name not in modules_before
        and ("price_action_ai_leg_v0" in name.lower() or "metatrader5" in name.lower())
        for name in sys.modules
    )

    expected = {
        "FEATURE_ROLE_MATRIX.csv",
        "DETERMINISTIC_IDENTITY_REPORT.csv",
        "CROSS_TF_RELATIONSHIP_REPORT.csv",
        "COMBINED_AUDIT_MANIFEST.json",
        *(f"MAIN_SPEARMAN_{tf}.csv" for tf in TIMEFRAMES),
        *(f"PARTIAL_SPEARMAN_{tf}.csv" for tf in TIMEFRAMES),
        *(
            f"SUPPLEMENTARY_{tf}_{direction}.csv"
            for tf in TIMEFRAMES
            for direction in DIRECTIONS
        ),
    }
    assert {path.name for path in output_dir.iterdir()} == expected
    assert len(expected) == 20

    deterministic = _read_csv(output_dir / "DETERMINISTIC_IDENTITY_REPORT.csv")
    assert len(deterministic) == 44
    assert tuple(deterministic[0]) == (
        "timeframe",
        "relation_id",
        "formula",
        "conditions",
        "tolerance_policy",
        "total_rows",
        "verified_rows",
        "failed_rows",
    )
    assert [row["timeframe"] for row in deterministic[::11]] == list(TIMEFRAMES)
    assert all(
        int(row["verified_rows"]) + int(row["failed_rows"])
        == int(row["total_rows"])
        for row in deterministic
    )

    for tf in TIMEFRAMES:
        assert len(_read_csv(output_dir / f"MAIN_SPEARMAN_{tf}.csv")) == 78
        assert len(_read_csv(output_dir / f"PARTIAL_SPEARMAN_{tf}.csv")) == 66
        for direction in DIRECTIONS:
            rows = _read_csv(output_dir / f"SUPPLEMENTARY_{tf}_{direction}.csv")
            assert len(rows) == 120
            assert all(row["evidence_scope"] == "SUPPLEMENTARY_ONLY" for row in rows)
            assert all(
                row["rho_duration_controlled"] == ""
                for row in rows
                if "active_bar_count" in (row["feature_x"], row["feature_y"])
            )
            assert all(
                row["controlled_status"] != ""
                for row in rows
                if "active_bar_count" not in (row["feature_x"], row["feature_y"])
            )

    assert len(_read_csv(output_dir / "CROSS_TF_RELATIONSHIP_REPORT.csv")) == 78

    manifest = json.loads(
        (output_dir / "COMBINED_AUDIT_MANIFEST.json").read_text(encoding="utf-8")
    )
    assert manifest["analysis_feature_count"] == 13
    assert manifest["timeframes"] == list(TIMEFRAMES)
    assert manifest["raw_cross_tf_pooling"] is False
    assert manifest["control_variable"] == "active_bar_count"
    assert manifest["deterministic_float_rel_tol"] == 1e-12
    assert manifest["deterministic_float_abs_tol"] == 1e-12
    assert manifest["input_locked_leg_source_commit"] == LOCKED_SOURCE_COMMIT
    assert manifest["input_zip_sha256"] == hashlib.sha256(input_before).hexdigest()
    assert manifest["broker_company"] == "Synthetic Broker LLC"
    assert manifest["broker_server"] == "Synthetic-Test-Server"
    assert manifest["symbols_by_tf"] == {tf: f"SYNTH_{tf}" for tf in TIMEFRAMES}
    assert manifest["snapshot_sha256_by_tf"] == {
        tf: hashlib.sha256(
            f"time,close\n2026-01-01T00:00:00Z,{1900 + index}\n".encode()
        ).hexdigest()
        for index, tf in enumerate(TIMEFRAMES)
    }
    assert manifest["required_schema_gate_passed_by_tf"] == {
        tf: True for tf in TIMEFRAMES
    }
    assert manifest["numeric_finiteness_gate_passed_by_tf"] == {
        tf: True for tf in TIMEFRAMES
    }
    assert manifest["report_filenames"] == sorted(expected)
    assert re.fullmatch(r"[0-9a-f]{40}", manifest["audit_code_commit"])
    assert "generated_at" not in manifest
    assert "timestamp" not in manifest

    first_run = _artifact_bytes(output_dir)
    assert main(["--input-zip", str(input_zip), "--output-dir", str(output_dir)]) == 0
    assert _artifact_bytes(output_dir) == first_run
    assert input_zip.read_bytes() == input_before
