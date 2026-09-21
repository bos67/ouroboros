"""Final-text integrity gate at the terminal delivery seam (v6.119.5).

The seam stamps typed facts beside degenerate repetition-loop finals instead of
rewriting or blocking them (delivery never mutates an answer). Calibration was
done once against two real incidents (tasks 74c83c57, e38b486c: manifest-loop
finals measured trigram uniqueness 0.569, top-trigram repeats 26-27) against
clean finals (1ae96feb/451177be: uniqueness 0.986-0.997, repeats <=4); these
tests pin the behavior with deterministic synthetic corpora shaped like those
measurements, not with live data-drive reads (tests must stay hermetic).
"""

import pytest

from ouroboros.task_finalization import (
    final_text_integrity_facts,
    prepare_terminal_send_event,
    terminal_result_fields,
)


def _loop_corpus(repeats: int = 30) -> str:
    """Deterministic repetition-loop-shaped corpus (~420 words).

    Cycles a small phrase pool with tiny variations so most trigrams collide —
    mirrors the measured manifest-loop shape.
    """
    pool = [
        "the manifest carries attachments",
        "the attachments manifest the manifest",
        "the transport carried the envelope",
        "the envelope carries the transport",
        "the carrier maps the frame",
        "the frame maps the carrier",
    ]
    words: list[str] = []
    count = 0
    while len(words) < 60 * 7:  # comfortably past the 60-word applicability floor
        for i, phrase in enumerate(pool):
            count += 1
            suffix = " and onward" if count % 3 == 0 else ""
            words.extend(phrase.split())
            if suffix:
                words.extend(suffix.split())
    sent = " ".join(words)
    # A distinct tail tube so unique_trigram_ratio, not its absence, drives the
    # verdict — the corpus must look like a summary followed by a collapsed loop.
    tail = (
        "In summary the loop continued the manifest carries attachments "
        "again and again without reaching any conclusion at all."
    )
    return ".".join([f" {sent}." for _ in range(repeats)]) + f" {tail}"


def _single_stutter(repeats: int = 20) -> str:
    """One shingle stuttered ~20x inside otherwise ALL-unique text: ONLY the
    top-repeats branch may fire (uniqueness stays ~0.97)."""
    words: list[str] = []
    for i in range(600):
        words += [f"w{i}_{j}" for j in range(3)]
        if i == 300:
            words += ["alpha", "beta", "gamma"] * repeats
    return " ".join(words)


def _varied_loop() -> str:
    """Every shingle appears just twice: ONLY the uniqueness branch may fire
    (top repeats = 2, well under the floor; window uniqueness collapses)."""
    pool = [
        f"{chr(97 + k)} note {k * 7} greeting {k * 3} horizon {k * 5} beacon"
        for k in range(16)
    ]
    return " ".join(pool * 2)


def _clean_corpora() -> list[str]:
    return [
        ("The extraction moved the file-pack block into review_pack_files with "
         "a compatibility re-export plane preserving historical imports and "
         "monkeypatch targets. The size-ratchet manifest was regenerated; "
         "carriers were synchronized across the nine version surfaces. "
         "Independent verification diffed the old module's surface against the "
         "new one and confirmed every retained name, including the identity "
         "pin on the shared iterator. Three residual documentation issues from "
         "the previous release were fixed in the same pass."),
        ("Swap activation survived the reboot because fstab now references the "
         "swap file by path, not by UUID. The worker rederived its commit "
         "identity from git HEAD at startup and the physical log line showed "
         "the expected hash equal to the observed one. Queue and scheduled "
         "tasks were empty, so the restart settled without orphaned work. "
         "The push relay verification matched every remote reference bit for "
         "bit before the tree was declared clean."),
    ]


class TestFinalTextIntegrityFacts:
    def test_repetition_loop_flags_degenerate(self):
        facts = final_text_integrity_facts(_loop_corpus())
        assert facts["degenerate"] is True
        assert facts["trigram_uniqueness"] < 0.92
        assert facts["top_trigram_repeats"] > 12  # matches measured 26-27 range
        # Egressable mask carries the numbers the report will quote.
        assert facts["frame"].startswith("final_text_integrity:")
        assert "degenerate=False" not in facts["frame"]

    def test_single_phrase_stutter_trips_even_at_high_uniqueness(self):
        corpus = _single_stutter()
        default_answer = final_text_integrity_facts(corpus)
        assert default_answer["degenerate"] is True
        assert default_answer["top_trigram_repeats"] > 12
        assert default_answer["trigram_uniqueness"] >= 0.92  # uniqueness branch silent
        forced_off = final_text_integrity_facts(
            corpus, top_ngram_repeats_threshold=10**6,
        )
        assert forced_off["degenerate"] is False  # OR verified: only repeats fired

    def test_varied_loop_trips_only_on_window_uniqueness(self):
        corpus = _varied_loop()
        default_answer = final_text_integrity_facts(corpus)
        assert default_answer["degenerate"] is True
        assert default_answer["trigram_uniqueness"] < 0.92
        assert default_answer["top_trigram_repeats"] <= 12  # repeats branch silent
        forced_off = final_text_integrity_facts(
            corpus, trigram_uniqueness_threshold=0.0,
        )
        assert forced_off["degenerate"] is False  # OR verified: only uniqueness fired

    def test_clean_text_passes_clearly(self):
        for corpus in _clean_corpora():
            facts = final_text_integrity_facts(corpus)
            assert facts["degenerate"] is False, facts
            assert facts["trigram_uniqueness"] > 0.92
            # No mask on a clean frame.

    def test_short_text_not_applicable(self):
        assert final_text_integrity_facts("too short to judge") == {}

    def test_empty_and_none_not_applicable(self):
        assert final_text_integrity_facts("") == {}
        assert final_text_integrity_facts(None) == {}


class TestSeamStamp:
    def test_degenerate_final_stamps_usage_and_frame_meta(self, tmp_path):
        usage: dict = {"terminal_origin": "model_final"}
        event = {"type": "send_message", "task_id": "t1", "chat_id": 1}
        prepare_terminal_send_event(
            tmp_path, {"id": "t1"}, _loop_corpus(), usage, event,
            ephemeral=False, presence=False,
        )
        facts = usage.get("final_text_integrity") or {}
        assert facts.get("degenerate") is True
        stamp = event.get("progress_meta", {}).get("final_text_integrity") or {}
        assert stamp.get("degenerate") is True

    def test_clean_final_reports_facts_without_frame_stamp(self, tmp_path):
        usage: dict = {}
        event = {"type": "send_message"}
        prepare_terminal_send_event(
            tmp_path, {"id": "t2"}, _clean_corpora()[0], usage, event,
            ephemeral=False, presence=False,
        )
        assert (usage.get("final_text_integrity") or {}).get("degenerate") is False
        assert not event.get("progress_meta")  # no integrity key, no unrelated keys

    def test_terminal_result_fields_only_on_degenerate(self):
        degenerate_usage = {"final_text_integrity": {"degenerate": True}}
        fields = terminal_result_fields(degenerate_usage)
        assert fields["final_text_integrity"]["degenerate"] is True
        clean_usage = {"final_text_integrity": {"degenerate": False}}
        assert "final_text_integrity" not in terminal_result_fields(clean_usage)

    def test_ephemeral_path_also_stamps(self, tmp_path):
        # The stamp sits BEFORE the early returns: every delivery path carries it.
        usage: dict = {}
        event = {"type": "send_message", "task_id": "te"}
        prepare_terminal_send_event(
            tmp_path, {"id": "te", "_ephemeral_turn": True}, _loop_corpus(),
            usage, event, ephemeral=True, presence=False,
        )
        assert (usage.get("final_text_integrity") or {}).get("degenerate") is True
        assert event["progress_meta"]["task_terminal_status"] == "completed"  # existing behavior intact
        assert event["progress_meta"]["final_text_integrity"]["degenerate"] is True

    @pytest.mark.parametrize("corpus", _clean_corpora())
    def test_short_clean_keeps_meta_untouched(self, tmp_path, corpus):
        event = {"type": "send_message"}
        prepare_terminal_send_event(
            tmp_path, {"id": "tc"}, corpus[:60], {}, event,
            ephemeral=False, presence=False,
        )
        assert not event.get("progress_meta") or \
            all(k in ("task_phase", "task_terminal_status")
                for k in event["progress_meta"])

    def test_existing_integrity_stamp_is_overwritten_by_sole_writer(self, tmp_path):
        usage: dict = {"terminal_origin": "model_final"}
        event = {
            "type": "send_message", "task_id": "tw", "chat_id": 1,
            "progress_meta": {"final_text_integrity": {"degenerate": False}},
        }
        prepare_terminal_send_event(
            tmp_path, {"id": "tw"}, _loop_corpus(), usage, event,
            ephemeral=False, presence=False,
        )
        stamp = event["progress_meta"]["final_text_integrity"]
        assert stamp["degenerate"] is True  # write-wins: the seam is the sole writer

    def test_integrity_key_survives_history_replay_allowlist(self):
        from ouroboros.gateway.history import _PROGRESS_META_FIELDS

        assert "final_text_integrity" in _PROGRESS_META_FIELDS
