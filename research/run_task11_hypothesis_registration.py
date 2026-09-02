"""Private deterministic orchestration for Task 11 hypothesis registration."""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
from pathlib import Path

from research.task11_hypothesis_contract import (
    CONTROL_FEATURE_NON_APPLICABLE_COUNT,
    DETERMINISTIC_CONTEXT_PAIR_COUNT,
    DURATION_CONTROL_ELIGIBLE_COUNT,
    HYPOTHESIS_COUNT,
    HYPOTHESIS_ID_PREFIX,
    LOGICAL_FILE_COUNT,
    MAIN_PAIR_COUNT,
    OUTPUT_ZIP_FILENAME,
    TASK10_IMPLEMENTATION_COMMIT,
    TASK10_MAIN_DOSSIERS_MEMBER_SHA256,
    TASK10_MANIFEST_MEMBER_SHA256,
    TASK10_PRODUCTION_PACKAGE_FILENAME,
    TASK10_PRODUCTION_PACKAGE_SHA256,
    TASK11_FALSE_SCOPE_FIELDS,
    TASK11_LOGICAL_FILENAMES,
    TASK11_MANIFEST_FIELDS,
    TASK11_SPEC_BLOB_SHA,
    TASK11_SPEC_COMMIT,
    TASK11_SPEC_LOCK_COMMIT,
    TASK11_SPEC_LOCK_RECORD_BLOB_SHA,
    TASK11_SPEC_LOCK_RECORD_PATH,
    TASK11_SPEC_PATH,
    TEST_QUESTION_TEMPLATE_ID,
)
from research.task11_hypothesis_io import (
    Task10ProductionBundle,
    _json_bytes,
    _validate_output_zip_path,
    load_task10_production_package,
    write_task11_outputs,
)
from research.task11_hypothesis_registry import (
    build_hypothesis_registry,
    validate_hypothesis_registry,
)


_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_REQUIRED_HEAD_PATHS = (
    "research/task11_hypothesis_contract.py",
    "research/task11_hypothesis_io.py",
    "research/task11_hypothesis_registry.py",
    "research/run_task11_hypothesis_registration.py",
    TASK11_SPEC_PATH,
    TASK11_SPEC_LOCK_RECORD_PATH,
)
_SHA1_RE = re.compile(r"[0-9a-f]{40}\Z")


def _git(*args: str, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=_REPOSITORY_ROOT,
        check=False,
        capture_output=capture_output,
        text=True,
    )


def assert_clean_committed_task11_worktree() -> str:
    """Return HEAD only when the locked Task 11 implementation is clean and present."""
    if _git("diff", "--quiet").returncode != 0:
        raise RuntimeError("tracked worktree is not clean")
    if _git("diff", "--cached", "--quiet").returncode != 0:
        raise RuntimeError("tracked worktree is not clean")

    status = _git(
        "status", "--porcelain=v1", "--untracked-files=no", capture_output=True
    )
    if status.returncode != 0 or status.stdout:
        raise RuntimeError("tracked worktree is not clean")

    head_result = _git("rev-parse", "HEAD", capture_output=True)
    head = head_result.stdout.strip()
    if head_result.returncode != 0 or not _SHA1_RE.fullmatch(head):
        raise RuntimeError("invalid HEAD SHA")

    if _git("merge-base", "--is-ancestor", TASK11_SPEC_COMMIT, head).returncode != 0:
        raise RuntimeError("locked Task 11 Spec commit is not an ancestor")
    if (
        _git("merge-base", "--is-ancestor", TASK11_SPEC_LOCK_COMMIT, head).returncode
        != 0
    ):
        raise RuntimeError("Task 11 Spec Lock commit is not an ancestor")

    for path in _REQUIRED_HEAD_PATHS:
        if _git("cat-file", "-e", f"HEAD:{path}").returncode != 0:
            raise RuntimeError(f"required Task 11 implementation path missing at HEAD: {path}")

    spec_blob = _git("rev-parse", f"HEAD:{TASK11_SPEC_PATH}", capture_output=True)
    if spec_blob.returncode != 0 or spec_blob.stdout.strip() != TASK11_SPEC_BLOB_SHA:
        raise RuntimeError("locked Task 11 Spec blob mismatch")
    lock_blob = _git(
        "rev-parse", f"HEAD:{TASK11_SPEC_LOCK_RECORD_PATH}", capture_output=True
    )
    if (
        lock_blob.returncode != 0
        or lock_blob.stdout.strip() != TASK11_SPEC_LOCK_RECORD_BLOB_SHA
    ):
        raise RuntimeError("locked Task 11 Spec Lock Record blob mismatch")

    return head


def _build_manifest(
    bundle: Task10ProductionBundle,
    *,
    implementation_commit: str,
    hypothesis_registry_sha256: str,
    main_pair_count: int,
    hypothesis_count: int,
    duration_control_eligible_count: int,
    control_feature_non_applicable_count: int,
    deterministic_context_pair_count: int,
) -> dict[str, object]:
    """Build the closed Task 11 manifest after the source bundle is validated."""
    if type(implementation_commit) is not str or not _SHA1_RE.fullmatch(
        implementation_commit
    ):
        raise ValueError("Task 11 implementation commit must be lowercase SHA-1")
    if type(hypothesis_registry_sha256) is not str or not re.fullmatch(
        r"[0-9a-f]{64}", hypothesis_registry_sha256
    ):
        raise ValueError("Task 11 registry SHA-256 must be lowercase hexadecimal")
    observed_counts = (
        main_pair_count,
        hypothesis_count,
        duration_control_eligible_count,
        control_feature_non_applicable_count,
        deterministic_context_pair_count,
    )
    if any(type(value) is not int for value in observed_counts):
        raise ValueError("Task 11 observed counts must be integers")
    if (
        *observed_counts,
        LOGICAL_FILE_COUNT,
    ) != (
        MAIN_PAIR_COUNT,
        HYPOTHESIS_COUNT,
        DURATION_CONTROL_ELIGIBLE_COUNT,
        CONTROL_FEATURE_NON_APPLICABLE_COUNT,
        DETERMINISTIC_CONTEXT_PAIR_COUNT,
        LOGICAL_FILE_COUNT,
    ):
        raise ValueError("Task 11 observed counts do not match the locked tuple")

    manifest: dict[str, object] = {
        "task": "Task 11 — Evidence Review & Hypothesis Registration",
        "task11_spec_commit": TASK11_SPEC_COMMIT,
        "task11_implementation_commit": implementation_commit,
        "hypothesis_registry_filename": "TASK11_HYPOTHESIS_REGISTRY.json",
        "hypothesis_registry_sha256": hypothesis_registry_sha256,
        "production_archive_filename": OUTPUT_ZIP_FILENAME,
        "logical_output_filenames": list(TASK11_LOGICAL_FILENAMES),
        "task10_implementation_commit": TASK10_IMPLEMENTATION_COMMIT,
        "task10_production_package_filename": TASK10_PRODUCTION_PACKAGE_FILENAME,
        "task10_production_package_sha256": TASK10_PRODUCTION_PACKAGE_SHA256,
        "task10_main_dossiers_member_sha256": TASK10_MAIN_DOSSIERS_MEMBER_SHA256,
        "task10_manifest_member_sha256": TASK10_MANIFEST_MEMBER_SHA256,
        "hypothesis_unit": "PAIRWISE_ONLY",
        "hypothesis_cardinality": "EXACTLY_ONE_PER_CANONICAL_PAIR",
        "hypothesis_id_policy": "DETERMINISTIC_FROM_PAIR_KEY",
        "hypothesis_id_prefix": HYPOTHESIS_ID_PREFIX,
        "test_question_policy": "SINGLE_FIXED_TEMPLATE",
        "test_question_template_id": TEST_QUESTION_TEMPLATE_ID,
        "evidence_summary_policy": "COPY_LOCKED_TASK10_OBSERVATIONS",
        "cross_tf_evidence_policy": "COPY_LOCKED_TASK10_CROSS_TF",
        "main_pair_count": main_pair_count,
        "hypothesis_count": hypothesis_count,
        "duration_control_eligible_count": duration_control_eligible_count,
        "control_feature_non_applicable_count": (
            control_feature_non_applicable_count
        ),
        "deterministic_context_pair_count": deterministic_context_pair_count,
        "logical_file_count": LOGICAL_FILE_COUNT,
        **{field: False for field in TASK11_FALSE_SCOPE_FIELDS},
    }
    if set(manifest) != set(TASK11_MANIFEST_FIELDS):
        raise RuntimeError("Task 11 manifest closed schema drifted")
    return manifest


def _run_task11_from_bundle(
    bundle: Task10ProductionBundle,
    output_dir: Path,
    *,
    implementation_commit: str,
    output_zip: Path,
) -> dict[str, object]:
    output_zip = _validate_output_zip_path(output_zip)
    registry = build_hypothesis_registry(bundle.main_dossiers)
    validate_hypothesis_registry(registry, bundle.main_dossiers)
    registry_bytes = _json_bytes(registry)
    eligible_count = sum(
        record["duration_control_applicability"] == "ELIGIBLE" for record in registry
    )
    control_count = sum(
        record["duration_control_applicability"]
        == "NOT_APPLICABLE_CONTROL_FEATURE"
        for record in registry
    )
    deterministic_count = sum(
        record["direct_deterministic_dependency"] is True for record in registry
    )
    manifest = _build_manifest(
        bundle,
        implementation_commit=implementation_commit,
        hypothesis_registry_sha256=hashlib.sha256(registry_bytes).hexdigest(),
        main_pair_count=len(bundle.main_dossiers),
        hypothesis_count=len(registry),
        duration_control_eligible_count=eligible_count,
        control_feature_non_applicable_count=control_count,
        deterministic_context_pair_count=deterministic_count,
    )
    write_task11_outputs(
        output_dir,
        implementation_commit=implementation_commit,
        registry=registry,
        manifest=manifest,
        output_zip=output_zip,
    )
    return manifest


def run_task11(
    input_task10_production: Path,
    output_dir: Path,
    *,
    output_zip: Path,
) -> dict[str, object]:
    """Register the locked Task 11 package from its canonical Task 10 input."""
    implementation_commit = assert_clean_committed_task11_worktree()
    output_zip = _validate_output_zip_path(output_zip)
    bundle = load_task10_production_package(input_task10_production)
    return _run_task11_from_bundle(
        bundle,
        output_dir,
        implementation_commit=implementation_commit,
        output_zip=output_zip,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the locked Task 11 runtime CLI."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-task10-production", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--output-zip", required=True, type=Path)
    return parser


def main() -> int:
    """Run Task 11 from the required canonical paths."""
    arguments = build_parser().parse_args()
    run_task11(
        arguments.input_task10_production,
        arguments.output_dir,
        output_zip=arguments.output_zip,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
