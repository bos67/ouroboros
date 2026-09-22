"""Per-task reclaim provenance accessors over the tool ctx.

Extracted WHOLE from ``ouroboros/loop_tool_execution.py`` (6.119.11): the
reclaim materializer (``ouroboros/loop.py``) and the shared result-plumbing
in the donor need these bindings; they are pure ctx-state readers/writers
with no tool-dispatch knowledge. Donor keeps its own ``_tool_trace_refs``
accumulator seam in ``process_tool_results`` — these three functions only
read/prune that state.
"""

from __future__ import annotations

from typing import Any, Dict


def reclaim_trace_refs(tool_ctx: Any) -> Dict[str, Any]:
    """Per-task {tool_call_id: trace_ref} accumulated as tool results append."""
    refs = getattr(tool_ctx, "_tool_trace_refs", None)
    return refs if isinstance(refs, dict) else {}


def reclaim_negative_memo(tool_ctx: Any) -> set:
    """Per-task set of non-shrinking reclaim unit keys (created on demand)."""
    memo = getattr(tool_ctx, "_context_reclaim_negative_memo", None)
    if not isinstance(memo, set):
        memo = set()
        tool_ctx._context_reclaim_negative_memo = memo
    return memo


def prune_reclaim_trace_refs(tool_ctx: Any, messages) -> None:
    """Drop trace refs whose tool_call_id left the transcript (post-reclaim bound)."""
    msgs = list(messages or [])
    refs = getattr(tool_ctx, "_tool_trace_refs", None)
    if not isinstance(refs, dict) or not refs:
        return
    live = {
        str(msg.get("tool_call_id"))
        for msg in msgs
        if isinstance(msg, dict) and msg.get("tool_call_id")
    }
    for call_id in [key for key in refs if key not in live]:
        del refs[call_id]