"""Nearest-match recovery hints for the edit family and path resolution.

Two pure helpers, no policy imports — the recovery rail for the measured
stale-anchor class (edit_text 13.1% -> 22.5% error rate, edit_batch 19.2%,
2026-09-18 error-rate recheck): when an exact ``old_str`` miss or a missing
path aborts an edit, the error now carries the closest real fragments/paths so
the next attempt can succeed WITHOUT an extra read round-trip.

Extraction precedent: ``advisory_pack_policy.py`` — a leaf module beside the
edit tools keeps ``core.py`` / ``git.py`` / ``edit_ops.py`` at their size-ratchet
positions. The hint is ADDITIVE diagnostic text on an existing typed error:
the miss is still a refusal (nothing is written, atomicity unchanged), never a
silent fuzzy write.
"""

from __future__ import annotations

import difflib
import os
import pathlib

# Bounded scan: hints are diagnostics, not a second indexing system.
_MAX_HINT_LINES = 5000
_MAX_WALK_ENTRIES = 2000
_MAX_WALK_DIRS = 500
_MAX_WALK_DEPTH = 6


def nearest_fragment_hints(text: str, old_str: str, max_hints: int = 3) -> str:
    """Closest fragments to a missed ``old_str``, formatted for an error message.

    Slides a window of ``old_str``'s line count over the file (capped) and ranks
    windows by ``difflib.SequenceMatcher`` ratio. Returns "" when nothing is
    close enough — the caller's plain error is already sufficient then.
    """
    needle_lines = old_str.split("\n")
    needle = "\n".join(needle_lines).strip()
    if not needle:
        return ""
    window = len(needle_lines)
    lines = text.split("\n")
    if len(lines) > _MAX_HINT_LINES:
        lines = lines[:_MAX_HINT_LINES]
    scored: list[tuple[float, int, str]] = []
    for i in range(0, max(1, len(lines) - window + 1)):
        candidate = "\n".join(lines[i:i + window]).strip()
        if not candidate:
            continue
        ratio = difflib.SequenceMatcher(None, needle, candidate).ratio()
        if ratio >= 0.4:
            scored.append((ratio, i, candidate))
    if not scored:
        return ""
    scored.sort(key=lambda item: (-item[0], item[1]))
    parts: list[str] = ["Nearest matching fragments:"]
    for ratio, i, candidate in scored[:max_hints]:
        first = candidate.split("\n")[0]
        preview = first[:120]
        # Egress seam (P3/security): a runtime-data or repo file may hold
        # credential-shaped content; hints are model-visible error text, so the
        # preview rides the same mask_secret_bytes path as every other egress.
        from ouroboros.secret_masking import mask_secret_bytes
        preview, _masked = mask_secret_bytes(preview)
        parts.append(f"  ~line {i + 1} ({ratio:.0%}): {preview}")
    return "\n".join(parts)


def suggest_similar_paths(base: pathlib.Path, rel: str, max_suggestions: int = 5) -> str:
    """Existing paths under ``base`` closest to a missing ``rel``.

    Walks ``base`` bounded on BOTH axes (os.walk: depth cap AND a combined
    entries+directories budget, symlinked directories skipped), then ranks the
    collected relative paths by ``difflib.get_close_matches``. Returns "" when
    the tree is empty or nothing is plausibly close — no suggestion is better
    than a wrong suggestion.
    """
    needle = str(rel or "").strip().replace("\\", "/")
    if not needle or not base.is_dir():
        return ""
    candidates: list[str] = []
    visited_dirs = 0
    try:
        for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
            visited_dirs += 1
            if visited_dirs > _MAX_WALK_DIRS or len(candidates) >= _MAX_WALK_ENTRIES:
                break
            root_rel = pathlib.Path(dirpath).relative_to(base)
            depth = 0 if root_rel == pathlib.Path(".") else len(root_rel.parts)
            if depth >= _MAX_WALK_DEPTH:
                dirnames[:] = []
            # Prune symlinked directories: followlinks=False keeps os.walk honest,
            # but the entries still need pruning out of the descent plan.
            dirnames[:] = [
                d for d in dirnames
                if not (pathlib.Path(dirpath) / d).is_symlink()
            ]
            for name in filenames:
                rel_path = (root_rel / name).as_posix()
                if rel_path != ".":
                    candidates.append(rel_path)
                    if len(candidates) >= _MAX_WALK_ENTRIES:
                        break
    except OSError:
        return ""
    if not candidates:
        return ""
    close = difflib.get_close_matches(needle, candidates, n=max_suggestions, cutoff=0.5)
    if not close:
        return ""
    parts = ["Nearest existing paths under this root:"]
    parts.extend(f"  - {c}" for c in close)
    return "\n".join(parts)
