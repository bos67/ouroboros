"""Tool-arg degradation streak: a task-scoped consecutive arg-error counter.

Extracted WHOLE from ``ouroboros/loop_tool_execution.py`` (6.119.11) to close
the GIANT_PATHS debt on that module: the streak mechanics have their own
cohesive domain — task-scoped lazily-initialized counter state on the tool
ctx, the increment/reset semantics, and the alert line riding the periodic
self-check. Nothing here touches result plumbing or truncation.

Task-scoping is deliberate: a degradation arc is a property of ONE task
(measured: bc50794b burned ~15 consecutive rounds of degraded tool-args
mid-arc); a process-global counter would carry degradation across task
boundaries and inject alerts into unrelated tasks. Task boundaries
therefore reset it by construction.
"""

from __future__ import annotations

from typing import Any, Dict

_ARG_ERROR_STATUS = "arg_error"
_ARG_STREAK_ALERT_AT = 3
_ARG_STREAK_TOOL_NAMES_MAX = 5


def tool_arg_streak(tool_ctx: Any) -> Dict[str, Any]:
    """Task-scoped consecutive arg-error streak on the tool ctx (lazy init)."""
    streak = getattr(tool_ctx, "_arg_error_streak", None)
    if not isinstance(streak, dict) or "count" not in streak or "tools" not in streak:
        streak = {"count": 0, "tools": []}
        try:
            setattr(tool_ctx, "_arg_error_streak", streak)
        except Exception:
            streak = {"count": 0, "tools": []}
    return streak


def update_tool_arg_streak(
    tool_ctx: Any, streak: Dict[str, Any], fn_name: str, result_meta: Dict[str, Any],
) -> None:
    """Increment the streak ONLY on typed arg_error outcomes (pinned class).

    Every other failure class (timeout, blocked, safety_violation,
    tool_reported_failure, edit_ops_blocked, generic error...) is not an
    argument-degradation signal: incrementing on it would make the alert
    fire on infra noise instead of the measured class.
    """
    if str(result_meta.get("status") or "") != _ARG_ERROR_STATUS:
        return
    streak["count"] += 1
    if fn_name and fn_name not in streak["tools"]:
        streak["tools"].append(fn_name)
    if len(streak["tools"]) > _ARG_STREAK_TOOL_NAMES_MAX:
        del streak["tools"][:-_ARG_STREAK_TOOL_NAMES_MAX]


def tool_arg_streak_alert_line(tool_ctx: Any) -> str:
    """The alert block riding the periodic self-check when streak >= threshold.

    Returns "" below the threshold so below-threshold checkpoint turns stay
    byte-identical to today; bounded last-5 unique tool list (first-seen
    order kept by the counter) and the re-derive-from-error-text command.
    """
    streak = tool_arg_streak(tool_ctx)
    count = streak.get("count") or 0
    if count < _ARG_STREAK_ALERT_AT:
        return ""
    tools_text = ", ".join(str(name) for name in streak.get("tools") or [])
    return (
        f"\n\n⚠️ [TOOL-ARG DEGRADATION ALERT — {count} consecutive arg-error"
        f"(s), tools: {tools_text}] Your last {count} tool calls failed on "
        "argument JSON (parse or schema). STOP generating tool arguments "
        "from memory. Re-derive the arguments from the accepted-parameters "
        "shown in the recent error texts (they appear under 'accepted "
        "parameters:'), or answer the owner directly in a plain sentence "
        "and stop rather than risk repeating the same wrong call. A "
        "degenerate repetition-loop final is already stamped "
        "(final_text_integrity); this alert is the turn-level companion "
        "of that seam.\n"
    )