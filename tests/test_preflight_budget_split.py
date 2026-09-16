"""Unit tests for the per-phase preflight budget split (v6.117.0).

The gate's shared 900s budget could not fit the parallel `not serial` pass on
the 2-core reference box: the parallel pass was killed at 888s/900s (55% done,
zero red tests) and the serial pass never started — three releases went to
manual handoff over it. This file is the SSOT of the budget contract: pure
slice arithmetic, the typed phase-expiry diagnoses, and the orchestration pins
of who receives which slice (fixtures shared with test_preflight_runner.py
live here so both contracts stay in one place).
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import textwrap
import time

import pytest


def test_default_total_is_2700_seconds():
    """The shipped default must fit the measured suite: the parallel pass alone
    consumed 888s for 55% (~1600s full) on the reference box, and the serial
    pass still needs to run after it. 2700 leaves ~200s of margin on top of the
    node cap, the 1806s parallel slice and the 774s serial remainder."""
    from ouroboros.preflight_runner import _DEFAULT_PREFLIGHT_TIMEOUT_SEC

    assert _DEFAULT_PREFLIGHT_TIMEOUT_SEC == 2700
    assert _DEFAULT_PREFLIGHT_TIMEOUT_SEC >= 180, "the smoke floor of the old contract still holds"


@pytest.mark.parametrize(
    ("total", "expected"),
    [
        (2700.0, (120.0, 2064.0, 516.0)),
        (1800.0, (90.0, 1368.0, 342.0)),
        (900.0, (45.0, 684.0, 171.0)),
    ],
)
def test_phase_budgets_are_exact_fractions_of_the_total(total, expected):
    """node = min(120, 5% of T); parallel = 80% of (T - node); serial = the
    exact unrounded remainder. No rounding anywhere: the runner passes floats
    straight through so the whole gate stays bounded by the resolved total."""
    from ouroboros.preflight_runner import _preflight_phase_budgets

    assert _preflight_phase_budgets(total) == pytest.approx(expected)


@pytest.mark.parametrize("total", [120.0, 300.0, 900.0, 2700.0, 5137.0])
def test_phase_budget_slices_sum_to_the_total(total):
    """The serial reservation is DEFINED as the remainder, so the three slices
    always reassemble the resolved total — the gate never advertises more or
    less budget than it owns."""
    from ouroboros.preflight_runner import _preflight_phase_budgets

    node, parallel, serial = _preflight_phase_budgets(total)
    assert node + parallel + serial == pytest.approx(total)
    assert 0 < node < parallel, "node is the smallest ceiling, parallel the largest"


def test_node_slice_caps_at_120_seconds_even_for_huge_totals():
    """A 5%-of-T node slice must never grow with the total: an operator who
    raises OUROBOROS_PREFLIGHT_TIMEOUT_SEC gives the time to pytest phases, not
    to the browser-module lane."""
    from ouroboros.preflight_runner import _preflight_phase_budgets

    node, _, _ = _preflight_phase_budgets(100_000.0)
    assert node == pytest.approx(120.0)


def _git(repo: pathlib.Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=str(repo), check=True, capture_output=True, text=True)


def _commit_all(repo: pathlib.Path) -> None:
    _git(repo, "add", ".")
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "init"],
        cwd=str(repo), check=True, capture_output=True, text=True,
    )


def _make_repo(tmp_path: pathlib.Path, files: dict[str, str]) -> pathlib.Path:
    """Init a tiny git repo whose `tests/` holds only the given probe files."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "checkout", "-b", "ouroboros")
    (repo / "pytest.ini").write_text(
        "[pytest]\nmarkers =\n    serial: real-process/port/global-state test; runs in the serial pass\n",
        encoding="utf-8",
    )
    (repo / "tests").mkdir()
    for rel, body in files.items():
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(textwrap.dedent(body), encoding="utf-8")
    _commit_all(repo)
    return repo


@pytest.fixture
def two_pass_env(monkeypatch):
    """Deterministic env for the two-pass tests (shared contract with
    test_preflight_runner.py)."""
    monkeypatch.delenv("OUROBOROS_PREFLIGHT_TIMEOUT_SEC", raising=False)
    monkeypatch.delenv("OUROBOROS_PREFLIGHT_SERIAL", raising=False)
    monkeypatch.setenv("OUROBOROS_PREFLIGHT_TEST_WORKERS", "2")
    monkeypatch.setenv("PYTEST_XDIST_AUTO_NUM_WORKERS", "1")
    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
    monkeypatch.delenv("PYTEST_XDIST_TESTRUNUID", raising=False)


@pytest.fixture
def stub_passes(monkeypatch):
    """Replace the pytest spawn with a recorder (shared contract with
    test_preflight_runner.py); the recorded `timeout` argument is what the
    slice assertions below pin."""
    from ouroboros import platform_layer, preflight_runner

    events: list[tuple] = []
    monkeypatch.setattr(platform_layer, "kill_processes_referencing", lambda marker: events.append(("sweep", marker)))
    monkeypatch.setattr(preflight_runner, "_verify_preflight_plugins", lambda *a, **k: [])
    monkeypatch.setattr(preflight_runner, "_observed_worker_ids", lambda *a, **k: {"gw0", "gw1"})

    def _install(results):
        pending = list(results)

        def _fake_pass(agent_python, worktree, temp_root, args, timeout):
            events.append(("pass", list(args), timeout))
            handler = pending.pop(0)
            result = tuple(handler() if callable(handler) else handler)
            return result if len(result) == 3 else (result[0], result[1], "")

        monkeypatch.setattr(preflight_runner, "_execute_pytest_pass", _fake_pass)
        return events

    return _install


def test_the_parallel_pass_runs_on_its_own_phase_slice(tmp_path, two_pass_env, stub_passes):
    """v6.117.0: the parallel pass runs on its phase slice (80% of T after the
    node carve), NOT on the whole remainder. The old shared-budget loop spent
    the serial pass's share inside the parallel one and killed it at 888s/900s
    (2026-09-14, 55% complete, serial never started) — this pins the split: a
    pass that exhausts its slice fails fast in ITS OWN pass with the slice
    named, and pass 2 never spawns."""
    from ouroboros.preflight_runner import run_hermetic_pytest

    events = stub_passes([(None, "partial output before the kill"), (0, "")])
    repo = _make_repo(tmp_path, {"tests/test_plain.py": "def test_ok():\n    assert True\n"})

    result = run_hermetic_pytest(repo, timeout=1)

    assert result is not None
    assert "parallel pass" in result, result
    assert "phase budget" in result, result
    assert "of total 1 seconds" in result, result
    # Fixture repos carry no web/tests, so the node carve is dormant but still
    # subtracted: node slice = 0.05 of T, parallel = 0.80 * (T - node).
    assert events[0][2] == pytest.approx(0.8 * (1 - 0.05))
    assert [event[0] for event in events].count("pass") == 1, "pass 2 never spawns after a slice expiry"


def test_the_serial_pass_starts_on_the_exact_remainder(tmp_path, two_pass_env, stub_passes):
    """v6.117.0: the serial pass STARTS (the class failure was it never
    starting) on the exact unrounded remainder — a fast parallel pass hands its
    unused slice back, because slices are ceilings and time flows through the
    exact-remainder rule."""
    from ouroboros.preflight_runner import run_hermetic_pytest

    events = stub_passes([(0, ""), (0, "")])
    repo = _make_repo(tmp_path, {"tests/test_plain.py": "def test_ok():\n    assert True\n"})

    assert run_hermetic_pytest(repo, timeout=3) is None

    assert events[0][2] == pytest.approx(0.8 * (3 - 0.15)), "parallel slice = 80% after the node carve"
    assert events[2][2] == pytest.approx(3.0, abs=0.2), "serial starts on ~the whole unspent total"
    assert events[2][1][2].startswith("serial and")


def test_single_pass_mode_preserves_whole_remainder_semantics(tmp_path, two_pass_env, stub_passes):
    """Explicit argv / OUROBOROS_PREFLIGHT_SERIAL keep today's contract: the one
    pass may spend the whole resolved total."""
    from ouroboros.preflight_runner import run_hermetic_pytest

    events = stub_passes([(0, "")])
    repo = _make_repo(tmp_path, {"tests/test_plain.py": "def test_ok():\n    assert True\n"})

    assert run_hermetic_pytest(repo, timeout=2, pytest_args=["tests/"]) is None

    assert events[0][2] == pytest.approx(2.0, abs=0.1)


def test_the_node_lane_receives_its_slice_and_the_total(tmp_path, two_pass_env, stub_passes, monkeypatch):
    """v6.117.0 wiring: run_node_tests() is called with the node slice as its
    own ceiling and the whole resolved total, so its expiry diagnosis can name
    both."""
    from ouroboros import preflight_runner
    from ouroboros.preflight_runner import run_hermetic_pytest

    captured = {}

    def _fake_node(worktree, temp_root, timeout, max_output, total_timeout=None):
        captured["timeout"] = timeout
        captured["total"] = total_timeout
        return None

    monkeypatch.setattr(preflight_runner, "run_node_tests", _fake_node)
    stub_passes([(0, ""), (0, "")])
    repo = _make_repo(tmp_path, {"tests/test_plain.py": "def test_ok():\n    assert True\n"})

    assert run_hermetic_pytest(repo, timeout=2) is None

    assert captured["total"] == 2
    assert captured["timeout"] == pytest.approx(0.1), "node slice = min(120, 5% of T)"


def test_each_pass_gets_the_exact_remaining_budget(tmp_path, two_pass_env, stub_passes):
    """v6.117.0: the parallel pass runs on its own slice; the SERIAL pass starts
    on the exact remaining TOTAL as a float, never rounded up — a fast parallel
    pass hands its unused slice time back to the serial lane (slices are
    ceilings). The two passes together may not outlive the total the gate
    advertises."""
    from ouroboros.preflight_runner import run_hermetic_pytest

    def _spend_half_a_second():
        time.sleep(0.5)
        return (0, "")

    events = stub_passes([_spend_half_a_second, (0, "")])
    repo = _make_repo(tmp_path, {"tests/test_plain.py": "def test_ok():\n    assert True\n"})

    assert run_hermetic_pytest(repo, timeout=60) is None

    spawns = [event for event in events if event[0] == "pass"]
    assert len(spawns) == 2
    first_timeout, second_timeout = spawns[0][2], spawns[1][2]
    assert first_timeout == pytest.approx(0.8 * (60 - 3)), "parallel runs on its slice, not the remainder"
    assert second_timeout == pytest.approx(60 - 0.5, abs=0.3), (
        "pass 2 starts on the exact remaining TOTAL (unused parallel slice flows back)"
    )
    assert second_timeout <= 60 - 0.5, "pass 2's share was rounded up past the total budget"


def test_parallel_pass_expiry_names_phase_budget_and_total(tmp_path, monkeypatch):
    """The typed timeout diagnosis must name the phase's own slice and the
    total, so the NEXT kill is self-explaining (the old message blamed the
    phase with the TOTAL budget and misdirected two release-cycle
    investigations). Stubbed passes, no real pytest spawn."""
    from ouroboros import platform_layer, preflight_runner

    monkeypatch.setattr(platform_layer, "kill_processes_referencing", lambda marker: None)
    monkeypatch.setattr(preflight_runner, "_terminate_preflight_tree", lambda proc, root: None)
    monkeypatch.setattr(
        preflight_runner, "_execute_pytest_pass",
        lambda *a, **k: (None, "tests/test_hangs.py", ""),
    )
    monkeypatch.setattr(preflight_runner, "_verify_preflight_plugins", lambda *a, **k: [])
    monkeypatch.setattr(preflight_runner, "_observed_worker_ids", lambda *a, **k: {"gw0", "gw1"})

    repo = _make_repo(tmp_path, {"tests/test_plain.py": "def test_ok():\n    assert True\n"})

    # T=3000: node slice caps at 120, parallel = 0.80 * 2880 = 2304.
    result = preflight_runner.run_hermetic_pytest(repo, timeout=3000)
    assert result is not None
    assert "parallel pass" in result
    assert "pytest timed out after 2304 seconds in the parallel pass" in result, result
    assert "(phase budget 2304 of total 3000 seconds)" in result, result


def test_node_pass_expiry_reports_phase_budget_and_total(tmp_path, monkeypatch):
    """The node lane names its own slice and the whole total when it expires.
    The container layer is stood in by a fake whose spawn hangs forever."""
    from ouroboros import platform_layer, preflight_node as pn, preflight_runner
    from ouroboros.process_containment import ProcessContainer

    worktree = tmp_path / "repo"
    (worktree / "web" / "tests").mkdir(parents=True)
    (worktree / "web" / "tests" / "ok.test.js").write_text(
        "test('ok', () => {});\n", encoding="utf-8"
    )

    class _FakeProc:
        pid = os.getpid() + 1_000_000  # non-colliding convention (sibling tests)
        stdout = None
        stderr = None
        returncode = None

        def communicate(self, timeout=None):
            raise subprocess.TimeoutExpired(cmd="node --test", timeout=timeout)

        def poll(self):
            return -9

        def wait(self, timeout=None):
            return -9

    def _fake_spawn(self, *args, **kwargs):
        return _FakeProc()

    monkeypatch.setattr(ProcessContainer, "__init__", lambda self, *a, **k: None)
    monkeypatch.setattr(ProcessContainer, "spawn", _fake_spawn)
    monkeypatch.setattr(ProcessContainer, "reap", lambda self: "")
    monkeypatch.setattr(ProcessContainer, "close", lambda self: None)
    monkeypatch.setattr(preflight_runner, "_terminate_preflight_tree", lambda proc, root: None)
    monkeypatch.setattr(pn, "resolve_node", lambda: "/fake/node")
    monkeypatch.setattr(pn, "probe_node_version", lambda node: "22.0.0")

    result = pn.run_node_tests(worktree, tmp_path / "t", 90.0, 8000, total_timeout=1800)

    assert result is not None
    error = result["error"] or ""
    assert "node --test timed out after 90 seconds in the node pass" in error, error
    assert "(phase budget 90 of total 1800 seconds)" in error, error
