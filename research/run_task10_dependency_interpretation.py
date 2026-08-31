"""Production-safe Task 10 interpretation orchestration and CLI."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess

from research.task10_interpretation_contract import (
    CONTROL_NOT_APPLICABLE,
    TASK9_ACTIVITY_INPUT_SHA256,
    TASK9_AUDIT_CODE_COMMIT,
    TASK9_EVIDENCE_PACKAGE_FILENAME,
    TASK9_REGISTRATION_COMMIT,
    TASK10_SPEC_COMMIT,
)
from research.task10_interpretation_io import (
    Task9EvidenceBundle,
    load_task9_evidence_package,
    write_task10_outputs,
)
from research.task10_interpretation_reports import (
    build_feature_dossiers,
    build_future_ablation_hypotheses,
    build_main_relationship_dossiers,
    build_supplementary_evidence,
)


_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_REQUIRED_HEAD_PATHS = (
    "research/task10_interpretation_contract.py",
    "research/task10_interpretation_io.py",
    "research/task10_interpretation_reports.py",
    "research/run_task10_dependency_interpretation.py",
)
_SHA1_RE = re.compile(r"[0-9a-f]{40}\Z")
_FALSE_SCOPE_FIELDS = (
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
)


def _git(*args: str, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=_REPOSITORY_ROOT,
        check=False,
        capture_output=capture_output,
        text=True,
    )


def assert_clean_committed_task10_worktree() -> str:
    """Return HEAD only when tracked state is clean and all production files exist."""

    if _git("diff", "--quiet").returncode != 0:
        raise RuntimeError("tracked worktree is not clean")
    if _git("diff", "--cached", "--quiet").returncode != 0:
        raise RuntimeError("tracked worktree is not clean")
    status = _git(
        "status", "--porcelain=v1", "--untracked-files=no", capture_output=True
    )
    if status.returncode != 0:
        raise RuntimeError("unable to inspect tracked worktree")
    if status.stdout:
        raise RuntimeError("tracked worktree is not clean")
    head_result = _git("rev-parse", "HEAD", capture_output=True)
    head = head_result.stdout.strip()
    if head_result.returncode != 0 or _SHA1_RE.fullmatch(head) is None:
        raise RuntimeError("invalid HEAD SHA")
    for path in _REQUIRED_HEAD_PATHS:
        if _git("cat-file", "-e", f"HEAD:{path}").returncode != 0:
            raise RuntimeError(f"required Task 10 path is absent from HEAD: {path}")
    return head


def _build_manifest(
    bundle: Task9EvidenceBundle,
    *,
    implementation_commit: str,
    main_count: int,
    partial_eligible_count: int,
    control_non_applicable_count: int,
    supplementary_count: int,
    feature_count: int,
    hypothesis_count: int,
) -> dict[str, object]:
    if _SHA1_RE.fullmatch(implementation_commit) is None:
        raise ValueError("implementation_commit must be a lowercase 40-character SHA")
    manifest: dict[str, object] = {
        "task": "Task 10 Dependency / Redundancy Interpretation",
        "task10_spec_commit": TASK10_SPEC_COMMIT,
        "task10_implementation_commit": implementation_commit,
        "task9_evidence_package_filename": TASK9_EVIDENCE_PACKAGE_FILENAME,
        "task9_evidence_package_sha256": bundle.evidence_zip_sha256,
        "task9_activity_input_sha256": TASK9_ACTIVITY_INPUT_SHA256,
        "task9_audit_code_commit": TASK9_AUDIT_CODE_COMMIT,
        "task9_registration_commit": TASK9_REGISTRATION_COMMIT,
        "main_relationship_dossier_count": main_count,
        "partial_delta_eligible_pair_count": partial_eligible_count,
        "control_feature_non_applicable_pair_count": control_non_applicable_count,
        "feature_dossier_count": feature_count,
        "supplementary_evidence_row_count": supplementary_count,
        "future_ablation_hypothesis_count": hypothesis_count,
        **{field: False for field in _FALSE_SCOPE_FIELDS},
    }
    expected_counts = (
        main_count,
        partial_eligible_count,
        control_non_applicable_count,
        supplementary_count,
        feature_count,
        hypothesis_count,
    )
    if expected_counts != (78, 66, 12, 960, 13, 0):
        raise ValueError(
            "Task 10 locked output counts differ from 78/66/12/960/13/0: "
            f"got {expected_counts}"
        )
    if any(manifest.get(field) is not False for field in _FALSE_SCOPE_FIELDS):
        raise ValueError("Task 10 mandatory scope-state fields must be false")
    return manifest


def _run_task10_from_bundle(
    bundle: Task9EvidenceBundle,
    output_dir: Path,
    *,
    implementation_commit: str,
    output_zip: Path | None = None,
) -> dict[str, object]:
    """Private deterministic seam used only after a bundle is already validated."""

    main_dossiers = build_main_relationship_dossiers(bundle)
    supplementary = build_supplementary_evidence(bundle)
    feature_dossiers = build_feature_dossiers(bundle, main_dossiers)
    hypotheses = build_future_ablation_hypotheses()
    partial_eligible_count = sum(
        dossier["partial_applicability"] == "ELIGIBLE"
        for dossier in main_dossiers
    )
    control_non_applicable_count = sum(
        dossier["partial_applicability"] == CONTROL_NOT_APPLICABLE
        for dossier in main_dossiers
    )
    manifest = _build_manifest(
        bundle,
        implementation_commit=implementation_commit,
        main_count=len(main_dossiers),
        partial_eligible_count=partial_eligible_count,
        control_non_applicable_count=control_non_applicable_count,
        supplementary_count=len(supplementary),
        feature_count=len(feature_dossiers),
        hypothesis_count=len(hypotheses),
    )
    write_task10_outputs(
        output_dir,
        implementation_commit=implementation_commit,
        main_dossiers=main_dossiers,
        supplementary_evidence=supplementary,
        feature_dossiers=feature_dossiers,
        future_ablation_hypotheses=hypotheses,
        manifest=manifest,
        output_zip=output_zip,
    )
    return manifest


def run_task10(
    input_evidence: Path,
    output_dir: Path,
    *,
    output_zip: Path | None = None,
) -> dict[str, object]:
    """Run the canonical production path after validating committed provenance."""

    implementation_commit = assert_clean_committed_task10_worktree()
    bundle = load_task9_evidence_package(input_evidence)
    return _run_task10_from_bundle(
        bundle,
        output_dir,
        implementation_commit=implementation_commit,
        output_zip=output_zip,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Task 10 dependency/redundancy interpretation artifacts."
    )
    parser.add_argument("--input-evidence", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--output-zip", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_task10(
        args.input_evidence,
        args.output_dir,
        output_zip=args.output_zip,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
