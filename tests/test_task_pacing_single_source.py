"""Single-source pin: the periodic self-check reminder text (advisory closure).

The 2026-09-22 triad advisory claimed `build_self_check_reminder` in
``ouroboros/task_pacing.py`` duplicated an f-string scaffold that also
lived in ``ouroboros/loop.py`` — describing the PRE-migration state. The
6.119.12 shrink-authority release moved the scaffold wholesale; disk today
holds the reminder text exactly once. This pin keeps it that way: the
distinguishing sentence may not appear in any OTHER module of the package,
so a future regresssion (re-duplicating the scaffold) fails this test
instead of waiting for the next triad wave.
"""
import pathlib

import ouroboros

REPO = pathlib.Path(ouroboros.__file__).resolve().parent
_SENTINEL = "periodic self-check, not a command to stop"


def test_reminder_sentence_lives_exactly_once_in_package():
    hits = []
    for path in REPO.rglob("*.py"):
        if path.name == __file__.rsplit("/", 1)[-1]:
            continue  # do not count this test's own docstring
        try:
            if _SENTINEL in path.read_text(encoding="utf-8", errors="replace"):
                hits.append(path.relative_to(REPO))
        except OSError:
            continue
    assert hits == [pathlib.Path("task_pacing.py")], (
        f"self-check reminder text must live ONLY in task_pacing.py; found in: {hits}"
    )


def test_loop_delegates_instead_of_rebuilding():
    src = (REPO / "loop.py").read_text(encoding="utf-8")
    assert "task_pacing.build_self_check_reminder(" in src
    assert "This is a periodic self-check" not in src
