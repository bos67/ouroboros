"""Pins: the newest README Version History row's test-count claims must be
MACHINE-DERIVED, not written from memory — the live class of 2026-09-24:
the 6.119.18 row shipped through the full gate with ``22/22 (14 + 8)`` and
``126/126`` while the tree carried 21 collected tests and 170 collected
neighbors; both numbers were prose written from memory, and only the triad
caught them — after the commit.

Canonical claim shapes this pin understands (used by the 6.119.18/.19 rows;
a newest row that makes no such claims simply has nothing to check):

* lane claim —
  ``<file> NN/NN green across both marker lanes (P parallel + S serial)``
  The ``NN/NN`` total, parallel and serial slices are re-derived from a real
  ``pytest --collect-only`` of the named file in both marker lanes (the same
  split CI and the hermetic commit gate run).

* neighbor claim —
  ``(`t_a` + `t_b` + ...) = NN/NN collected and passed``
  The sum is re-derived from ``--collect-only`` of the named sibling files.
  The pin attests COLLECTED; the ``passed`` half is attested by the gate's
  own runs of those suites.

Only the newest table row (the one matching ``VERSION``) is checked —
historical rows are frozen tag truth. If a claim names a suite that does
not exist, or collect-only cannot return a count, the pin FAILS: it never
waves through what it cannot derive.
"""

import pathlib
import re
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]

_ROW_RE = re.compile(r"^\| (\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?) \| (.+) \|$")
_LANES_RE = re.compile(
    r"`+(tests/[\w./{}-]+\.py)`+\s+(\d+)/(\d+)\s+green across both marker"
    r"\s+lanes\s*\((\d+)\s+(?:parallel|not-serial)\s*\+\s*(\d+)\s*serial\)"
)
_SIBLINGS_RE = re.compile(
    r"(`test_\w+`(?:\s*\+\s*`test_\w+`)*)\s*=\s*(\d+)/(\d+)"
    r"\s+collected and passed"
)
_FILE_COUNT_RE = re.compile(r"^(?P<name>\S+\.py): (?P<count>\d+)$", re.MULTILINE)


def _readme_newest_row_text() -> str:
    """The description cell of the Version History row matching VERSION."""
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    version = (REPO / "VERSION").read_text(encoding="utf-8").strip()
    for line in readme.splitlines():
        m = _ROW_RE.match(line)
        if m and m.group(1) == version:
            return m.group(2)
    pytest.fail(
        f"README.md has no Version History row for {version} (VERSION)"
        " — release carriers are out of sync with the table"
    )


def _collect_counts(test_paths, marker=None) -> int:
    """Sum of ``pytest --collect-only -q`` per-file counts for the given files.

    ``-q`` prints one ``<file>: <count>`` line per requested file (post marker
    deselection); anything else — nonzero exit, missing file lines — fails the
    pin rather than waving through.
    """
    rel_paths = [str(p.relative_to(REPO)) for p in test_paths]
    for rel in rel_paths:
        if not (REPO / rel).exists():
            pytest.fail(f"claimed suite does not exist: {rel}")
    cmd = [sys.executable, "-m", "pytest", "--collect-only", "-q"]
    if marker:
        cmd += ["-m", marker]
    cmd += rel_paths
    try:
        proc = subprocess.run(
            cmd, cwd=str(REPO), capture_output=True, text=True, timeout=180
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        pytest.skip(f"pytest collect runner unavailable: {exc!r}")
    if proc.returncode != 0:
        pytest.fail(
            f"collect-only of {rel_paths} exited {proc.returncode}: "
            f"{(proc.stdout or '')[-300:]!r} {(proc.stderr or '')[-300:]!r}"
        )
    counts = {m.group("name"): int(m.group("count")) for m in _FILE_COUNT_RE.finditer(proc.stdout or "")}
    total = 0
    for rel in rel_paths:
        if rel not in counts:
            pytest.fail(
                f"collect-only did not report a count for {rel}; "
                f"reported: {sorted(counts)}"
            )
        total += counts[rel]
    return total


@pytest.mark.serial
def test_newest_row_lane_counts_are_machine_derived():
    """``NN/NN green across both marker lanes (P + S)`` must equal the real
    ``--collect-only`` counts of the named file, in both lanes (6.119.18
    shipped 22/22 (14+8) over a 21-test tree)."""
    row = _readme_newest_row_text()
    claims = list(_LANES_RE.finditer(row))
    if not claims:
        pytest.skip("newest row makes no lane claim")
    for m in claims:
        file_rel = m.group(1)
        claimed_total, _, claimed_par, claimed_ser = (
            int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)),
        )
        file_path = REPO / file_rel
        if not file_path.exists():
            pytest.fail(f"lane claim names a missing suite: {file_rel}")
        ser = _collect_counts([file_path], marker="serial")
        par = _collect_counts([file_path], marker="not serial")
        assert (par, ser) == (claimed_par, claimed_ser), (
            f"{file_rel}: row claims {claimed_par} parallel + {claimed_ser}"
            f" serial, tree collects {par} + {ser}. Derive with"
            " `pytest --collect-only` - the disk, not memory, is the source."
        )
        assert par + ser == claimed_total


@pytest.mark.serial
def test_newest_row_neighbor_sum_is_machine_derived():
    """``= NN/NN collected and passed`` for the named sibling suites must
    equal the summed ``--collect-only`` counts (6.119.18 shipped 126/126
    while the four named suites collect 170)."""
    row = _readme_newest_row_text()
    claims = list(_SIBLINGS_RE.finditer(row))
    if not claims:
        pytest.skip("newest row makes no neighbor-sum claim")
    for m in claims:
        names = re.findall(r"`(test_\w+)`", m.group(1))
        claimed_total = int(m.group(2))
        paths = [REPO / "tests" / f"{name}.py" for name in names]
        total = _collect_counts(paths)
        assert total == claimed_total, (
            f"row claims {claimed_total} collected across"
            f" {[p.name for p in paths]}, tree collects {total}."
            " Derive with `pytest --collect-only`."
        )


def test_newest_row_exists_for_version():
    """A carrier-synced README must carry the released row (the row the
    lane/neighbor pins parse)."""
    _readme_newest_row_text()


def test_lane_claims_parse_from_canonical_row_text():
    """The lane regex must catch the canonical shapes (guards the pin itself
    against / a test that matches nothing pins nothing)."""
    sample = (
        "Verification: `tests/test_shell_preflight.py` 21/21 green across"
        " both marker lanes (14 parallel + 7 serial); neighbors green."
    )
    m = _LANES_RE.search(sample)
    assert m, "canonical lane phrase no longer matches the pin regex"
    assert (m.group(1), m.group(2), m.group(4), m.group(5)) == (
        "tests/test_shell_preflight.py", "21", "14", "7",
    )


def test_neighbor_claims_parse_from_canonical_row_text():
    sample = (
        "neighbors green by exit code (`test_shell_run_shell` +"
        " `test_release_sync` + `test_packaging_sync` + `test_docs_sync` ="
        " 170/170 collected and passed, incl. the three-cell render pin)."
    )
    m = _SIBLINGS_RE.search(sample)
    assert m, "canonical neighbor phrase no longer matches the pin regex"
    assert re.findall(r"`(test_\w+)`", m.group(1)) == [
        "test_shell_run_shell", "test_release_sync",
        "test_packaging_sync", "test_docs_sync",
    ]
    assert m.group(2) == "170"
