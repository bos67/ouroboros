"""Regression suite for the tool-args recovery rail (6.119.8).

Pins the spec semantics:
1) Repair only on ONE clean unique reparse to a dict (ambiguity/off-shape refuse).
2) Parse-refusal error text carries the accepted-params ladder from the
   registry SSOT accessor (fail-soft: none -> no line).
3) Typed arg_error status for the parse-refusal path; counter increments ONLY
   on typed arg_error outcomes, resets on any non-arg-error outcome; alert
   text at >=3 rides ONLY the self-check seam.
4) Alert tool list bounded to last 5 unique names in first-seen order.
"""

from __future__ import annotations

import pathlib
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ouroboros.loop_tool_execution import (
    _accepted_params_note,
    _execute_single_tool,
    _tool_arg_streak,
    _update_tool_arg_streak,
    process_tool_results,
    tool_arg_streak_alert_line,
)
from ouroboros.tools.arg_recovery import recover_tool_arguments


# ---------------------------------------------------------------------------
# recover_tool_arguments
# ---------------------------------------------------------------------------

def test_recover_empty_and_null_to_empty_args():
    args, kind = recover_tool_arguments("")
    assert args == {} and kind == "empty_args"
    args, kind = recover_tool_arguments("   ")
    assert args == {} and kind == "empty_args"
    args, kind = recover_tool_arguments("null")
    assert args == {} and kind == "empty_args"


def test_recover_truncated_json_at_last_pair_boundary():
    raw = '{"path": "a.py", "old_str": "x'
    args, kind = recover_tool_arguments(raw)
    assert args == {"path": "a.py"} and kind == "balanced_prefix"

    # Truncated AFTER a complete pair (only closers missing): the end-cut
    # recovers every pair — the least-lossy repair.
    raw = ('{"root": "system_repo", "path": "x.py", '
           '"old_str": "alpha", "new_str": "beta"')
    args, kind = recover_tool_arguments(raw)
    assert args == {
        "root": "system_repo",
        "path": "x.py",
        "old_str": "alpha",
        "new_str": "beta",
    } and kind == "balanced_prefix"

    # Truncated INSIDE the backup-path string (unterminated tail): the
    # END-cut path fails; the boundary-cut drops the incomplete pair.
    raw = ('{"cmd": ["python", "-c"], "backup_path": "/tmp/x.p')
    args, kind = recover_tool_arguments(raw)
    assert args == {"cmd": ["python", "-c"]} and kind == "balanced_prefix"


def test_recover_refuses_non_dict_and_nested_ambiguity_is_resolved():
    # Nested mid-string cut: the end-cut is the unique least-lossy repair
    # (closes the inner dict then the list) — recovers, does not refuse.
    args, kind = recover_tool_arguments('{"a": "x", "b": [1, {"c": "y')
    assert args == {"a": "x", "b": [1]} and kind == "balanced_prefix"
    # Lists and bare strings never recover — the args must be a dict.
    with pytest.raises(ValueError):
        recover_tool_arguments("[1, 2")
    with pytest.raises(ValueError):
        recover_tool_arguments('"just a string')


def test_recover_returns_valid_json_untouched():
    args, kind = recover_tool_arguments('{"x": 1}')
    assert args == {"x": 1} and kind == "empty_args"


# ---------------------------------------------------------------------------
# accepted-params ladder (SSOT accessor; fail-soft)
# ---------------------------------------------------------------------------

def test_accepted_params_note_uses_registry_schema():
    class _Registry:
        def get_schema_by_name(self, name):
            return {
                "type": "function",
                "function": {
                    "name": name,
                    "parameters": {
                        "type": "object",
                        "properties": {"cmd": {}, "cwd": {}},
                    },
                },
            }

    note = _accepted_params_note(_Registry(), "run_command")
    assert note == " (accepted parameters: cmd, cwd)"


def test_accepted_params_note_failsoft_when_schema_absent():
    class _Registry:
        def get_schema_by_name(self, name):
            return None

    assert _accepted_params_note(_Registry(), "ghost_tool") == ""


# ---------------------------------------------------------------------------
# typed arg_error status + streak counter semantics
# ---------------------------------------------------------------------------

def _fake_registry(properties, with_execute=True):
    class _Registry:
        CODE_TOOLS = set()

        def get_schema_by_name(self, name):
            if not properties:
                return None
            return {
                "type": "function",
                "function": {
                    "name": name,
                    "parameters": {"type": "object", "properties": properties},
                },
            }

        def execute(self, name, args):
            return "ok"

    reg = _Registry()
    reg._ctx = SimpleNamespace()
    return reg


def test_parse_refusal_carries_accepted_params_and_typed_status(tmp_path):
    logs = tmp_path / "logs"
    logs.mkdir()
    tools = _fake_registry({"cmd": {}, "cwd": {}})
    tc = {
        "id": "c1",
        "function": {
            "name": "run_command",
            "arguments": '{"a": "',  # open object + open string, no boundary
        },
    }

    import ouroboros.loop_tool_execution as lte

    real = lte.persist_call
    recorded = {}

    def fake_persist(*args, **kwargs):
        recorded["manifest"] = kwargs.get("manifest") or {}
        return {"manifest_ref": {"path": "stub"}}

    lte.persist_call = staticmethod(fake_persist)  # type: ignore[assignment]
    try:
        out = _execute_single_tool(tools, tc, logs, "task1")
    finally:
        lte.persist_call = real
    text = str(out["result"])
    assert text.startswith("⚠️ TOOL_ARG_ERROR")
    assert "repair refused" in text
    assert "(accepted parameters: cmd, cwd)" in text
    assert out["result_meta"]["status"] == "arg_error"
    assert recorded["manifest"]["status"] == "arg_error"


def test_recovered_call_dispatches_with_repaired_args(tmp_path):
    """Recovery path: repaired args are dispatched (never executed here),
    and the typed recovery fact lands on result_meta, not the result text."""
    logs = tmp_path / "logs"
    logs.mkdir()
    tools = _fake_registry({"cmd": {}, "cwd": {}})
    seen = {}

    def fake_execute(name, args):
        seen["args"] = args
        return 'ARD_NOTE {"ok_recovered": true, "mark_fix": "NOTE-1726"}'

    tools.execute = fake_execute
    tc = {
        "id": "c2",
        "function": {
            "name": "run_command",
            "arguments": '{"cmd": ["python", "-c", "print(1)", INVALID',
        },
    }
    out = _execute_single_tool(tools, tc, logs, "task1")
    assert seen["args"] == {"cmd": ["python", "-c", "print(1)"]}
    assert out["result_meta"]["arg_wire_repaired"] == "balanced_prefix"
    assert out["is_error"] is False


def test_process_tool_results_streak_increment_and_success_reset(tmp_path):
    tools = _fake_registry(None)
    messages = []
    llm_trace = {"tool_calls": []}

    def _run(result_meta_status):
        return process_tool_results(
            [{
                "tool_call_id": "c",
                "fn_name": "run_command",
                "result": "⚠️ TOOL_ARG_ERROR: x",
                "is_error": result_meta_status == "arg_error",
                "tool_args": {},
                "args_for_log": {},
                "is_code_tool": False,
                "result_meta": {"status": result_meta_status},
            }],
            messages, llm_trace, lambda *_: None, tools=tools,
        )

    _run("arg_error")
    streak = _tool_arg_streak(tools._ctx)
    assert streak["count"] == 1 and streak["tools"] == ["run_command"]
    _run("arg_error")
    _run("ok")
    assert _tool_arg_streak(tools._ctx)["count"] == 0
    _run("arg_error")
    _run("timeout")     # timeout is also a non-arg-error outcome → resets
    assert _tool_arg_streak(tools._ctx)["count"] == 0


def test_alert_food_threshold_and_boundary(tmp_path):
    tools = _fake_registry(None)
    ctx = tools._ctx
    assert tool_arg_streak_alert_line(ctx) == ""
    import ouroboros.loop_tool_execution as lte

    streak = _tool_arg_streak(ctx)
    for _ in range(3):
        _update_tool_arg_streak(ctx, streak, "run_command", {"status": "arg_error"})
    alert = lte.tool_arg_streak_alert_line(ctx)
    assert "3 consecutive" in alert
    assert "run_command" in alert
    assert "TOOL-ARG DEGRADATION ALERT" in alert


def test_alert_tool_list_bounded_last5(tmp_path):
    tools = _fake_registry(None)
    ctx = tools._ctx
    streak = _tool_arg_streak(ctx)
    for name in ("a", "b", "c", "d", "e", "f"):
        _update_tool_arg_streak(ctx, streak, name, {"status": "arg_error"})
    alert = tool_arg_streak_alert_line(ctx)
    for name in ("b", "c", "d", "e", "f"):
        assert name in alert
    assert not alert.startswith("a")


def test_self_check_injects_alert_only_at_threshold(tmp_path):
    import ouroboros.loop as loop

    tools = _fake_registry(None)
    ctx = tools._ctx
    messages = [{"role": "user", "content": "work"}]
    usage = {"cost": 0.1}
    emitted = []

    streak = _tool_arg_streak(ctx)
    streak["count"] = 2
    streak["tools"].append("run_command")
    ok_below = loop._maybe_inject_self_check(
        15, 200, messages, usage, emitted.append, tool_ctx=ctx, task_id="t",
    )
    assert ok_below is True
    assert "TOOL-ARG DEGRADATION ALERT" not in messages[-1]["content"]

    streak["count"] += 1
    ok_above = loop._maybe_inject_self_check(
        30, 200, messages, usage, emitted.append, tool_ctx=ctx, task_id="t",
    )
    assert ok_above is True
    assert "TOOL-ARG DEGRADATION ALERT" in messages[-1]["content"]
    assert "3 consecutive" in messages[-1]["content"]
    assert "accepted parameters" in messages[-1]["content"]
