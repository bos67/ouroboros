"""Append-path tail validation contract for the usage ledger.

Pins the 2026-09-21 change in ``ouroboros/usage_ledger.py::_append_rows_locked``:
the appended TAIL is validated against the caller's already-validated history
(dense sequence across the read boundary + transition legality against the full
per-attempt state map) instead of re-validating the whole history on every
append (~107ms under the monetary lock at 17K rows in the release A/B; the
first same-day probe measured 99.2ms — same operation, ~8% run spread).
The guarantee
strength must stay identical to a full validation: same accepts, same rejects,
same exception type.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from ouroboros import usage_ledger as ul
from ouroboros.usage_ledger import (
    LEDGER_REL,
    UsageLedgerCorrupt,
    _append_rows_locked,
)


def _row(attempt_id: str, state: str, seq: int) -> dict:
    return {
        "kind": "attempt",
        "attempt_id": attempt_id,
        "state": state,
        "model": "m",
        "provider": "p",
        "seq": seq,
    }


def _legal_history() -> list[dict]:
    """a1: reserved->released; a2: reserved->dispatched->settled."""
    return [
        _row("a1", "reserved", 1),
        _row("a1", "released", 2),
        _row("a2", "reserved", 3),
        _row("a2", "dispatched", 4),
        _row("a2", "settled", 5),
    ]


def test_append_validates_only_the_tail_not_whole_history(tmp_path: pathlib.Path) -> None:
    """The validator sees the tail rows with the cross-boundary start_seq, never
    the full history — that is the whole point of the change."""
    history = _legal_history()
    captured: dict = {}

    real_validate = ul._validate_records

    def spy(records, *, start_seq: int = 1, states: dict | None = None) -> None:
        captured.setdefault("calls", []).append(
            {"rows": list(records), "start_seq": start_seq, "states": dict(states or {})}
        )
        return real_validate(records, start_seq=start_seq, states=states)

    original = ul._validate_records
    ul._validate_records = spy
    try:
        appended = _append_rows_locked(tmp_path, history, [_row("a3", "reserved", 0)])
    finally:
        ul._validate_records = original

    assert len(captured["calls"]) == 1
    call = captured["calls"][0]
    assert [r["attempt_id"] for r in call["rows"]] == ["a3"]
    assert call["start_seq"] == len(history) + 1
    # The states map carries the FULL history's per-attempt last state.
    assert call["states"] == {"a1": "released", "a2": "settled"}
    assert appended[0]["seq"] == len(history) + 1


def test_append_catches_gappy_history_argument(tmp_path: pathlib.Path) -> None:
    """A caller argument with a hole in its dense sequence is rejected with the
    same exception class the full validation would raise — nothing is appended."""
    gappy = [_row("a1", "reserved", 1), _row("a1", "released", 3)]
    with pytest.raises(UsageLedgerCorrupt, match="sequence mismatch at 2"):
        _append_rows_locked(tmp_path, gappy, [_row("a2", "reserved", 0)])
    assert not (tmp_path / LEDGER_REL).exists()


def test_append_catches_illegal_transition_against_history_states(
    tmp_path: pathlib.Path,
) -> None:
    """An attempt that reached a terminal state in the history cannot be
    resurrected by a tail row — the state map is derived from the history."""
    history = _legal_history()
    with pytest.raises(UsageLedgerCorrupt, match="changed after terminal state"):
        _append_rows_locked(tmp_path, history, [_row("a2", "reserved", 0)])


def test_append_matches_full_validation_accept_reject(tmp_path: pathlib.Path) -> None:
    """Property: the real append path (tail validation + history scan) agrees
    with a whole-history validation of the same candidate — identical accepts
    and identical exception classes. Rejects must leave no ledger file."""
    cases: list[tuple[list[dict], list[dict]]] = [
        # accept: legal new attempt on legal history
        (_legal_history(), [_row("a3", "reserved", 0)]),
        # reject: settled straight from reserved (validator transition rule)
        (
            [_row("a1", "reserved", 1)],
            [{"kind": "attempt", "attempt_id": "a1", "state": "settled", "model": "m", "provider": "p"}],
        ),
        # reject: invalid state string in the tail
        (_legal_history(), [_row("a3", "flying", 0)]),
        # reject: gappy history
        ([_row("a1", "reserved", 1), _row("a1", "released", 3)], [_row("a2", "reserved", 0)]),
        # reject: resurrect terminal attempt
        (_legal_history(), [_row("a2", "dispatched", 0)]),
    ]
    for history, rows in cases:
        ledger_path = tmp_path / "state" / "usage_attempts.jsonl"
        if ledger_path.exists():
            ledger_path.unlink()
        materialized = [
            {**raw, "seq": len(history) + i + 1} for i, raw in enumerate(rows)
        ]
        tail_error = full_error = None
        try:
            _append_rows_locked(tmp_path, history, [dict(raw) for raw in rows])
        except UsageLedgerCorrupt as exc:
            tail_error = str(exc)
        try:
            ul._validate_records([*history, *materialized])
        except UsageLedgerCorrupt as exc:
            full_error = str(exc)
        assert (tail_error is None) == (full_error is None), (history, rows)
        if tail_error is not None:
            assert tail_error == full_error, (tail_error, full_error)
            assert not ledger_path.exists(), "a rejected append must not write"
        else:
            assert ledger_path.exists()


def test_append_through_public_api_on_real_ledger(tmp_path: pathlib.Path) -> None:
    """End-to-end: dense-seq file persists, and a fresh full replay validates it."""
    from ouroboros.usage_accounting import (
        AttemptRequest,
        release_attempt,
        reserve_attempt,
    )

    reservation = reserve_attempt(
        AttemptRequest(
            model="m",
            provider="local",
            task_id="t1",
            root_task_id="t1",
            drive_root=tmp_path,
        )
    )
    release_attempt(reservation, "not_dispatched")
    raw = (tmp_path / LEDGER_REL).read_text(encoding="utf-8").splitlines()
    assert len(raw) == 2
    assert [json.loads(line)["seq"] for line in raw] == [1, 2]
    # A full authoritative replay (owns quarantine) accepts the file.
    records = ul._read_records_locked(tmp_path)
    ul._validate_records(records)
    assert [r["state"] for r in records] == ["reserved", "released"]
