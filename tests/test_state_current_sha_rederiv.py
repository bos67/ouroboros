"""Regression tests: state current_sha re-derivation at ordinary start (ibl-current-sha-deriv).

current_sha is written only by update/checkout paths; a manual commit plus a plain
restart used to leave it stale, which fed /api/state (ws.js reload-on-SHA) and the
worker spawn SHA verification. rederive_current_sha_from_repo() heals it at startup
when no update-intent owns the transition.
"""
from __future__ import annotations

import pathlib
import subprocess

import pytest

from supervisor import git_ops, state


def _git(repo: pathlib.Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True, capture_output=True, text=True,
    )
    return proc.stdout.strip()


def _make_repo(tmp_path: pathlib.Path) -> pathlib.Path:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "test")
    (repo / "f.txt").write_text("one", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "one")
    return repo


def _head(repo: pathlib.Path) -> str:
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture()
def bound(tmp_path):
    """Bind supervisor.state to a disposable drive (mirrors conftest's root binding)."""
    (tmp_path / "state").mkdir(parents=True, exist_ok=True)
    (tmp_path / "locks").mkdir(parents=True, exist_ok=True)
    state.init(tmp_path, 10.0)
    return tmp_path


def test_stale_sha_is_rederived_from_head(bound):
    repo = _make_repo(bound)
    saved = git_ops.REPO_DIR
    git_ops.REPO_DIR = repo
    try:
        state.update_state(lambda s: s.__setitem__("current_sha", "0" * 40))
        head = _head(repo)
        result = state.rederive_current_sha_from_repo(repo)
        assert result == {"old": "0" * 40, "new": head}
        assert state.load_state()["current_sha"] == head
    finally:
        git_ops.REPO_DIR = saved


def test_no_write_when_sha_already_current(bound):
    repo = _make_repo(bound)
    saved = git_ops.REPO_DIR
    git_ops.REPO_DIR = repo
    try:
        head = _head(repo)
        state.update_state(lambda s: s.__setitem__("current_sha", head))
        assert state.rederive_current_sha_from_repo(repo) is None
        assert state.load_state()["current_sha"] == head
    finally:
        git_ops.REPO_DIR = saved


def test_update_intent_blocks_rederivation(bound):
    repo = _make_repo(bound)
    saved = git_ops.REPO_DIR
    git_ops.REPO_DIR = repo
    try:
        from supervisor.git_ops import _clear_update_intent, _write_update_intent

        state.update_state(lambda s: s.__setitem__("current_sha", "0" * 40))
        # An active managed update/checkout intent owns the transition: the healer
        # must not touch the record the intent path is about to rewrite.
        _write_update_intent({"branch": "ouroboros", "target_sha": "a" * 40})
        assert state.rederive_current_sha_from_repo(repo) is None
        assert state.load_state()["current_sha"] == "0" * 40
        _clear_update_intent()
    finally:
        git_ops.REPO_DIR = saved


def test_non_repo_directory_is_ignored(bound):
    plain = bound / "plain"
    plain.mkdir()
    saved = git_ops.REPO_DIR
    git_ops.REPO_DIR = plain
    try:
        state.update_state(lambda s: s.__setitem__("current_sha", "0" * 40))
        # git rev-parse fails here: the healer must fail soft, not crash startup.
        assert state.rederive_current_sha_from_repo(plain) is None
        assert state.load_state()["current_sha"] == "0" * 40
    finally:
        git_ops.REPO_DIR = saved


def test_empty_sha_is_a_valid_heal(bound):
    repo = _make_repo(bound)
    saved = git_ops.REPO_DIR
    git_ops.REPO_DIR = repo
    try:
        head = _head(repo)
        st = state.load_state()
        st["current_sha"] = None
        state.save_state(st)
        assert state.rederive_current_sha_from_repo(repo) == {"old": "", "new": head}
        assert state.load_state()["current_sha"] == head
    finally:
        git_ops.REPO_DIR = saved
