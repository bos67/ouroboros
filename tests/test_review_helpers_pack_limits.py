"""Advisory touched-pack inline policies: lockfile and oversize metadata rows.

Closes the advisory-oversize class: a 730KB uv.lock once inflated the
advisory prompt to 1.6-2.2M chars. The compact policy renders lockfiles
(any size) and files above 128KB as metadata rows at the advisory call-site
only; the default ``full`` policy is byte-identical to the historical
behavior.
"""
import pathlib

from ouroboros.tools.review_helpers import (
    _ADVISORY_INLINE_FILE_LIMIT,
    _LOCKFILE_NAMES,
    build_touched_file_pack,
)

_KB = 1024


def _mk_repo(tmp_path, files: dict[str, bytes]) -> pathlib.Path:
    for rel, data in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return tmp_path


def _code_bytes(n: int) -> bytes:
    """n bytes of plausible Python code (no secrets, deterministic)."""
    line = b"x = 1  # padding line for advisory pack size fixture\n"
    reps = n // len(line) + 1
    return (line * reps)[:n]


def test_lockfile_never_inlined_any_size(tmp_path):
    for name in sorted(_LOCKFILE_NAMES):
        _mk_repo(tmp_path, {name: b"garbage-lock-content\n"})
        pack, omitted = build_touched_file_pack(
            tmp_path, [name], inline_policy="compact"
        )
        assert name in omitted, name
        assert "lockfile content not inlined" in pack, name
        assert "garbage-lock-content" not in pack, name
        (tmp_path / name).unlink()


def test_lockfile_full_policy_still_inlines(tmp_path):
    """Default full policy keeps the historical contract for other callers."""
    _mk_repo(tmp_path, {"uv.lock": b"lock-content-here\n"})
    pack, omitted = build_touched_file_pack(tmp_path, ["uv.lock"])
    assert omitted == []
    assert "lock-content-here" in pack


def test_boundary_just_below_limit_inlined(tmp_path):
    n = _ADVISORY_INLINE_FILE_LIMIT - 1
    _mk_repo(tmp_path, {"src/mod.py": _code_bytes(n)})
    pack, omitted = build_touched_file_pack(tmp_path, ["src/mod.py"], inline_policy="compact")
    assert omitted == []
    assert "padding line" in pack


def test_boundary_at_limit_metadata_row(tmp_path):
    n = _ADVISORY_INLINE_FILE_LIMIT
    _mk_repo(tmp_path, {"src/big.py": _code_bytes(n)})
    pack, omitted = build_touched_file_pack(tmp_path, ["src/big.py"], inline_policy="compact")
    assert "src/big.py" in omitted
    assert "file exceeds advisory inline limit" in pack
    assert "padding line" not in pack


def test_full_policy_identity_150kb(tmp_path):
    """inline_policy='full' (default): 150KB code file fully inlined."""
    n = 150 * _KB
    _mk_repo(tmp_path, {"src/big.py": _code_bytes(n)})
    pack, omitted = build_touched_file_pack(tmp_path, ["src/big.py"])
    assert omitted == []
    assert "padding line" in pack


def test_release_fixture_pack_below_episode_bound(tmp_path):
    """Canonical fixture (spec claim_5): 730KB uv.lock + 18 typical files.

    The compact advisory pack must stay far below the 900,000-char episode
    transcript bound that previously failed closed at 934,787.
    """
    files: dict[str, bytes] = {"uv.lock": _code_bytes(730 * _KB)}
    for i in range(14):
        files[f"ouroboros/mod_{i}.py"] = _code_bytes(48 * _KB)
    files["README.md"] = _code_bytes(30 * _KB)
    files["docs/guide.md"] = _code_bytes(40 * _KB)
    files["web/modules/api.js"] = _code_bytes(20 * _KB)
    files["tests/test_mod.py"] = _code_bytes(20 * _KB)
    assert len(files) == 19
    _mk_repo(tmp_path, files)
    pack, omitted = build_touched_file_pack(
        tmp_path, sorted(files), inline_policy="compact"
    )
    assert "uv.lock" in omitted
    # 14 x 48KB code files also exceed 128KB? No: 48KB < 128KB -> inlined.
    assert len(omitted) == 1
    pack_chars = len(pack)
    assert pack_chars < 900_000, {
        "fixture_files": {rel: len(data) for rel, data in files.items()},
        "omitted": omitted,
        "pack_chars": pack_chars,
        "episode_bound": 900_000,
        "policy": "compact",
    }
