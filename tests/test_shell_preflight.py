"""p1 hand-discipline tests: shell pre-exec audit (M1 argv + M2 body parse).

Each test pins a MEASURED incident class from the 2026-09-24 baseline
(artifact ``p1_baseline_report.md``): the lost-dash argv that died at exec
with ``sh: cannot open c`` (2026-09-23T05:49), and the malformed compound
``sh -c`` bodies that ran their leading commands before dying at a syntax
error (2026-09-21T15:53, 2026-09-24T08:04 — the latter a bash-only
``<(cmd)`` under sh). The heredoc-with-python working pattern — the most
common healthy form in real traces — is pinned as a strict negative; so is
the script-path negative from the 6.119.15 luna advisory: argv whose bare
suspect token names an EXISTING file in the run cwd (`sh c` with a real
script named `c`) must dispatch untouched. Real-interpreter M2 pre-parses
carry per-test `@pytest.mark.serial` per the conftest real-process
criterion.
"""
from __future__ import annotations

from subprocess import CompletedProcess

import pytest

from ouroboros.tools.shell import _run_shell
from ouroboros.tools.shell_preflight import preflight_argv


@pytest.fixture
def fake_subprocess(monkeypatch):
    """Canary fixture: records every _tracked_subprocess_run dispatch.

    Refusal tests assert ``calls == []`` — the preflight fires strictly
    before dispatch, so a recorded call means the guard failed its order.
    """
    monkeypatch.setattr("ouroboros.tools.shell.load_settings", lambda: {})

    def _install(*, returncode: int = 0, stdout: str = "", stderr: str = ""):
        calls: list[dict] = []

        def fake_run(cmd, **kwargs):
            calls.append({"cmd": cmd, "kwargs": kwargs})
            return CompletedProcess(cmd, returncode, stdout, stderr)

        monkeypatch.setattr("ouroboros.tools.shell._tracked_subprocess_run", fake_run)
        return calls

    return _install


def _ctx(tmp_path):
    from types import SimpleNamespace

    return SimpleNamespace(
        repo_dir=tmp_path,
        drive_root=tmp_path,
        drive_logs=lambda: tmp_path,
    )


# ---------------------------------------------------------------------------
# Unit: preflight_argv pure function
# ---------------------------------------------------------------------------
# The M2 tests below spawn REAL interpreter pre-parses (`sh|bash -n -c`),
# so they carry per-test `@pytest.mark.serial` (the conftest-preferred
# form of the real-process criterion): `-m serial` collects exactly the
# spawning set and the mocked remainder stays in the parallel lane.


def test_m1_lost_dash_flag_is_caught():
    ok, msg = preflight_argv(["sh", "c", "true"])
    assert not ok
    assert "lost its dash" in msg
    assert '"-c"' in msg


def test_m1_python_module_flag_variant():
    ok, msg = preflight_argv(["python3", "m", "pytest"])
    assert not ok
    assert '"-m"' in msg


def test_m1_correct_dashes_pass():
    for cmd in (["sh", "-c", "true"], ["python3", "-m", "pytest"], ["bash", "-lc", "true"]):
        ok, msg = preflight_argv(cmd)
        assert ok, (cmd, msg)


def test_m1_script_named_c_in_run_cwd_is_not_a_lost_flag(tmp_path):
    # 6.119.15 luna advisory pinned: `sh c` where `c` is an EXISTING file in
    # the run cwd is a script-path invocation, never a lost-flag refusal.
    (tmp_path / "c").write_text("echo hi")
    ok, _ = preflight_argv(["sh", "c"], cwd=str(tmp_path))
    assert ok


def test_m1_c_missing_in_run_cwd_still_refused(tmp_path):
    ok, msg = preflight_argv(["sh", "c", "true"], cwd=str(tmp_path))
    assert not ok
    assert "lost its dash" in msg


@pytest.mark.serial
def test_m2_bad_paren_body_refused():
    ok, msg = preflight_argv(["sh", "-c", "echo bad ("])
    assert not ok
    assert "pre-parse" in msg


@pytest.mark.serial
def test_m2_bashism_under_sh_refused():
    ok, msg = preflight_argv(["sh", "-c", "wc -l <(git show HEAD:README.md)"])
    assert not ok


@pytest.mark.serial
def test_m2_bashism_under_bash_passes():
    # Same body is VALID bash — the parse must follow the real interpreter.
    ok, _ = preflight_argv(["bash", "-c", "wc -l <(echo hi)"])
    assert ok


@pytest.mark.serial
def test_m2_heredoc_python_pattern_passes():
    body = "python3 - <<'PY'\nimport json\nprint(json.dumps({'a': 1}))\nPY"
    ok, _ = preflight_argv(["sh", "-c", body])
    assert ok


@pytest.mark.serial
def test_m2_command_substitution_and_pipes_pass():
    ok, _ = preflight_argv(["sh", "-c", "p=hello; echo \"$p\" | grep -c hel || true"])
    assert ok


def test_plain_exec_argv_untouched():
    ok, _ = preflight_argv(["git", "log", "--oneline", "-10"])
    assert ok


def test_run_script_style_argv_untouched():
    # run_script dispatches as [interp, path]; script bodies are file-backed
    # and deliberately not parsed here.
    ok, _ = preflight_argv(["python3", "/tmp/tmp_scripts/script_deadbeef.py"])
    assert ok


def test_checker_missing_passes_through(monkeypatch):
    import subprocess as real_subprocess

    def boom(*a, **k):
        raise OSError("no interpreter")

    monkeypatch.setattr(real_subprocess, "run", boom)
    ok, _ = preflight_argv(["sh", "-c", "echo ("])
    assert ok  # broken checker must never become the failure mode


# ---------------------------------------------------------------------------
# Integration: _run_shell refuses BEFORE any subprocess side effect
# ---------------------------------------------------------------------------


def test_run_shell_refuses_lost_dash_without_running(tmp_path, fake_subprocess):
    calls = fake_subprocess(stdout="ok")
    result = _run_shell(_ctx(tmp_path), ["sh", "c", "true"])
    assert "SHELL_PREFLIGHT" in result
    assert "lost its dash" in result
    assert calls == []  # nothing executed — the refusal precedes dispatch


def test_run_shell_script_named_c_dispatches(tmp_path, fake_subprocess):
    # End-to-end discriminator pin: a real script named `c` in the run cwd
    # dispatches THROUGH the audit (nothing refused, nothing skipped).
    (tmp_path / "c").write_text("echo hi")
    calls = fake_subprocess(stdout="hi")
    result = _run_shell(_ctx(tmp_path), ["sh", "c"])
    assert "SHELL_PREFLIGHT" not in result
    assert calls and calls[0]["cmd"] == ["sh", "c"]


@pytest.mark.serial
def test_run_shell_refuses_bad_body_without_running(tmp_path, fake_subprocess):
    calls = fake_subprocess(stdout="ok")
    result = _run_shell(_ctx(tmp_path), ["sh", "-c", "mkdir -p /tmp/x; echo bad ("])
    assert "SHELL_PREFLIGHT" in result
    assert "Syntax error" in result
    assert calls == []  # mkdir never ran — the pre-parse caught it first


@pytest.mark.serial
def test_run_shell_healthy_heredoc_still_runs(tmp_path, fake_subprocess):
    calls = fake_subprocess(stdout="ok")
    body = "python3 - <<'PY'\nprint(1)\nPY"
    result = _run_shell(_ctx(tmp_path), ["sh", "-c", body])
    assert "SHELL_PREFLIGHT" not in result
    assert "exit_code=0" in result
    assert calls and calls[0]["cmd"] == ["sh", "-c", body]


def test_run_shell_healthy_direct_argv_still_runs(tmp_path, fake_subprocess):
    fake_subprocess(stdout="  indented\n")
    result = _run_shell(_ctx(tmp_path), ["printf", "x"])
    assert "exit_code=0" in result
    assert "SHELL_PREFLIGHT" not in result


# ---------------------------------------------------------------------------
# 6.119.17: the audit hint is the RESOLVED run dir, not the raw cwd string
# ---------------------------------------------------------------------------


def test_preflight_hint_is_resolved_binding_dir(tmp_path, fake_subprocess, monkeypatch):
    # 6.119.17 triad residual: the audit must receive binding.target_path —
    # the directory the command will actually run in — never the raw `cwd`
    # argument (which may be a selector spelling or empty).
    import ouroboros.tools.shell_preflight as pf

    captured: list[str] = []

    def spy(cmd, cwd=None):
        captured.append(cwd)
        return True, ""

    monkeypatch.setattr(pf, "preflight_argv", spy)
    fake_subprocess(stdout="ok")
    result = _run_shell(_ctx(tmp_path), ["sh", "-c", "true"], cwd=str(tmp_path))
    assert "SHELL_PREFLIGHT" not in result
    assert captured, "audit was not consulted at all"
    assert captured[0] == str(tmp_path)  # resolved dir, not the raw spelling


def test_preflight_refusal_still_precedes_dispatch_after_move(tmp_path, fake_subprocess):
    # Ordering pin after the 6.119.17 move: the audit block now sits below
    # binding resolution, but a refusal still fires strictly before any
    # subprocess dispatch (binding resolution is process-free).
    calls = fake_subprocess(stdout="ok")
    result = _run_shell(_ctx(tmp_path), ["sh", "c", "true"], cwd=str(tmp_path))
    assert "SHELL_PREFLIGHT" in result
    assert calls == []  # nothing executed — refusal precedes dispatch


def test_preflight_hint_resolves_selector_cwd_spelling(tmp_path, fake_subprocess, monkeypatch):
    # 6.119.17 post-gate advisory (glm, changelog_accuracy): an absolute-cwd
    # spy test can pass unchanged against the pre-fix code, so it does not pin
    # the selector-spelling seam this release actually moved. This variant
    # passes cwd as the SELECTOR spelling `task_drive`; the binding layer
    # resolves it to <drive_root>/task_drives/<task_id>, so the audit must
    # receive that absolute dir — never the raw selector string, and never
    # the repo_dir fallback (both pre-fix behaviors).
    import ouroboros.tools.shell_preflight as pf

    captured: list[str] = []

    def spy(cmd, cwd=None):
        captured.append(str(cwd))
        return True, ""

    monkeypatch.setattr(pf, "preflight_argv", spy)
    calls = fake_subprocess(stdout="ok")
    result = _run_shell(_ctx(tmp_path), ["sh", "-c", "true"], cwd="task_drive")
    assert "SHELL_PREFLIGHT" not in result
    assert captured, "audit was not consulted at all"
    hint = captured[0]
    assert not hint.endswith("task_drive"), "raw selector spelling leaked into the hint"
    assert hint.startswith(str(tmp_path)), f"hint {hint} did not resolve under the ctx drive root"
    assert "task_drives" in hint, f"hint {hint} is not a resolved task_drive target"
    assert calls, "healthy selector-cwd dispatch must still run the command"
