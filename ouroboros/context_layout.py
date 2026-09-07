"""Single source of truth for the LLM context LAYOUT of reference docs.

This module decides, in ONE place, which governance / reference docs enter the
always-on agent context and in what form, per context mode (low / max) and task
kind. Centralizing it here keeps the low/max split from drifting across the
surfaces that consume it (main task context, background consciousness, deep
self-review).

Doc matrix (agent cognition surfaces; D-ARCH unification, owner 2026-08-08):

  | doc            | max            | low                                   |
  |----------------|----------------|---------------------------------------|
  | SYSTEM / BIBLE | full (tier-0; caller-owned, never varied here)              |
  | ARCHITECTURE   | full for self-body classes; nav map + on-demand pointer for direct-chat/external classes | navigation map (full sections on demand) |
  | DEVELOPMENT    | full when the caller includes dev context, else pointer — MODE-INDEPENDENT |
  | README         | on-demand pointer (removed from always-on for all modes)     |
  | CHECKLISTS     | on-demand pointer (reviewers load their own copy)            |

ARCHITECTURE.md residency in owner-max is CLASS-SCOPED (v6.115.0, owner
decision): the full document stays resident for self-body classes (pooled/
evolution/self-body work), while direct-chat turns and externally-bound
surfaces (external workspaces, project trees, subagents, external api/cli/
scheduled surfaces) receive the lossless H2-H4 navigation map plus a visible
on-demand pointer — a relocation, never truncation (BIBLE P1). In low mode the
nav map remains the form for every class. The caller computes the class from
structural task facts (never message text) and passes ``architecture_full``;
the default True keeps non-task callers (consciousness governance) at the
documented full-in-max behavior. DEVELOPMENT.md inclusion is the caller's
per-task decision and remains deliberately decoupled from the mode.

D-DEV (owner decision, 2026-08-08) fixes what that per-task decision keys on:
DEVELOPMENT.md is the self-engineering handbook, so it loads exactly when the
work targets Ouroboros's own body — and the signal is the ACTIVE REPO BINDING, a
path fact, never a guess from message text (P5). ``context.py`` derives it from
``not _task_uses_external_context(task)``: a bound workspace, a subagent, or an
api/cli/scheduled surface means another codebase and gets the pointer, while a
direct-chat turn in a PROJECT ROOM with no workspace bound keeps the handbook.
Project MEMBERSHIP is deliberately not the signal — an id in a room does not mean
the work left Ouroboros's body.

The TIER-0 protected core (SYSTEM, BIBLE, identity, scratchpad, knowledge index,
recent dialogue) is ALWAYS full in every mode (BIBLE P1 cognitive-horizon / P4)
and is declared here as a data invariant. Memory-section SIZE (not inclusion) is
governed separately by consolidation granularity, not by this layout.

No imports from ``ouroboros.context`` (avoids a circular import); docs are read
directly via ``env.repo_path``.
"""

from __future__ import annotations

from typing import Any, List

# Protected core: always rendered in full, in every context mode. Encoded as
# data so a drift-guard test can assert no future change demotes it.
TIER0_ALWAYS_FULL = frozenset({
    "system",
    "bible",
    "identity",
    "scratchpad",
    "knowledge_index",
    "recent_dialogue",
})


def _read_doc(env: Any, rel_path: str) -> str:
    try:
        return env.repo_path(rel_path).read_text(encoding="utf-8")
    except Exception:
        return ""


def generate_doc_nav_map(text: str, *, title: str, rel_path: str) -> str:
    """Build a compact, fence-aware navigation map of a markdown doc.

    Lists every ``##`` through ``####`` heading with its inclusive line range
    so the agent knows what exists and where, and can pull the full section on demand via
    ``read_file(root="system_repo", path=rel_path, start_line=A, max_lines=N)``.
    A parent's range includes its complete descendant group, so parent and child
    ranges intentionally overlap. This is a lossless index
    (P1: no silent truncation) — the single canonical file on disk is unchanged.
    """
    lines = text.splitlines()
    total = len(lines)
    headings: List[tuple[int, str, int]] = []  # (level, title, 1-based line)
    in_fence = False
    for i, line in enumerate(lines, start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("## "):
            headings.append((2, line[3:].strip(), i))
        elif line.startswith("### "):
            headings.append((3, line[4:].strip(), i))
        elif line.startswith("#### "):
            headings.append((4, line[5:].strip(), i))

    out = [
        f"## {title} (navigation map)",
        "",
        f"Full text is NOT inlined to keep the working context window fit. Read any "
        f"section on demand with `read_file(root=\"system_repo\", path=\"{rel_path}\", "
        f"start_line=A, max_lines=N)` (untruncated). Ranges are inclusive; a "
        f"parent includes its complete descendant group, and `max_lines=B-A+1` "
        f"for `lines A-B`. Sections:",
        "",
    ]
    if not headings:
        out.append(f"- (no `##`/`###`/`####` headings; read `{rel_path}` directly)")
    for idx, (level, htitle, lineno) in enumerate(headings):
        end = total
        for later_level, _later_title, later_lineno in headings[idx + 1:]:
            if later_level <= level:
                end = later_lineno - 1
                break
        indent = "  " * (level - 2)
        out.append(f"{indent}- {htitle} — lines {lineno}-{end}")
    return "\n".join(out)


def architecture_context_section(
    env: Any,
    *,
    context_mode: str,
    architecture_full: bool = True,
    text: str | None = None,
) -> str:
    """ARCHITECTURE.md form per mode and task class.

    v6.115.0 (owner decision): full residency in owner-max is class-scoped —
    self-body classes keep the full document; direct-chat turns and
    externally-bound surfaces (external workspaces, project trees, subagents,
    external api/cli/scheduled surfaces) get the lossless H2-H4 navigation map
    plus a visible on-demand pointer. Low mode is unchanged: navigation map for
    every class. The default ``architecture_full=True`` keeps non-task callers
    (consciousness governance sections) at the documented full-in-max
    behavior. Empty if unreadable."""
    if text is None:
        text = _read_doc(env, "docs/ARCHITECTURE.md")
    if not text.strip():
        return ""
    if context_mode == "low" or not architecture_full:
        return generate_doc_nav_map(
            text, title="ARCHITECTURE.md", rel_path="docs/ARCHITECTURE.md"
        )
    return "## ARCHITECTURE.md\n\n" + text


def reference_doc_sections(
    env: Any,
    *,
    context_mode: str,
    include_development: bool,
    architecture_full: bool = True,
    development_full: bool = True,
    architecture_text: str | None = None,
    development_text: str | None = None,
) -> List[str]:
    """Return the reference-doc parts for the always-on static block.

    SYSTEM.md and BIBLE.md are tier-0 and added by the caller; this owns
    ARCHITECTURE / DEVELOPMENT / README / CHECKLISTS per the doc matrix. Anything
    not inlined is named in a single visible on-demand pointer (P1: no silent
    omission).

    ``context_mode`` is the OWNER context mode; together with
    ``architecture_full`` and ``development_full`` it decides the
    ARCHITECTURE / DEVELOPMENT forms in owner-max (v6.115.0 / v6.116.0 owner
    decisions: full for self-body classes; direct chat gets the lossless nav
    map + on-demand pointer — for ARCHITECTURE.md and DEVELOPMENT.md
    respectively; external surfaces keep the pointer-only DEVELOPMENT posture
    via ``include_development=False``, so ``development_full`` is moot there;
    nav map for every class in low). ``include_development`` is the caller's
    mode-independent decision whether the self-engineering handbook is inline
    (self-body/self-mod/evolution work) or an on-demand pointer (project tasks
    — folder or not — and external surfaces).
    """
    parts: List[str] = []
    on_demand: List[str] = []

    arch_section = architecture_context_section(
        env,
        context_mode=context_mode,
        architecture_full=architecture_full,
        text=architecture_text,
    )
    if arch_section:
        parts.append(arch_section)
        if context_mode != "low" and not architecture_full:
            # v6.115.0: owner-max nav class — the nav map is disclosed a second
            # time in the visible on-demand pointer (P1: named, never silent).
            # Low keeps its established form (the nav map's own read_file
            # instruction is the disclosure; no pointer entry).
            on_demand.append("docs/ARCHITECTURE.md")

    dev_text = (
        development_text
        if development_text is not None
        else _read_doc(env, "docs/DEVELOPMENT.md")
    )
    if dev_text.strip():
        if include_development:
            # v6.116.0 (owner decision, the ARCHITECTURE mirror): full residency
            # in owner-max is class-scoped — the direct-chat class renders the
            # lossless nav map + a disclosed on-demand pointer (P1: named,
            # never silent); self-body classes keep the full document. Low mode
            # ignores the flag: the full document stays the low form (its
            # posture is separately test-pinned).
            if context_mode != "low" and not development_full:
                parts.append(
                    generate_doc_nav_map(
                        dev_text,
                        title="DEVELOPMENT.md",
                        rel_path="docs/DEVELOPMENT.md",
                    )
                )
                on_demand.append("docs/DEVELOPMENT.md")
            else:
                parts.append("## DEVELOPMENT.md\n\n" + dev_text)
        else:
            on_demand.append("docs/DEVELOPMENT.md")

    # README (user-facing) and CHECKLISTS (reviewers load their own copy) are not
    # inlined in the agent context in any mode.
    on_demand.extend(["README.md", "docs/CHECKLISTS.md"])

    if on_demand:
        listing = ", ".join(f"`{p}`" for p in on_demand)
        parts.append(
            "## Reference docs available on demand\n\n"
            f"Not inlined in the working context: {listing}. "
            "Read them in full (untruncated) with `read_file(root=\"system_repo\", path=...)` when relevant."
        )
    return parts
