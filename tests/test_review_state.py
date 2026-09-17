"""Regression tests for repo-scoped advisory invalidation (crd-0001 reopen class).

The fix narrows ``invalidate_advisory_after_mutation`` to real git repositories:
a mutation outside any repo (task_drive scratch, /tmp, runtime data) must keep
freshness, and a path that lost its leading slash (glued onto the mutation root)
must not inherit the root's repo attribution.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest

# serial: _make_repo spawns real `git init/add/commit` subprocesses (real OS
# processes) — sanctioned parallel-safety criterion (DEVELOPMENT.md/CHECKLISTS.md).
pytestmark = pytest.mark.serial

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ouroboros.review_state import (  # noqa: E402
    AdvisoryReviewState,
    AdvisoryRunRecord,
    _discovered_repo_dir,
    _resolve_mutation_repo_scope,
    invalidate_advisory_after_mutation,
)


def _make_repo(tmp_path: pathlib.Path, name: str) -> pathlib.Path:
    repo = tmp_path / name
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    (repo / ".gitignore").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    return repo


def _fresh_run(repo: pathlib.Path) -> AdvisoryRunRecord:
    return AdvisoryRunRecord(
        snapshot_hash="h" + str(abs(hash(str(repo))))[:12],
        commit_message="m",
        status="fresh",
        ts="2026-09-17T00:00:00+00:00",
        repo_key=str(repo),
    )


# ---------------------------------------------------------------------------
# _discovered_repo_dir
# ---------------------------------------------------------------------------


def test_discovered_repo_dir_finds_repo(tmp_path):
    repo = _make_repo(tmp_path, "r1")
    assert _discovered_repo_dir(repo / "sub" / "file.py") == repo


def test_discovered_repo_dir_returns_none_outside_repo(tmp_path):
    outside = tmp_path / "scratch"
    outside.mkdir()
    assert _discovered_repo_dir(outside / "f.txt") is None


# ---------------------------------------------------------------------------
# _resolve_mutation_repo_scope
# ---------------------------------------------------------------------------


def test_scope_relative_path_under_repo_root_attributes_repo(tmp_path):
    repo = _make_repo(tmp_path, "r1")
    # Real callers (edit_ops) pass relpaths of files they JUST mutated — the
    # file exists on disk by then; a nonexistent path contributes nothing
    # (that is exactly the anti-glued-path guard).
    target = repo / "src" / "a.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("x", encoding="utf-8")
    keys, known = _resolve_mutation_repo_scope(repo, ["src/a.py"])
    assert known is True
    assert keys == [str(repo)]


def test_scope_absolute_path_in_repo_attributes_repo(tmp_path):
    repo = _make_repo(tmp_path, "r1")
    keys, known = _resolve_mutation_repo_scope(tmp_path, [str(repo / "f.py")])
    assert known is True
    assert keys == [str(repo)]


def test_scope_task_drive_path_keeps_repo_fresh(tmp_path):
    """The crd-0001 incident shape: scratch outside any repo must not attribute."""
    repo = _make_repo(tmp_path, "r1")
    scratch = tmp_path / "scratch" / "f.py"
    scratch.parent.mkdir(parents=True, exist_ok=True)
    scratch.write_text("x", encoding="utf-8")
    keys, known = _resolve_mutation_repo_scope(tmp_path, [str(scratch)])
    assert keys == []
    assert known is True
    assert str(repo) not in keys


def test_scope_absolute_path_that_lost_leading_slash_not_inherited(tmp_path):
    """Absolute path glued onto mutation root (missing slash): the joined path
    does not exist under the root — zero locatable evidence = UNKNOWN scope,
    conservative stale-everything (never the root's repo attribution)."""
    repo = _make_repo(tmp_path, "r1")
    glued = repo / "home" / "graphrag" / "Ouroboros" / "data" / "task_drives" / "t" / "x.py"
    keys, known = _resolve_mutation_repo_scope(repo, [str(glued)])
    assert known is False
    assert keys == []


def test_scope_mixed_repos_and_scratch_lists_both_repos(tmp_path):
    repo_a = _make_repo(tmp_path, "ra")
    repo_b = _make_repo(tmp_path, "rb")
    keys, known = _resolve_mutation_repo_scope(
        tmp_path,
        [str(repo_a / "a.py"), str(tmp_path / "s.txt"), str(repo_b / "b.py")],
    )
    assert known is True
    assert sorted(keys) == sorted([str(repo_a), str(repo_b)])


def test_scope_no_root_no_paths_is_unknown(tmp_path):
    keys, known = _resolve_mutation_repo_scope(None, [])
    assert known is False
    assert keys == []


def test_scope_no_root_unlocatable_paths_is_unknown(tmp_path):
    """No root + zero locatable paths = UNKNOWN scope (stale everything),
    not 'proven outside any repo' (advisory finding, 6.118.1)."""
    keys, known = _resolve_mutation_repo_scope(None, ["missing/path/f.py"])
    assert known is False
    assert keys == []


# ---------------------------------------------------------------------------
# invalidate_advisory_after_mutation (end-to-end through durable state)
# ---------------------------------------------------------------------------


def _prepare_state(drive_root: pathlib.Path, repo: pathlib.Path) -> None:
    from ouroboros.review_state import update_state

    def _seed(state: AdvisoryReviewState) -> None:
        state.advisory_runs.append(_fresh_run(repo))

    update_state(drive_root, _seed)


def test_outside_repo_mutation_keeps_freshness(tmp_path):
    """The live crd-0001 shape: a WRITTEN scratch file outside any repo (real
    path, exists on disk) must keep the repo's advisory freshness."""
    repo = _make_repo(tmp_path, "r1")
    drive_root = tmp_path / "drive"
    drive_root.mkdir()
    _prepare_state(drive_root, repo)
    scratch = tmp_path / "scratch" / "nopipe.py"
    scratch.parent.mkdir(parents=True, exist_ok=True)
    scratch.write_text("x", encoding="utf-8")

    invalidate_advisory_after_mutation(
        drive_root,
        mutation_root=tmp_path,
        changed_paths=[str(tmp_path / "scratch" / "nopipe.py")],
        source_tool="write_file",
    )

    from ouroboros.review_state import load_state

    state = load_state(drive_root)
    runs = state.filter_advisory_runs(repo_key=str(repo))
    assert runs and runs[-1].status == "fresh"


def test_in_repo_mutation_stales_repo(tmp_path):
    repo = _make_repo(tmp_path, "r1")
    drive_root = tmp_path / "drive"
    drive_root.mkdir()
    _prepare_state(drive_root, repo)
    target = repo / "src" / "a.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("x", encoding="utf-8")

    invalidate_advisory_after_mutation(
        drive_root,
        mutation_root=repo,
        changed_paths=["src/a.py"],
        source_tool="edit_text",
    )

    from ouroboros.review_state import load_state

    state = load_state(drive_root)
    runs = state.filter_advisory_runs(repo_key=str(repo))
    assert runs and runs[-1].status == "stale"


def test_unknown_scope_stales_everything(tmp_path):
    repo = _make_repo(tmp_path, "r1")
    drive_root = tmp_path / "drive"
    drive_root.mkdir()
    _prepare_state(drive_root, repo)

    invalidate_advisory_after_mutation(
        drive_root,
        mutation_root=None,
        changed_paths=[],
        source_tool="mystery_tool",
    )

    invalidate_advisory_after_mutation(
        drive_root,
        mutation_root=None,
        changed_paths=["missing/path/f.py"],
        source_tool="mystery_tool",
    )

    from ouroboros.review_state import load_state

    state = load_state(drive_root)
    runs = state.filter_advisory_runs(repo_key=str(repo))
    assert runs and runs[-1].status == "stale"


def test_outside_repo_mutation_does_not_touch_last_stale_fields(tmp_path):
    """The debt observation (crd-0001) derives from last_stale_from_edit_ts;
    keeping freshness must also keep those fields empty. The scratch file is
    WRITTEN (locatable) — the live incident shape."""
    repo = _make_repo(tmp_path, "r1")
    drive_root = tmp_path / "drive"
    drive_root.mkdir()
    _prepare_state(drive_root, repo)
    scratch = tmp_path / "data" / "task_drives" / "x" / "nopipe.py"
    scratch.parent.mkdir(parents=True, exist_ok=True)
    scratch.write_text("x", encoding="utf-8")

    invalidate_advisory_after_mutation(
        drive_root,
        mutation_root=tmp_path,
        changed_paths=[str(scratch)],
        source_tool="write_file",
    )

    from ouroboros.review_state import load_state

    state = load_state(drive_root)
    assert state.last_stale_from_edit_ts == ""
    assert state.last_stale_reason == ""
    assert state.last_stale_repo_key == ""


def test_root_only_call_with_repo_root_stales_repo(tmp_path):
    """services.py path: mutation_root=<repo>, no changed_paths."""
    repo = _make_repo(tmp_path, "r1")
    drive_root = tmp_path / "drive"
    drive_root.mkdir()
    _prepare_state(drive_root, repo)

    invalidate_advisory_after_mutation(
        drive_root,
        mutation_root=repo,
        changed_paths=[],
        source_tool="start_service",
    )

    from ouroboros.review_state import load_state

    state = load_state(drive_root)
    runs = state.filter_advisory_runs(repo_key=str(repo))
    assert runs and runs[-1].status == "stale"


def test_repo_root_all_unlocatable_paths_stale_everything(tmp_path):
    """Paths supplied but none locatable = UNKNOWN scope even under a repo
    root: unusable evidence cannot prove 'outside any repo' (advisory
    finding wave 2, 6.118.1)."""
    repo = _make_repo(tmp_path, "r1")
    drive_root = tmp_path / "drive"
    drive_root.mkdir()
    _prepare_state(drive_root, repo)

    invalidate_advisory_after_mutation(
        drive_root,
        mutation_root=repo,
        changed_paths=["gone/missing/f.py"],
        source_tool="mystery_tool",
    )

    from ouroboros.review_state import load_state

    state = load_state(drive_root)
    runs = state.filter_advisory_runs(repo_key=str(repo))
    assert runs and runs[-1].status == "stale"


def test_service_placeholder_path_does_not_stale_unrelated_repo(tmp_path):
    """services.py passes changed_paths=['<service:name>'] with mutation_root=workdir;
    when the workdir is NOT a repo, the placeholder must not invent attribution."""
    repo = _make_repo(tmp_path, "r1")
    drive_root = tmp_path / "drive"
    drive_root.mkdir()
    _prepare_state(drive_root, repo)
    workdir = tmp_path / "svc_wd"
    workdir.mkdir()

    invalidate_advisory_after_mutation(
        drive_root,
        mutation_root=workdir,
        changed_paths=["<service:gate>"],
        source_tool="start_service",
    )

    from ouroboros.review_state import load_state

    state = load_state(drive_root)
    runs = state.filter_advisory_runs(repo_key=str(repo))
    assert runs and runs[-1].status == "fresh"


def test_git_ops_discovered_repo_dir_none_for_drive_root_of_bare_drive(tmp_path):
    outside = tmp_path / "plain"
    outside.mkdir()
    (outside / "f.txt").write_text("x", encoding="utf-8")
    assert _discovered_repo_dir(outside / "f.txt") is None
    assert _discovered_repo_dir(outside) is None
