"""Bounded JSON-argument recovery for model tool calls (6.119.8).

Degradation arcs (bc50794b, 74c83c57, and a live faceplant on plan_task
args in the same release) emit malformed argument JSON: an empty payload
where an object was intended, or a payload truncated mid-string/mid-key by
embedded newlines inside quoted values. The recovery rail — the same honesty
contract as the 6.118.2 edit-hints rail (ouroboros/tools/edit_support.py) —
tries ordered, deterministic, content-aware repairs; a repaired call may
proceed ONLY when exactly ONE repair candidate re-parses cleanly to a DICT
as the single surviving candidate.

Repairs never execute anything and never claim authorization: they only
re-shape the WIRE FORMAT. The repaired arguments still flow through full
registry validation and the safety layer, so a repaired call can still be
refused on policy or schema grounds.

Pinned rules:
  R1  raw arguments that are empty / whitespace-only / literal ``null``
      recover to ``{}`` (kind ``empty_args``). The empty wire is a legal
      argument shape; the registry's own param validation then answers
      with the accepted-params fact if the tool required more.
  R2  bounded structural truncation repair (kind ``balanced_prefix``),
      in priority order and AT MOST ONE candidate consumed:
        a) end-cut — when the tail after the last clean ``key: value,``
           boundary has NO unterminated string (the payload was truncated
           after a complete pair; only closers are missing), cut at
           end-of-text, close every still-open container in stack order,
           require the candidate to re-parse to a dict.
        b) last-boundary-cut — otherwise cut at the LAST clean boundary,
           close containers, re-parse. Never tries an earlier boundary:
           two competing prefix depths would be ambiguous repair, and
           ambiguity means the surviving tail could belong to more than
           one argument shape.
      If NO candidate re-parses cleanly to a dict, or the re-parsed value
      is not a dict (list/number/string), refuse loudly.

Fail-soft: any exception inside a candidate leaves it uncounted; the
original raw text is never mutated; nothing here writes to disk.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

_MAX_REPAIR_SCAN_BYTES = 20 * 1024
_PAIR_OPEN = {"{": "}", "[": "]"}
_PAIR_CLOSE = {v: k for k, v in _PAIR_OPEN.items()}


def _reparse_to_dict(candidate: str) -> Optional[Dict[str, Any]]:
    """Parse one candidate; keep it only when it re-parses cleanly to a dict."""
    try:
        parsed = json.loads(candidate)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _tail_has_unterminated_string(tail: str) -> bool:
    """True when a string is open at the end of ``tail`` (odd quote parity).

    The bounded first-truncation shape: a key-value tail was cut inside a
    string literal. In that case an end-cut cannot be trusted (one/both
    parts of the final pair are incomplete); the caller falls to a
    boundary-cut.
    """
    return bool(tail.count('"') % 2)


def _boundaries_with_stack(text: str) -> List[Tuple[int, List[str]]]:
    """Scan bounded: return clean ``,`` boundaries (index, open-stack snapshot).

    A boundary is recorded only OUTSIDE strings and only while at least one
    container is open (depth >= 1). The stack snapshot lists the still-open
    pairs at the boundary moment in open order — exactly what must be closed
    to make the prefix a complete JSON value.
    """
    boundaries: List[Tuple[int, List[str]]] = []
    stack: List[str] = []
    in_string = False
    escaped = False
    for i, ch in enumerate(text[:_MAX_REPAIR_SCAN_BYTES]):
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch in _PAIR_OPEN:
            stack.append(ch)
        elif ch in _PAIR_CLOSE:
            if not stack or stack[-1] != _PAIR_CLOSE[ch]:
                return boundaries  # deeper structural defect than we repair
            stack.pop()
        elif ch == "," and stack:
            boundaries.append((i, list(stack)))
    return boundaries


def _candidate_at(text: str, index: int, opens: List[str]) -> str:
    body = text[:index].rstrip().rstrip(",")
    suffix = "".join(_PAIR_OPEN[op] for op in reversed(opens))
    return body + suffix


def recover_tool_arguments(raw: Any) -> Tuple[Dict[str, Any], str]:
    """Recover model tool arguments from malformed wire JSON.

    Returns ``(args, repair_kind)``. Raises ``ValueError`` when no clean
    candidate survives (no parse, non-dict shape) — the caller must keep
    today's honest typed TOOL_ARG_ERROR and never invent arguments.
    """
    text = raw if isinstance(raw, str) else (str(raw) if raw is not None else "")
    stripped = text.strip()

    if not stripped or stripped.lower() == "null":
        return {}, "empty_args"

    parsed = _reparse_to_dict(stripped)
    if parsed is not None:
        # Caller-side json.loads normally catches this first; a dict that
        # parses here is simply valid — no repair needed.
        return parsed, "empty_args"

    boundaries = _boundaries_with_stack(stripped)
    # (a) end-cut: the tail after the LAST boundary has no unterminated
    # string — the payload was truncated after a complete pair, only
    # closers are missing. The end-cut is then the uniquely least-lossy
    # repair, kept deliberately ahead of any boundary-cut.
    if boundaries:
        last_index, last_opens = boundaries[-1]
        tail = stripped[last_index + 1:]
        if not _tail_has_unterminated_string(tail):
            end_cut = _candidate_at(stripped, len(stripped), last_opens)
            reparsed = _reparse_to_dict(end_cut)
            if reparsed is not None:
                return reparsed, "balanced_prefix"
        # (b) last-boundary-cut: drop the degenerate tail entirely.
        boundary_cut = _candidate_at(stripped, last_index, last_opens)
        reparsed = _reparse_to_dict(boundary_cut)
        if reparsed is not None:
            return reparsed, "balanced_prefix"
    raise ValueError("no clean repair candidate survived")
