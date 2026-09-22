"""Parity pin for the 6.119.12 self-check scaffold relocation.

loop.py kept every stateful decision (round gating, tree accounting,
arg-streak alert) and now delegates only the reminder TEXT to
``task_pacing.build_self_check_reminder``. The golden literals below are
verbatim from the pre-move inline builder (v6.119.11 ``loop.py``); this
suite pins that the relocation is behavior-preserving at the byte level for
the below-threshold base case and for the tool-trace / arg-alert / tree-line
variants. A future edit to the reminder wording must update BOTH this
golden and its own changelog — silently drifting text is the exact class
this pin exists to catch.
"""

import ouroboros.task_pacing as task_pacing


def _golden(checkpoint_num, round_idx, max_rounds, ctx_tokens, cost_text, tree_line, tool_trace, arg_alert):
    reminder = (
        f"[CHECKPOINT {checkpoint_num} — round {round_idx}/{max_rounds}]\n"
        f"Context: ~{ctx_tokens} tokens | Cost so far: {cost_text} | "
        f"Rounds remaining: {max_rounds - round_idx}\n"
        f"{tree_line}"
    )
    if tool_trace:
        reminder += f"\n{tool_trace}\n"
    if arg_alert:
        reminder += arg_alert
    reminder += (
        "\nThis is a periodic self-check, not a command to stop. "
        "Glance at your recent tool-call trace above and briefly consider:\n"
        "- Are you still making progress toward the task, or repeating the same actions?\n"
        "- Is the current approach still the right one, or should you narrow scope / try a different angle?\n"
        "- If you are waiting on a long build/download/training run or have independent branches of investigation, consider schedule_subagent for a focused parallel handoff.\n"
        "- If the task is effectively done, first re-check the literal original requirements one by one "
        "against the specified interface/path/format/service, then wrap up by replying with your final answer in plain text (no tool call). "
        "Otherwise continue with the most valuable next step.\n"
        "\nNo special format required — just think, then act."
    )
    return reminder


def test_self_check_reminder_matches_v611911_golden_base():
    got = task_pacing.build_self_check_reminder(
        checkpoint_num=2, round_idx=30, max_rounds=200,
        ctx_tokens=91557, cost_text="$0.46", tree_line="",
        tool_trace="", arg_alert="",
    )
    assert got == _golden(2, 30, 200, 91557, "$0.46", "", "", "")


def test_self_check_reminder_matches_golden_tree_line():
    tree_line = (
        "Task tree spend: ~$0.46 of $10.00 hard tree cap "
        "(ledger-accounted incl. in-flight holds, subagents included)\n"
    )
    got = task_pacing.build_self_check_reminder(
        checkpoint_num=1, round_idx=15, max_rounds=200,
        ctx_tokens=12345, cost_text="unknown", tree_line=tree_line,
        tool_trace="", arg_alert="",
    )
    assert got == _golden(1, 15, 200, 12345, "unknown", tree_line, "", "")


def test_self_check_reminder_matches_golden_trace_and_alert():
    tool_trace = "Recent tool calls (oldest first):\n  1. read_file"
    arg_alert = "\n\n⚠️ [TOOL-ARG DEGRADATION ALERT — 3 consecutive arg-error(s), tools: run_command] stop."
    got = task_pacing.build_self_check_reminder(
        checkpoint_num=2, round_idx=30, max_rounds=200,
        ctx_tokens=91557, cost_text="$0.46", tree_line="",
        tool_trace=tool_trace, arg_alert=arg_alert,
    )
    assert got == _golden(2, 30, 200, 91557, "$0.46", "", tool_trace, arg_alert)
