"""Nearest-match recovery hints for the edit family (6.118.2).

Pins the measured stale-anchor recovery rail: an exact old_str miss or a missing
path now carries the closest real fragments/paths in the SAME typed refusal
(still atomic, still nothing written). The hint must never appear on a
count-mismatch (occurrences > 0) and never change refusal/atomicity semantics.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ouroboros.tools import edit_ops
from ouroboros.tools.core import _str_match_replace
from ouroboros.tools.edit_support import nearest_fragment_hints, suggest_similar_paths


SAMPLE = "\n".join([
    "def ddd(x):",
    "    return x * 3",
    "",
    "def other(x):",
    "    return ddd(x)",
])


# ---------------------------------------------------------------------------
# nearest_fragment_hints
# ---------------------------------------------------------------------------

def test_hint_returns_empty_when_nothing_is_close():
    text = "alpha\nbeta\ngamma\n"
    assert nearest_fragment_hints(text, "completely unrelated content here\n") == ""


def test_hint_finds_close_fragment_with_line_and_ratio():
    text = SAMPLE + "\n"
    hint = nearest_fragment_hints(text, "def ddd(x):\n    return x * 4\n")
    assert hint != ""
    assert "~line 1" in hint
    assert "%" in hint


def test_hint_scan_is_bounded_to_the_cap():
    """The scan is cost-bounded: a near-match ONLY beyond the 5000-line cap
    must not be found (and the cap must not crash the search)."""
    text = "line\n" * 5000 + "def ddd(x):\n    return x * 3\n"
    hint = nearest_fragment_hints(text, "def ddd(x):\n    return x * 4\n")
    assert hint == ""


# ---------------------------------------------------------------------------
# _str_match_replace (shared repo + data-plane editor seam)
# ---------------------------------------------------------------------------

def test_str_match_replace_miss_carries_hint():
    text = SAMPLE + "\n"
    new_text, err = _str_match_replace(
        text, "def ddd(x):\n    return x * 4\n", "NEW", "sample.py", "STR_REPLACE_ERROR"
    )
    assert new_text is None
    assert "old_str not found in sample.py" in err
    assert "Nearest matching fragments:" in err
    assert "~line 1" in err


def test_str_match_replace_count_gt1_does_not_gain_hints():
    text = SAMPLE + "\n" + SAMPLE
    new_text, err = _str_match_replace(text, "def ddd(x):", "NEW", "sample.py", "EDIT_TEXT_ERROR")
    assert new_text is None
    assert "found 2 times" in err
    assert "Nearest matching fragments:" not in err


# ---------------------------------------------------------------------------
# edit_batch misses
# ---------------------------------------------------------------------------

def _ws_ctx(tmp_path):
    from ouroboros.tools.registry import ToolContext

    return ToolContext(
        repo_dir=tmp_path,
        drive_root=tmp_path / "data",
    )


@pytest.fixture()
def ws(tmp_path):
    ctx = _ws_ctx(tmp_path)
    ctx.repo_dir.mkdir(parents=True, exist_ok=True)
    (ctx.repo_dir / "s.py").write_text(SAMPLE + "\n", encoding="utf-8")
    return ctx


def test_edit_batch_zero_occurrence_miss_carries_hint(ws):
    result = edit_ops._edit_batch(
        ws,
        [{"path": "s.py", "old_str": "def ddd(x):\n    return x * 4\n", "new_str": "NEW"}],
    )
    assert "EDIT_BATCH_ERROR" in result
    assert "occurs 0 time(s)" in result
    assert "Nearest matching fragments:" in result


def test_edit_batch_count_mismatch_does_not_gain_hint(ws):
    result = edit_ops._edit_batch(
        ws,
        [{"path": "s.py", "old_str": "def ddd(x):", "new_str": "NEW", "count": 2}],
    )
    assert "occurs 1 time(s), expected 2" in result
    assert "Nearest matching fragments:" not in result


def test_edit_batch_missing_file_suggests_similar_paths(ws):
    (ws.repo_dir / "service.py").write_text("x = 1\n", encoding="utf-8")
    result = edit_ops._edit_batch(
        ws,
        [{"path": "servce.py", "old_str": "a", "new_str": "b"}],
    )
    assert "EDIT_BATCH_ERROR" in result
    assert "file not found" in result
    assert "Nearest existing paths" in result
    assert "service.py" in result


def test_edit_batch_missing_file_without_neighbors_stays_plain(ws):
    result = edit_ops._edit_batch(
        ws,
        [{"path": "totally_absent_zz.py", "old_str": "a", "new_str": "b"}],
    )
    assert "EDIT_BATCH_ERROR" in result
    assert "file not found" in result
    assert "Nearest existing paths" not in result


# ---------------------------------------------------------------------------
# Absolute-glue guard in the target resolver
# ---------------------------------------------------------------------------

def test_glued_absolute_path_resolves_to_the_real_child(tmp_path):
    from ouroboros.tool_access import build_resolved_resource_binding
    from ouroboros.tools.registry import ToolContext

    repo = tmp_path / "repo"
    data = tmp_path / "data"
    repo.mkdir()
    data.mkdir()
    (repo / "real.py").write_text("x = 1\n", encoding="utf-8")
    ctx = ToolContext(repo_dir=repo, drive_root=data)

    binding = build_resolved_resource_binding(
        ctx, root="system_repo", operation="edit",
        path=f"{repo}/real.py",
    )
    assert binding.target_path == (repo / "real.py").resolve()


def test_case_variant_absolute_path_strips_to_the_real_child(tmp_path):
    """The guard must be pathlib-based, not string-based (P6 cross_platform).

    A case-variant spelling of the root (routine on Windows) must still strip
    to the real child instead of re-nesting: the old str-comparison guard
    missed it exactly like it missed forward-vs-backslash separators."""
    from ouroboros.tool_access import build_resolved_resource_binding
    from ouroboros.tools.registry import ToolContext

    repo = tmp_path / "repo"
    data = tmp_path / "data"
    repo.mkdir()
    data.mkdir()
    (repo / "real.py").write_text("x = 1\n", encoding="utf-8")
    ctx = ToolContext(repo_dir=repo, drive_root=data)

    # Deliberate case variant of the root in the input path.
    case_variant_root = pathlib.Path(str(repo).replace("repo", "Repo"))
    assert case_variant_root != repo  # POSIX: different text, same intent
    binding = build_resolved_resource_binding(
        ctx, root="system_repo", operation="edit",
        path=f"{case_variant_root}/real.py",
    )
    assert binding.target_path == (repo / "real.py").resolve()


def test_hint_preview_masks_secret_shaped_content(ws):
    """Egress seam: hint previews ride mask_secret_bytes like every other egress."""
    secret_line = "token = ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8s9T0"  # 40+ opaque run
    (ws.repo_dir / "creds.py").write_text(secret_line + "\n", encoding="utf-8")
    from ouroboros.tools.edit_support import nearest_fragment_hints
    # Near-miss old_str (last 3 chars dropped) guarantees the ratio clears the
    # closeness floor, so the hint — and its masked preview — definitely render.
    hint = nearest_fragment_hints(
        (ws.repo_dir / "creds.py").read_text(encoding="utf-8"),
        secret_line[:-3],
    )
    assert hint, "near-miss old_str must render a hint"
    assert "a1B2c3D4" not in hint
    assert "***" in hint
