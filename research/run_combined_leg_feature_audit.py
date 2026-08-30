"""Run the descriptive Combined Leg Feature Audit on a locked Activity package."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.combined_audit_contract import (  # noqa: E402
    DIRECTIONS,
    TIMEFRAMES,
    feature_role_rows,
)
from research.combined_audit_io import (  # noqa: E402
    load_locked_activity_package,
    write_combined_audit_outputs,
)
from research.combined_audit_reports import (  # noqa: E402
    build_cross_tf_relationship_report,
    build_deterministic_identity_report,
    build_direction_stratified_report,
    build_main_spearman_report,
    build_partial_spearman_report,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-zip", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    bundle = load_locked_activity_package(args.input_zip)
    feature_roles = feature_role_rows()
    deterministic: dict[str, list[dict[str, object]]] = {}
    main_reports: dict[str, list[dict[str, object]]] = {}
    partial_reports: dict[str, list[dict[str, object]]] = {}
    supplementary: dict[tuple[str, str], dict[str, object]] = {}
    for tf in TIMEFRAMES:
        rows = bundle.rows_by_tf[tf]
        deterministic[tf] = build_deterministic_identity_report(rows)
        main_reports[tf] = build_main_spearman_report(rows)
        partial_reports[tf] = build_partial_spearman_report(rows)
        for direction in DIRECTIONS:
            supplementary[(tf, direction)] = build_direction_stratified_report(
                rows, direction
            )
    cross_tf = build_cross_tf_relationship_report(main_reports, partial_reports)

    write_combined_audit_outputs(
        args.output_dir,
        bundle=bundle,
        feature_roles=feature_roles,
        deterministic=deterministic,
        main_reports=main_reports,
        partial_reports=partial_reports,
        supplementary=supplementary,
        cross_tf=cross_tf,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
