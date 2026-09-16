"""Advisory pack inline policy + advisory changed-context adapter (6.118.0).

Leaf module extracted from ``ouroboros/tools/review_helpers.py`` when the
advisory-oversize fix pushed it over the 1600-line ratchet. Everything here
is advisory-surface only:

- ``_LOCKFILE_NAMES`` / ``_ADVISORY_INLINE_FILE_LIMIT`` — the compact inline
  policy: lockfiles are generated artifacts whose content no reviewer reads
  inline (``release_sync`` checks versions deterministically), and a single
  730 KB lock once inflated the advisory prompt past 1.6M chars — past every
  real reviewer window. Exact basenames only, matched lowercased; suffix
  matching would catch source files.
- ``compact_omission_row`` — the visible metadata row for a non-inlined
  file: names the reason and the byte size, never silent truncation.
- ``build_advisory_changed_context`` — the advisory adapter over
  ``review_helpers.build_touched_file_pack`` (imported lazily: the two
  modules reference each other by contract, not by module-level cycle).

Default policy remains ``full`` for every non-advisory caller.
"""
from __future__ import annotations

from pathlib import Path

_ADVISORY_INLINE_FILE_LIMIT = 131_072  # 128 KB — compact inline bound

_LOCKFILE_NAMES = frozenset({
    "uv.lock", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "poetry.lock", "pipfile.lock", "cargo.lock", "gemfile.lock",
    "composer.lock", "packages.lock.json", "bun.lockb",
})  # matched against the lowercased basename; keep entries lowercase


def compact_omission_row(
    inline_policy: str, fname_lower: str, rel: str, size: int
) -> str | None:
    """Return the metadata row for a file the compact policy must not inline.

    ``None`` when the file should be inlined (non-compact policy, or within
    the limit and not a lockfile). A returned row is always visible to the
    reviewer and names the reason plus the byte size.
    """
    if inline_policy != "compact":
        return None
    lockfile = fname_lower in _LOCKFILE_NAMES
    if not lockfile and size < _ADVISORY_INLINE_FILE_LIMIT:
        return None
    reason = (
        "lockfile content not inlined (generated artifact)"
        if lockfile
        else "file exceeds advisory inline limit"
    )
    return f"### {rel}\n\n*(omitted — {reason}; {size:,} bytes)*\n"


def build_advisory_changed_context(
    repo_dir: Path,
    *,
    changed_files_text: str,
    paths: list[str] | None = None,
    exclude_paths: set[str] | None = None,
    inline_policy: str = "compact",
) -> tuple[list[str], str, list[str]]:
    """Resolve changed paths and build the advisory touched-file context.

    The advisory surface opts into ``inline_policy='compact'`` here (its own
    default); other callers of ``review_helpers.build_touched_file_pack``
    keep the historical ``full`` behavior.
    """
    from ouroboros.tools.review_helpers import (
        build_touched_file_pack,
        parse_changed_paths_from_porcelain,
    )

    resolved_paths = (
        list(paths)
        if paths is not None
        else parse_changed_paths_from_porcelain(changed_files_text)
    )
    filtered_paths = [
        p for p in resolved_paths
        if p not in (exclude_paths or set())
    ]
    touched_pack, omitted = build_touched_file_pack(
        repo_dir,
        filtered_paths if filtered_paths is not None else None,
        inline_policy=inline_policy,
    )
    if not touched_pack.strip():
        touched_pack = "(no touched files)"
    return resolved_paths, touched_pack, omitted
