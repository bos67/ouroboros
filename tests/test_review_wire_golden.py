"""Golden replay of real reviewer wire responses (provider-failure fixtures).

Ported pattern (not merged code): ``tests/fixtures/llm_golden@33da7a4f``
(razzant/ouroboros v7.4.5). The material is ours: every case is a real wire
response recorded by the commit gate in ``data/state/advisory_review.json``
(triad seats and the scope slot), including the degenerate outputs — prose
verdicts without a JSON array, refusal prose with a buried ``[]`` sentinel,
provider 504/worker-lost error envelopes — that previously cost paid gate
attempts to discover.

The contract under test is the classification seam, not the network:
``parse_model_review_results`` (triad) and
``extract_json_array`` → ``normalize_scope_items`` → ``_classify_scope_findings``
(scope). Expected values were re-derived at fixture-build time by replaying
each case through this same production code and asserting equality with the
ledger-recorded status, so the fixtures pin behavior, not hand-written labels.

Each fixture carries the case's provenance: source attempt timestamp, recorded
status and sha256 of the raw response. No credentials or prompts are stored —
responses only.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from ouroboros.tools.scope_review import _classify_scope_findings
from ouroboros.tools.scope_review_contract import normalize_scope_items
from ouroboros.triad_review import extract_json_array, parse_model_review_results

FIXTURE_DIR = pathlib.Path(__file__).parent / "fixtures" / "review_wire_golden"


def _load(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


TRIAD_FIXTURE = _load("triad_responses.json")
SCOPE_FIXTURE = _load("scope_responses.json")

TRIAD_CASES = {c["case"]: c for c in TRIAD_FIXTURE["cases"]}
SCOPE_CASES = {c["case"]: c for c in SCOPE_FIXTURE["cases"]}


def test_fixture_provenance_is_complete():
    """Every case names the ledger it came from and the sha256 of its raw text."""
    for case in TRIAD_FIXTURE["cases"] + SCOPE_FIXTURE["cases"]:
        prov = case["provenance"]
        assert prov["ledger"] == "data/state/advisory_review.json", case["case"]
        assert prov["attempt_ts"], case["case"]
        assert len(prov["raw_text_sha256"]) == 64, case["case"]
        assert prov["recorded_status"] == case["expected"]["status"], case["case"]


@pytest.mark.parametrize("case", list(TRIAD_CASES), ids=list(TRIAD_CASES))
def test_triad_wire_replay_matches_expected(case: str):
    record = TRIAD_CASES[case]
    parsed = parse_model_review_results({"results": [record["envelope"]]})
    assert len(parsed.actor_records) == 1, case
    actor = parsed.actor_records[0]
    exp = record["expected"]
    assert actor.status == exp["status"], f"{case}: {actor.status!r} != {exp['status']!r}"
    assert len(actor.parsed_items) == exp["parsed_items"], case
    assert (actor.status == "responded") == exp["quorum_contribution"], case
    # Degenerate statuses must never enter the quorum.
    if actor.status != "responded":
        assert parsed.responsive_models == [], case


def test_triad_partial_wave_keeps_quorum_degraded():
    """The release-6.119.11 wave (real): grok prose-failure + luna + glm.

    Two of three real seats responded — quorum met but DEGRADED must be
    recorded with the parse_failure named. This is the live shape that kept
    a paid gate attempt honest; it must stay pinned.
    """
    wave = [TRIAD_CASES[n]["envelope"] for n in
            ("luna_responded_items", "glm_responded_items", "grok_prose_verdict_pf")]
    parsed = parse_model_review_results({"results": wave})
    assert parsed.quorum_met is True
    assert any("parse_failure" in reason for reason in parsed.degraded_reasons)
    assert sum(1 for r in parsed.actor_records if r.status == "responded") == 2
    assert sum(1 for r in parsed.actor_records if r.status == "parse_failure") == 1


def test_triad_clean_vs_refusal_sentinel_pair():
    """Two real minimax responses, same model slot, opposite verdicts.

    The 15-byte fenced-sentinel response IS a clean no-findings verdict;
    refusal prose with ``[]NO_FINDINGS`` glued to analysis is a parse_failure
    and must not enter the quorum. Anti-refusal contract, pinned by wire.
    """
    clean = TRIAD_CASES["minimax_sentinel_clean"]
    refusal = TRIAD_CASES["minimax_refusal_pf"]
    assert parse_model_review_results({"results": [clean["envelope"]]}).actor_records[0].status == "responded"
    parsed = parse_model_review_results({"results": [refusal["envelope"]]})
    actor = parsed.actor_records[0]
    assert actor.status == "parse_failure"
    assert parsed.responsive_models == []


@pytest.mark.parametrize("case", list(SCOPE_CASES), ids=list(SCOPE_CASES))
def test_scope_wire_replay_matches_expected(case: str):
    record = SCOPE_CASES[case]
    text = record["raw_text"]
    exp = record["expected"]
    items = extract_json_array(text, normalize=True)
    assert items is not None, f"{case}: scope seam requires extractable JSON here"
    parsed, contract_error = normalize_scope_items(items)
    assert bool(contract_error) == exp["contract_error"], case
    if exp["status"] == "parse_failure":
        assert contract_error, f"{case}: contract violation must carry the reason"
        return
    critical, advisory = _classify_scope_findings(parsed)
    assert exp["status"] == "responded", case
    assert len(parsed) == exp["parsed_items"], case
    assert len(critical) == exp["critical_count"], case
    assert len(advisory) == exp["advisory_count"], case


def test_scope_responded_case_preserves_real_findings():
    """The deepseek scope response of 2026-09-16 carried one critical and two
    advisory findings; the seam must recover exactly that classification."""
    record = SCOPE_CASES["deepseek_scope_responded"]
    items = extract_json_array(record["raw_text"], normalize=True)
    parsed, contract_error = normalize_scope_items(items)
    assert not contract_error
    critical, advisory = _classify_scope_findings(parsed)
    assert [f["item"] for f in critical] == ["prompt_doc_sync"]
    assert {f["item"] for f in advisory} == {"cross_surface_consistency", "cross_module_bugs"}


def test_error_wire_never_counts_as_quorum():
    """Provider error envelopes (504 upstream, worker-lost) are errors, not
    responses: replayed waves of pure errors fail quorum loudly."""
    errors = [TRIAD_CASES[n]["envelope"] for n in
              ("deepseek_504_error", "luna_worker_lost_error")]
    parsed = parse_model_review_results({"results": errors})
    assert parsed.quorum_met is False
    assert parsed.responsive_models == []
    assert all(r.status == "error" for r in parsed.actor_records)
