"""Private integration coverage for Task 11 deterministic outputs."""

from __future__ import annotations

import hashlib
import inspect
import json
import subprocess
import zipfile
from pathlib import Path

import pytest

from research.run_task11_hypothesis_registration import (
    _build_manifest,
    _run_task11_from_bundle,
    assert_clean_committed_task11_worktree,
    build_parser,
    run_task11,
)
from research.task11_hypothesis_contract import (
    OUTPUT_ZIP_FILENAME,
    TASK11_FALSE_SCOPE_FIELDS,
    TASK11_LOGICAL_FILENAMES,
    TASK11_MANIFEST_FIELDS,
    TASK11_SPEC_LOCK_RECORD_PATH,
    TASK11_SPEC_PATH,
)
from research.task11_hypothesis_io import _json_bytes, write_task11_outputs
from research.task11_hypothesis_registry import build_hypothesis_registry
from test_task11_hypothesis_io import (
    load_synthetic_task10,
    make_synthetic_task10_production_zip,
)


def artifact_bytes(directory: Path) -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in directory.iterdir()}


def _git(repository: Path, *args: str, capture_output: bool = False):
    return subprocess.run(
        ["git", *args],
        cwd=repository,
        check=True,
        capture_output=capture_output,
        text=True,
    )


def _commit(repository: Path, message: str) -> str:
    _git(repository, "add", ".")
    _git(repository, "commit", "-m", message)
    return _git(repository, "rev-parse", "HEAD", capture_output=True).stdout.strip()


def _init_guard_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a clean repository with Task 11's locked provenance history."""
    import research.run_task11_hypothesis_registration as runner

    repository = tmp_path / "guard-repository"
    repository.mkdir()
    _git(repository, "init")
    _git(repository, "config", "user.email", "task11@example.test")
    _git(repository, "config", "user.name", "Task 11 Test")

    source_root = Path(__file__).resolve().parents[1]
    spec_path = repository / TASK11_SPEC_PATH
    spec_path.parent.mkdir(parents=True)
    spec_path.write_bytes((source_root / TASK11_SPEC_PATH).read_bytes())
    spec_commit = _commit(repository, "add locked spec")
    spec_blob = _git(
        repository, "rev-parse", f"HEAD:{TASK11_SPEC_PATH}", capture_output=True
    ).stdout.strip()

    lock_path = repository / TASK11_SPEC_LOCK_RECORD_PATH
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_bytes((source_root / TASK11_SPEC_LOCK_RECORD_PATH).read_bytes())
    lock_commit = _commit(repository, "add locked spec record")
    lock_blob = _git(
        repository,
        "rev-parse",
        f"HEAD:{TASK11_SPEC_LOCK_RECORD_PATH}",
        capture_output=True,
    ).stdout.strip()

    for path in (
        "research/task11_hypothesis_contract.py",
        "research/task11_hypothesis_io.py",
        "research/task11_hypothesis_registry.py",
        "research/run_task11_hypothesis_registration.py",
    ):
        target = repository / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# task 11 required implementation path\n")
    head = _commit(repository, "add task 11 implementation")

    _git(repository, "checkout", "-b", "task11-non-ancestor", spec_commit)
    (repository / "non-ancestor-marker").write_text("valid unreachable commit\n")
    _commit(repository, "add valid non-ancestor")
    _git(repository, "checkout", "--detach", head)

    monkeypatch.setattr(runner, "_REPOSITORY_ROOT", repository)
    monkeypatch.setattr(runner, "TASK11_SPEC_COMMIT", spec_commit)
    monkeypatch.setattr(runner, "TASK11_SPEC_BLOB_SHA", spec_blob)
    monkeypatch.setattr(runner, "TASK11_SPEC_LOCK_COMMIT", lock_commit)
    monkeypatch.setattr(runner, "TASK11_SPEC_LOCK_RECORD_BLOB_SHA", lock_blob)
    return repository


def test_public_function_and_cli_expose_only_locked_runtime_paths():
    """A runtime override could bypass Task 11's locked provenance."""
    parameters = inspect.signature(run_task11).parameters
    assert tuple(parameters) == (
        "input_task10_production",
        "output_dir",
        "output_zip",
    )
    assert parameters["output_zip"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["output_zip"].default is inspect.Parameter.empty

    parser = build_parser()
    option_strings = {
        option for action in parser._actions for option in action.option_strings
    }
    assert option_strings == {
        "-h",
        "--help",
        "--input-task10-production",
        "--output-dir",
        "--output-zip",
    }
    assert all(
        parser.get_default(name) is None
        for name in ("input_task10_production", "output_dir", "output_zip")
    )
    non_help_actions = [action for action in parser._actions if action.dest != "help"]
    assert {action.dest for action in non_help_actions} == {
        "input_task10_production",
        "output_dir",
        "output_zip",
    }
    assert all(action.required is True and action.type is Path for action in non_help_actions)

    forbidden = (
        "sha",
        "loader",
        "bundle",
        "template",
        "identifier",
        "count",
        "ordering",
        "commit",
        "rank",
        "score",
        "threshold",
        "outcome",
        "ablation",
        "causal",
        "feature_selection",
    )
    exposed_names = (*parameters, *(action.dest for action in non_help_actions))
    assert all(term not in name for name in exposed_names for term in forbidden)


def test_public_flow_stops_at_guard_before_loader_or_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """A failed provenance check must prevent package reads and output creation."""
    import research.run_task11_hypothesis_registration as runner

    def blocked_guard() -> str:
        raise RuntimeError("guard blocked")

    def loader_must_not_run(_path: Path):
        raise AssertionError("loader ran after failed provenance guard")

    monkeypatch.setattr(runner, "assert_clean_committed_task11_worktree", blocked_guard)
    monkeypatch.setattr(runner, "load_task10_production_package", loader_must_not_run)

    output_dir = tmp_path / "blocked"
    output_zip = tmp_path / "blocked.zip"
    with pytest.raises(RuntimeError, match="guard blocked"):
        run_task11(tmp_path / "unused.zip", output_dir, output_zip=output_zip)
    assert not output_dir.exists()
    assert not output_zip.exists()


def test_public_flow_rejects_noncanonical_zip_before_loader_or_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """A noncanonical archive name must fail before package loading."""
    import research.run_task11_hypothesis_registration as runner

    monkeypatch.setattr(
        runner, "assert_clean_committed_task11_worktree", lambda: "b" * 40
    )

    def loader_must_not_run(_path: Path):
        raise AssertionError("loader ran after invalid output ZIP basename")

    monkeypatch.setattr(runner, "load_task10_production_package", loader_must_not_run)
    output_dir = tmp_path / "noncanonical-output"
    output_zip = tmp_path / "noncanonical.zip"
    with pytest.raises(ValueError, match="production ZIP basename"):
        run_task11(tmp_path / "unused.zip", output_dir, output_zip=output_zip)
    assert not output_dir.exists()
    assert not output_zip.exists()


def test_public_flow_writes_guard_commit_to_returned_and_written_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """The manifest must identify the exact provenance SHA captured by the guard."""
    import research.run_task11_hypothesis_registration as runner

    package = make_synthetic_task10_production_zip()
    bundle = load_synthetic_task10(package)
    monkeypatch.setattr(
        runner, "assert_clean_committed_task11_worktree", lambda: "b" * 40
    )
    monkeypatch.setattr(runner, "load_task10_production_package", lambda _path: bundle)
    output_dir = tmp_path / "accepted" / "logical"
    output_zip = tmp_path / "accepted" / OUTPUT_ZIP_FILENAME

    manifest = run_task11(package, output_dir, output_zip=output_zip)

    assert manifest["task11_implementation_commit"] == "b" * 40
    written_manifest = json.loads((output_dir / "TASK11_MANIFEST.json").read_bytes())
    assert written_manifest["task11_implementation_commit"] == "b" * 40
    logical_payloads = artifact_bytes(output_dir)
    assert set(logical_payloads) == set(TASK11_LOGICAL_FILENAMES)
    assert output_zip.is_file()
    with zipfile.ZipFile(output_zip) as archive:
        assert archive.namelist() == sorted(TASK11_LOGICAL_FILENAMES)
        assert {
            info.filename: archive.read(info) for info in archive.infolist()
        } == logical_payloads


def test_guard_returns_exact_head_for_clean_tracked_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Returning another SHA would misidentify the implementation that produced output."""
    repository = _init_guard_repo(tmp_path, monkeypatch)
    expected_head = _git(repository, "rev-parse", "HEAD", capture_output=True).stdout.strip()
    assert assert_clean_committed_task11_worktree() == expected_head


def test_guard_ignores_untracked_file_without_touching_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Untracked artifacts are excluded from the tracked provenance boundary."""
    repository = _init_guard_repo(tmp_path, monkeypatch)
    expected_head = _git(repository, "rev-parse", "HEAD", capture_output=True).stdout.strip()
    untracked = repository / "untracked-artifact.txt"
    payload = b"preserve this untracked artifact\n"
    untracked.write_bytes(payload)

    assert assert_clean_committed_task11_worktree() == expected_head
    assert untracked.is_file()
    assert untracked.read_bytes() == payload


@pytest.mark.parametrize("staged", [False, True])
def test_guard_rejects_tracked_worktree_or_index_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, staged: bool
):
    """A tracked implementation edit could make output provenance inaccurate."""
    repository = _init_guard_repo(tmp_path, monkeypatch)
    changed_path = repository / "research/task11_hypothesis_registry.py"
    changed_path.write_text("# changed\n")
    if staged:
        _git(repository, "add", "research/task11_hypothesis_registry.py")

    with pytest.raises(RuntimeError, match="tracked worktree is not clean"):
        assert_clean_committed_task11_worktree()


def test_guard_rejects_missing_required_head_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """A partial committed implementation must not be accepted as Task 11."""
    repository = _init_guard_repo(tmp_path, monkeypatch)
    missing_path = "research/task11_hypothesis_io.py"
    _git(repository, "rm", missing_path)
    _commit(repository, "remove required implementation path")

    with pytest.raises(RuntimeError, match=missing_path):
        assert_clean_committed_task11_worktree()


def test_guard_rejects_spec_commit_outside_head_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """A detached locked Spec commit means the reviewed design is not in history."""
    repository = _init_guard_repo(tmp_path, monkeypatch)
    import research.run_task11_hypothesis_registration as runner

    non_ancestor = _git(
        repository, "rev-parse", "task11-non-ancestor", capture_output=True
    ).stdout.strip()
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", non_ancestor, "HEAD"],
        cwd=repository,
        check=False,
    )
    assert ancestry.returncode == 1
    monkeypatch.setattr(runner, "TASK11_SPEC_COMMIT", non_ancestor)
    with pytest.raises(RuntimeError, match="locked Task 11 Spec commit is not an ancestor"):
        assert_clean_committed_task11_worktree()


def test_guard_rejects_lock_record_commit_outside_head_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """A detached lock record means the locked review record is not in history."""
    repository = _init_guard_repo(tmp_path, monkeypatch)
    import research.run_task11_hypothesis_registration as runner

    non_ancestor = _git(
        repository, "rev-parse", "task11-non-ancestor", capture_output=True
    ).stdout.strip()
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", non_ancestor, "HEAD"],
        cwd=repository,
        check=False,
    )
    assert ancestry.returncode == 1
    monkeypatch.setattr(runner, "TASK11_SPEC_LOCK_COMMIT", non_ancestor)
    with pytest.raises(
        RuntimeError, match="Task 11 Spec Lock commit is not an ancestor"
    ):
        assert_clean_committed_task11_worktree()


@pytest.mark.parametrize(
    ("path", "message"),
    [
        (TASK11_SPEC_PATH, "locked Task 11 Spec blob mismatch"),
        (
            TASK11_SPEC_LOCK_RECORD_PATH,
            "locked Task 11 Spec Lock Record blob mismatch",
        ),
    ],
)
def test_guard_rejects_committed_locked_blob_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    path: str,
    message: str,
):
    """A committed changed lock artifact must invalidate production provenance."""
    repository = _init_guard_repo(tmp_path, monkeypatch)
    changed_path = repository / path
    changed_path.write_text("changed locked bytes\n")
    _commit(repository, "change locked artifact")

    with pytest.raises(RuntimeError, match=message):
        assert_clean_committed_task11_worktree()


def test_guard_rejects_invalid_or_absent_head_sha(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """An invalid HEAD value cannot be recorded as output provenance."""
    repository = _init_guard_repo(tmp_path, monkeypatch)
    import research.run_task11_hypothesis_registration as runner

    real_git = runner._git

    def git_with_invalid_head(*args: str, capture_output: bool = False):
        result = real_git(*args, capture_output=capture_output)
        if args == ("rev-parse", "HEAD"):
            return subprocess.CompletedProcess(
                result.args, 0, stdout="A" * 40 + "\n", stderr=""
            )
        return result

    monkeypatch.setattr(runner, "_git", git_with_invalid_head)
    with pytest.raises(RuntimeError, match="invalid HEAD SHA"):
        assert_clean_committed_task11_worktree()

    monkeypatch.setattr(runner, "_REPOSITORY_ROOT", tmp_path / "empty-repository")
    (tmp_path / "empty-repository").mkdir()
    _git(tmp_path / "empty-repository", "init")
    monkeypatch.setattr(runner, "_git", real_git)
    with pytest.raises(RuntimeError, match="invalid HEAD SHA"):
        assert_clean_committed_task11_worktree()


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
            assert info.compress_type == zipfile.ZIP_DEFLATED
            assert info.create_system == 3
            assert info.external_attr >> 16 == 0o100644
            assert info.extra == b""
            assert archive.read(info) == first_artifacts[info.filename]


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
