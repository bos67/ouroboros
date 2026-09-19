"""Dense shared file/text primitives for the review stack (6.118.3).

Leaf module extracted from ``ouroboros/tools/review_helpers.py`` so that file
stays none-debt again after 6.118.2 pushed it to exactly 1600 lines (the
official-CI ratchet is shrink-only pairwise; touching review_helpers would
have then blocked every next release). Extraction pattern matches the
6.118.0 ``advisory_pack_policy`` precedent: a text-dense leaf module owning
primitives, while ``review_helpers`` keeps a thin re-export plane so every
historical import path and monkeypatch target keeps working.

Owned here:

- File-classification constants: binary/vendored/sensitive denylists shared
  by legacy pack helpers and generated atlases, plus the full-repo scan
  constants (skip prefixes, size caps, sniff bound).
- Secret redaction before prompt injection (``redact_prompt_secrets``) and
  collision-safe prompt fencing (``_make_fence`` / ``format_prompt_code_block``).
- Binary sniffing (``_raw_bytes_binary`` / ``_is_probably_binary``).
- Full-repack scanning (``list_git_tracked_paths`` / ``iter_repo_pack_entries``
  / ``build_full_repo_pack``) — the scope-atlas and size-ratchet lane feeds.
- HEAD / skill-payload snapshot rendering (``build_head_snapshot_section``).
- The touched-file pack builders (``build_touched_file_pack``) with the
  managed-resolution ``m0_tree`` / ``staged_tree`` binary-metadata contract
  and the advisory ``inline_policy`` shims.

No imports from other ``ouroboros.tools`` modules at import time except the
version-sync re-export home and the lazy in-function seams that already
existed (advisory_pack_policy, review_binary_context) — both bodies import
back lazily by the same contract, never at module import time.
"""
from __future__ import annotations

import logging
import os
import re
import subprocess
from pathlib import Path

from ouroboros.utils import sanitize_tool_result_for_log

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt text primitives (redaction + collision-safe fencing)
# ---------------------------------------------------------------------------

_SECRET_LINE_RE = re.compile(
    r'(?im)^(\s*(?:export\s+)?[A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|PASSWD|PASSPHRASE|API[_-]?KEY|AUTHORIZATION)[A-Z0-9_]*\s*[:=]\s*)(.+)$'
)
_JSON_SECRET_RE = re.compile(
    r'(?i)("?(?:token|api[_-]?key|authorization|secret|password|passwd|passphrase)"?\s*:\s*)"([^"\n\r]{4,})"'
)


def redact_prompt_secrets(text: str) -> tuple[str, bool]:
    """Redact secret-like values before prompt injection."""
    if not isinstance(text, str) or not text:
        return text, False

    redacted = sanitize_tool_result_for_log(text)
    redacted = _SECRET_LINE_RE.sub(r"\1***REDACTED***", redacted)
    redacted = _JSON_SECRET_RE.sub(r'\1"***REDACTED***"', redacted)
    return redacted, redacted != text


def _make_fence(content: str) -> str:
    longest = 0
    current = 0
    for ch in str(content or ""):
        if ch == "`":
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return "`" * max(3, longest + 1)


def format_prompt_code_block(content: str, language: str = "") -> str:
    """Fence content with a delimiter that cannot collide with the body."""
    fence = _make_fence(content)
    lang = language or ""
    return f"{fence}{lang}\n{content}\n{fence}"


# ---------------------------------------------------------------------------
# File-classification constants shared by legacy pack helpers and atlases
# ---------------------------------------------------------------------------

BINARY_EXTENSIONS = frozenset({
    # Compiled/archive
    ".so", ".dylib", ".dll", ".pyc", ".whl", ".egg",
    ".zip", ".tar", ".gz", ".bz2",
    # Images/icons
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".icns", ".webp", ".bmp", ".tiff", ".svg",
    # Fonts
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    # Other binary blobs
    ".pdf", ".db", ".sqlite", ".sqlite3",
    ".mp3", ".mp4", ".wav", ".ogg", ".flac",
    ".exe", ".pyo",
})

_FILE_SIZE_LIMIT = 1_048_576  # 1 MB per file

# File-classification constants shared by legacy pack helpers and generated atlases.
_SENSITIVE_EXTENSIONS = frozenset({
    ".env", ".pem", ".key", ".p12", ".pfx", ".jks", ".keystore",
    # Credential vaults / encrypted blobs.
    ".kdbx", ".gpg", ".asc",
})
_SENSITIVE_NAMES = frozenset({
    ".env", ".env.local", ".env.production", ".env.staging",
    # Env-file variants are credential-shaped even when named for examples/tests.
    ".env.development", ".env.dev", ".env.test", ".env.example",
    "credentials.json", "service-account.json", "secrets.yaml", "secrets.json",
    "secrets.toml", "secrets.ini",
    "aws-credentials.json", "gcp-service-account.json",
    # SSH private keys
    "id_rsa", "id_ed25519", "id_ecdsa", "id_dsa",
    ".git-credentials", ".netrc", ".npmrc", ".pypirc",
})
_VENDORED_SUFFIXES = frozenset({".min.js", ".min.css", ".min.mjs"})
_VENDORED_NAMES = frozenset({"chart.umd.min.js"})
_FULL_REPO_BINARY_EXTENSIONS = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".icns", ".webp", ".bmp", ".tiff",
    ".svg", ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".pdf", ".zip", ".tar", ".gz", ".bz2",
    ".pyc", ".pyo", ".so", ".dylib", ".dll", ".exe",
    ".mp3", ".mp4", ".wav", ".ogg", ".flac",
    ".db", ".sqlite", ".sqlite3",
})
_FULL_REPO_SKIP_DIR_PREFIXES = (
    ".cursor/", ".github/", ".vscode/", ".idea/", "assets/",
    # Operator/devtools sources are tracked and reviewed when touched, but are
    # not core runtime context for unrelated broad scope packs.
    "devtools/",
    # Full pack excludes tests; touched tests are still sent separately.
    "tests/",
)
_MAX_FULL_REPO_FILE_BYTES = 1_048_576  # 1 MB
_BINARY_SNIFF_BYTES = 8192


# ---------------------------------------------------------------------------
# Binary sniffing
# ---------------------------------------------------------------------------


def _raw_bytes_binary(sample: bytes) -> bool:
    if not sample:
        return False
    if b"\x00" in sample:
        return True
    non_text = sum(
        1 for b in sample
        if b < 9 or (13 < b < 32) or b == 127
    )
    if non_text / len(sample) > 0.30:
        return True
    try:
        import codecs
        dec = codecs.getincrementaldecoder("utf-8")("strict")
        dec.decode(sample, final=False)
    except UnicodeDecodeError:
        return True
    return False


def _is_probably_binary(path: Path) -> bool:
    """Return True if the sampled bytes look binary; false on I/O errors."""
    try:
        with path.open("rb") as fh:
            sample = fh.read(_BINARY_SNIFF_BYTES)
    except Exception:
        return False
    return _raw_bytes_binary(sample)


def _binary_omission_note(context: str) -> str:
    """Shared template for binary-omission rows (6.118.3 advisory finding):
    HEAD snapshots and the live touched-file path render from one source of truth."""
    return f"*({context} omitted — binary content detected)*\n"


# ---------------------------------------------------------------------------
# Full-repo pack scanning (scope-atlas and size-ratchet lane feeds)
# ---------------------------------------------------------------------------


def list_git_tracked_paths(repo_dir: Path) -> list[str]:
    """Return git-tracked repo paths using the normal subprocess path."""
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        err = result.stderr.strip()[:200] if result.stderr else "unknown error"
        raise RuntimeError(
            f"build_full_repo_pack: git ls-files failed (exit {result.returncode}): {err}"
        )
    return result.stdout.splitlines()


def iter_repo_pack_entries(
    repo_dir: Path,
    *,
    tracked_paths: list[str] | None = None,
    exclude_paths: set[str] | None = None,
    skip_dir_prefixes: tuple[str, ...] = _FULL_REPO_SKIP_DIR_PREFIXES,
    max_file_bytes: int = _MAX_FULL_REPO_FILE_BYTES,
    include_oversized_placeholder: bool = False,
) -> tuple[list[tuple[str, str, str, str]], list[str]]:
    """Return reviewable tracked-file entries and omissions for repo packs."""
    exclude_paths = exclude_paths or set()
    tracked = tracked_paths if tracked_paths is not None else list_git_tracked_paths(repo_dir)

    entries: list[tuple[str, str, str, str]] = []
    omitted: list[str] = []
    repo_dir_resolved = repo_dir.resolve()

    for rel in tracked:
        if rel in exclude_paths:
            continue

        rel_norm = rel.replace("\\", "/")

        if rel_norm.startswith(skip_dir_prefixes):
            omitted.append(f"{rel} (excluded dir)")
            continue

        fp = repo_dir / rel

        # Reject tracked symlinks/paths that resolve outside the repo root.
        try:
            fp_resolved = fp.resolve()
            fp_resolved.relative_to(repo_dir_resolved)
        except (OSError, ValueError):
            omitted.append(f"{rel} (path escapes repository root)")
            continue

        if not fp.is_file():
            continue

        fname = fp.name.lower()
        fsuffix = fp.suffix.lower()

        if fname in _SENSITIVE_NAMES or fsuffix in _SENSITIVE_EXTENSIONS:
            omitted.append(f"{rel} (sensitive)")
            continue

        if fsuffix in _FULL_REPO_BINARY_EXTENSIONS:
            omitted.append(f"{rel} (binary/media)")
            continue

        if fname in _VENDORED_NAMES or any(fname.endswith(s) for s in _VENDORED_SUFFIXES):
            omitted.append(f"{rel} (vendored/minified)")
            continue

        # Size guard before content sniffer.
        try:
            size = fp.stat().st_size
        except OSError:
            omitted.append(f"{rel} (stat error)")
            continue

        if size > max_file_bytes:
            omitted.append(f"{rel} (>{max_file_bytes // 1024}KB)")
            if include_oversized_placeholder:
                entries.append((rel, f"[SKIPPED: file too large ({size} bytes)]", "", ""))
            continue

        if _is_probably_binary(fp):
            omitted.append(f"{rel} (binary content)")
            continue

        try:
            content = fp.read_text(encoding="utf-8", errors="replace")
        except Exception:
            omitted.append(f"{rel} (read error)")
            logger.warning("Could not read repo file: %s", rel, exc_info=True)
            continue

        content, redacted = redact_prompt_secrets(content)
        ext = fp.suffix.lstrip(".")
        lang = ext if ext else ""
        note = "*(secret-like content redacted)*\n" if redacted else ""
        entries.append((rel, content, lang, note))

    return entries, omitted


def build_full_repo_pack(
    repo_dir: Path,
    exclude_paths: set[str] | None = None,
) -> tuple[str, list[str]]:
    """Build a filtered full-repo text pack; callers handle size limits."""
    entries, omitted = iter_repo_pack_entries(repo_dir, exclude_paths=exclude_paths)
    parts = [
        f"### {rel}\n{note}```{lang}\n{content}\n```\n\n"
        for rel, content, lang, note in entries
    ]

    return "".join(parts), omitted


# ---------------------------------------------------------------------------
# HEAD / skill-payload snapshot rendering
# ---------------------------------------------------------------------------


def build_head_snapshot_section(
    repo_dir: Path, paths: list[str], *, current_snapshots: dict[str, Path] | None = None,
) -> tuple[str, frozenset[str]]:
    """Build prompt text with HEAD or explicit current snapshots of touched files.

    ``included_paths`` names only FULL snapshots; omission markers must never
    become Atlas ``already_included`` claims (BIBLE P3 / XG-1R.4).
    """
    if not paths:
        return "(no touched files)", frozenset()
    current_by_label = {str(k).strip(): Path(v) for k, v in (current_snapshots or {}).items()}
    parts: list[str] = []
    included: set[str] = set()
    def append_bytes(rel: str, raw: bytes, source: str) -> None:
        if len(raw) > _FILE_SIZE_LIMIT:
            parts.append(
                f"### {rel}\n\n*({source} omitted — {len(raw):,} bytes exceeds "
                f"{_FILE_SIZE_LIMIT:,} byte limit)*\n"
            )
        elif _raw_bytes_binary(raw[:_BINARY_SNIFF_BYTES]):
            parts.append(f"### {rel}\n\n{_binary_omission_note(source)}")
        else:
            lang = Path(rel).suffix.lstrip(".")
            note = f"*{source}*\n\n" if source != "HEAD snapshot" else ""
            content = raw.decode("utf-8", errors="replace")
            parts.append(f"### {rel}\n\n{note}{format_prompt_code_block(content, lang)}\n")
            included.add(rel)

    for rel in paths:
        fp_rel = Path(rel)
        suffix = fp_rel.suffix.lower()
        current_path = current_by_label.get(str(rel).strip())
        source = "Current skill-payload snapshot (data plane, not Git HEAD)" if current_path else "HEAD snapshot"
        fname_lower = fp_rel.name.lower()
        if suffix in _SENSITIVE_EXTENSIONS or fname_lower in _SENSITIVE_NAMES:
            parts.append(f"### {rel}\n\n*({source} omitted — sensitive file)*\n")
            continue
        if suffix in BINARY_EXTENSIONS:
            parts.append(f"### {rel}\n\n*({source} omitted — binary file ({suffix}))*\n")
            continue
        try:
            if current_path is not None:
                if not current_path.is_file():
                    parts.append(
                        f"### {rel}\n\n*(Current skill-payload snapshot unavailable — "
                        "file does not exist or is not a regular file)*\n"
                    )
                else:
                    append_bytes(rel, current_path.read_bytes(), source)
                continue
            result = subprocess.run(
                ["git", "show", f"HEAD:{rel}"],
                cwd=repo_dir,
                capture_output=True,
                timeout=10,
                env={**os.environ, "LC_ALL": "C", "LANG": "C", "LANGUAGE": "C"},
            )
            if result.returncode == 0 and result.stdout:
                append_bytes(rel, result.stdout, source)
                continue
            if result.returncode != 0:
                raw_stderr = result.stderr or b""
                stderr_str = (
                    raw_stderr.decode("utf-8", errors="replace")
                    if isinstance(raw_stderr, (bytes, bytearray))
                    else str(raw_stderr)
                )
                stderr_lower = stderr_str.lower()
                is_new_file = (
                    "does not exist" in stderr_lower
                    or "exists on disk" in stderr_lower
                    or "path not in" in stderr_lower
                    or "not in 'head'" in stderr_lower
                )
                if is_new_file:
                    parts.append(f"### {rel}\n\n*(File is new — no HEAD snapshot)*\n")
                else:
                    short_err = stderr_str.strip()[:200]
                    parts.append(f"### {rel}\n\n*(HEAD snapshot error — git exited {result.returncode}: {short_err})*\n")
            elif not result.stdout:
                parts.append(f"### {rel}\n\n*(HEAD snapshot was empty)*\n")
        except subprocess.TimeoutExpired:
            parts.append(f"### {rel}\n\n*(HEAD snapshot timeout)*\n")
        except Exception as exc:
            parts.append(f"### {rel}\n\n*(HEAD snapshot error: {exc})*\n")

    return "\n".join(parts), frozenset(included)


# ---------------------------------------------------------------------------
# Touched-file pack
# ---------------------------------------------------------------------------


def build_touched_file_pack(
    repo_dir: Path,
    paths: list[str] | None = None,
    *,
    represent_binary: bool = False,
    m0_tree: str = "",  # managed resolutions: binary rows carry the M0 baseline identity
    staged_tree: str = "",
    inline_policy: str = "full",
) -> tuple[str, list[str]]:
    """Read changed files into a prompt code pack plus omission list.

    ``inline_policy``: ``"full"`` (default) inlines content up to
    ``_FILE_SIZE_LIMIT`` exactly as before — every non-advisory caller keeps
    its contract byte-for-byte. ``"compact"`` (advisory touched pack)
    renders metadata rows via ``compact_omission_row`` (advisory_pack_policy
    leaf) instead of content for lockfiles and files ≥ 128 KB; every such
    row names the reason and the byte size — no silent truncation.
    """
    if paths is None:
        from ouroboros.tools.review_helpers import list_changed_paths_from_git_status
        paths = list_changed_paths_from_git_status(repo_dir)

    parts: list[str] = []
    omitted: list[str] = []
    repo_dir_resolved = repo_dir.resolve()

    for rel in paths:
        fp = repo_dir / rel
        # Reject traversal/symlink escapes outside the repo root.
        try:
            fp_resolved = fp.resolve()
        except OSError:
            omitted.append(rel)
            parts.append(f"### {rel}\n\n*(omitted — path resolution error)*\n")
            continue
        try:
            fp_resolved.relative_to(repo_dir_resolved)
        except ValueError:
            omitted.append(rel)
            parts.append(f"### {rel}\n\n*(omitted — path escapes repository root)*\n")
            continue
        binary_extension = fp.suffix.lower() in BINARY_EXTENSIONS
        if not fp.is_file():
            from ouroboros.tools import review_binary_context as binary_context
            deleted_binary = represent_binary and (
                binary_extension or binary_context.staged_path_is_binary(
                    repo_dir, rel, m0_tree=m0_tree, staged_tree=staged_tree)
            )
            if deleted_binary:
                metadata = binary_context.render_staged_binary_metadata(repo_dir, rel, m0_tree=m0_tree)
                if metadata is not None:
                    parts.append(f"### {rel}\n\n{metadata}")
                    continue
                omitted.append(rel)
                parts.append(f"### {rel}\n\n*(omitted — deleted binary has no exact staged Git metadata)*\n")
            continue
        # Never inject credential-shaped files into review prompts.
        fname_lower = fp.name.lower()
        if fp.suffix.lower() in _SENSITIVE_EXTENSIONS or fname_lower in _SENSITIVE_NAMES:
            omitted.append(rel)
            parts.append(f"### {rel}\n\n*(omitted — sensitive file)*\n")
            continue
        if binary_extension or _is_probably_binary(fp):
            if represent_binary:
                from ouroboros.tools.review_binary_context import render_staged_binary_metadata
                metadata = render_staged_binary_metadata(repo_dir, rel, m0_tree=m0_tree)
                if metadata is None:
                    omitted.append(rel)
                    parts.append(
                        f"### {rel}\n\n"
                        "*(omitted — binary file has no readable stage-0 Git object metadata)*\n"
                    )
                    continue
                parts.append(f"### {rel}\n\n{metadata}")
                continue
            omitted.append(rel)
            parts.append(f"### {rel}\n\n{_binary_omission_note('Binary file')}")
            continue
        try:
            size = fp.stat().st_size
            from ouroboros.tools.advisory_pack_policy import compact_omission_row
            omission_row = compact_omission_row(inline_policy, fname_lower, rel, size)
            if omission_row is not None:
                omitted.append(rel)
                parts.append(omission_row)
                continue
            if size > _FILE_SIZE_LIMIT:
                omitted.append(rel)
                parts.append(f"### {rel}\n\n*(omitted — {size:,} bytes exceeds {_FILE_SIZE_LIMIT:,} byte limit)*\n")
                continue
            content = fp.read_text(encoding="utf-8", errors="replace")
        except Exception as read_exc:
            omitted.append(rel)
            logger.warning("Could not read file: %s", rel, exc_info=True)
            parts.append(f"### {rel}\n\n*(omitted — unreadable file: {read_exc})*\n")
            continue

        ext = fp.suffix.lstrip(".")
        lang = ext if ext else ""
        redacted_content, redacted = redact_prompt_secrets(content)
        note = "*(secret-like content redacted)*\n" if redacted else ""
        parts.append(f"### {rel}\n{note}{format_prompt_code_block(redacted_content, lang)}\n")

    return "\n".join(parts), omitted
