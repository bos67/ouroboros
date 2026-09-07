"""Unit tests for the context_layout doc-layout SSOT (low/max)."""

from pathlib import Path

from ouroboros import context_layout as cl


def test_tier0_protected_core_declared():
    """The protected always-full core is a data invariant; future context-mode
    work must not silently demote any of these (BIBLE P1 / P4)."""
    expected = {
        "system",
        "bible",
        "identity",
        "scratchpad",
        "knowledge_index",
        "recent_dialogue",
    }
    assert expected <= set(cl.TIER0_ALWAYS_FULL)


def test_nav_map_lists_h2_through_h4_as_inclusive_complete_subtrees():
    text = "\n".join([
        "# Title",                   # 1
        "intro",                     # 2
        "## Alpha",                  # 3
        "alpha BODYSENT",            # 4
        "### Shared",                # 5
        "sub intro",                 # 6
        "#### Child one",            # 7
        "child one body",            # 8
        "#### Child two",            # 9
        "child two body",            # 10
        "### Shared",                # 11 (duplicate title)
        "second shared body",        # 12
        "#### Last child",            # 13
        "last body",                 # 14
        "## Beta",                   # 15
        "beta body",                 # 16
        "### Final",                 # 17
        "final body",                # 18 (EOF)
    ])
    m = cl.generate_doc_nav_map(text, title="ARCHITECTURE.md", rel_path="docs/ARCHITECTURE.md")
    assert m == "\n".join([
        "## ARCHITECTURE.md (navigation map)",
        "",
        "Full text is NOT inlined to keep the working context window fit. Read any "
        "section on demand with `read_file(root=\"system_repo\", "
        "path=\"docs/ARCHITECTURE.md\", start_line=A, max_lines=N)` (untruncated). "
        "Ranges are inclusive; a parent includes its complete descendant group, "
        "and `max_lines=B-A+1` for `lines A-B`. Sections:",
        "",
        "- Alpha — lines 3-14",
        "  - Shared — lines 5-10",
        "    - Child one — lines 7-8",
        "    - Child two — lines 9-10",
        "  - Shared — lines 11-14",
        "    - Last child — lines 13-14",
        "- Beta — lines 15-18",
        "  - Final — lines 17-18",
    ])
    # Structure only — the section bodies are NOT inlined.
    assert "BODYSENT" not in m
    assert "final body" not in m


def test_nav_map_is_fence_aware_at_every_supported_depth():
    """Supported heading forms inside a backtick fence stay out of the map."""
    text = (
        "## Real\n\n```markdown\n## fake-h2\n### fake-h3\n#### fake-h4\n"
        "```\n\n### Real child\n\n#### Real grandchild\n"
    )
    m = cl.generate_doc_nav_map(text, title="X", rel_path="x.md")
    assert "- Real — lines 1-11" in m
    assert "  - Real child — lines 9-11" in m
    assert "    - Real grandchild — lines 11-11" in m
    assert "fake-h2" not in m
    assert "fake-h3" not in m
    assert "fake-h4" not in m


def test_real_architecture_map_exposes_all_h4_groups():
    architecture = (
        Path(__file__).resolve().parents[1] / "docs" / "ARCHITECTURE.md"
    ).read_text(encoding="utf-8")
    m = cl.generate_doc_nav_map(
        architecture,
        title="ARCHITECTURE.md",
        rel_path="docs/ARCHITECTURE.md",
    )
    tool_children = (
        "Web access mechanisms (three distinct paths — do not conflate)",
        "Context fitting, retry, and compaction",
        "Vision and local image evidence",
        "Background consciousness and Evolution",
    )
    planning_children = (
        "Plan construction and review",
        "Deep self-review",
        "Post-task reflection",
        "Durable memory and project focus",
    )
    for title in (*tool_children, *planning_children):
        assert f"    - {title} — lines " in m

    def _range(indent: str, title: str) -> tuple[int, int]:
        prefix = f"{indent}- {title} — lines "
        row = next(line for line in m.splitlines() if line.startswith(prefix))
        start, end = row.removeprefix(prefix).split("-", 1)
        return int(start), int(end)

    for parent_title, children in (
        ("Tool capability and execution", tool_children),
        ("Planning, deep review, reflection, memory", planning_children),
    ):
        parent_start, parent_end = _range("  ", parent_title)
        child_ranges = [_range("    ", title) for title in children]
        assert all(parent_start < start <= end <= parent_end for start, end in child_ranges)
        assert parent_end == child_ranges[-1][1]


def test_nav_map_no_heading_fallback_names_all_supported_depths():
    m = cl.generate_doc_nav_map("# Title\nbody", title="X", rel_path="x.md")
    assert "(no `##`/`###`/`####` headings; read `x.md` directly)" in m


def test_reference_doc_sections_decouple_arch_mode_from_dev_inclusion():
    """D-ARCH (owner, 2026-08-08): context_mode decides ONLY the ARCHITECTURE
    form (full in max, nav map in low); DEVELOPMENT inclusion is the caller's
    mode-independent decision. Whatever is not inlined is named in the visible
    on-demand pointer (P1)."""
    arch = "## Arch A\n\nARCHBODY\n"
    dev = "## Dev A\n\nDEVBODY\n"

    def _render(mode, include_dev):
        parts = cl.reference_doc_sections(
            None,
            context_mode=mode,
            include_development=include_dev,
            architecture_text=arch,
            development_text=dev,
        )
        return "\n\n".join(parts)

    max_no_dev = _render("max", False)
    assert "ARCHBODY" in max_no_dev  # ARCH full in max even without dev context
    assert "DEVBODY" not in max_no_dev
    assert "docs/DEVELOPMENT.md" in max_no_dev  # pointer, never silent

    max_dev = _render("max", True)
    assert "ARCHBODY" in max_dev and "DEVBODY" in max_dev

    low_dev = _render("low", True)
    assert "ARCHBODY" not in low_dev  # nav map in low
    assert "navigation map" in low_dev
    assert "DEVBODY" in low_dev  # DEV inclusion independent of the mode

    low_no_dev = _render("low", False)
    assert "DEVBODY" not in low_no_dev
    assert "docs/DEVELOPMENT.md" in low_no_dev


def _pointer_listing(text: str) -> str:
    marker = "## Reference docs available on demand"
    idx = text.find(marker)
    return text[idx:] if idx >= 0 else ""


def test_v6115_nav_class_in_max_gets_nav_map_and_pointer():
    """v6.115.0: in owner-max the nav class (architecture_full=False) renders
    the lossless navigation map AND names docs/ARCHITECTURE.md in the visible
    on-demand pointer; the full class keeps the body with NO pointer entry;
    low keeps its established form (nav map; the map's own read_file
    instruction remains the disclosure — no new pointer entry)."""
    arch = "## Arch A\n\nARCHBODY\n"
    dev = "## Dev A\n\nDEVBODY\n"

    def _render(mode, full):
        return "\n\n".join(cl.reference_doc_sections(
            None,
            context_mode=mode,
            include_development=True,
            architecture_full=full,
            architecture_text=arch,
            development_text=dev,
        ))

    max_nav = _render("max", False)
    assert "ARCHBODY" not in max_nav
    assert "navigation map" in max_nav
    assert "docs/ARCHITECTURE.md" in _pointer_listing(max_nav)

    max_full = _render("max", True)
    assert "ARCHBODY" in max_full
    assert "docs/ARCHITECTURE.md" not in max_full  # no pointer entry when full

    low_nav = _render("low", False)
    assert "ARCHBODY" not in low_nav
    assert "navigation map" in low_nav
    assert "docs/ARCHITECTURE.md" not in _pointer_listing(low_nav)  # no new entry


def test_v6115_architecture_context_section_is_class_scoped():
    arch = "# T\n\n## A\n\nBODY\n"
    full = cl.architecture_context_section(
        None, context_mode="max", architecture_full=True, text=arch,
    )
    assert "BODY" in full
    nav = cl.architecture_context_section(
        None, context_mode="max", architecture_full=False, text=arch,
    )
    assert "BODY" not in nav
    assert "navigation map" in nav
    low = cl.architecture_context_section(
        None, context_mode="low", architecture_full=True, text=arch,
    )
    assert "BODY" not in low
    assert "navigation map" in low
    # Default keeps non-task callers (consciousness governance) at full-in-max.
    default = cl.architecture_context_section(None, context_mode="max", text=arch)
    assert "BODY" in default


def test_v6116_development_nav_class_in_max_gets_nav_map_and_pointer():
    """v6.116.0 (owner decision, the ARCHITECTURE mirror): in owner-max
    ``development_full=False`` renders the lossless navigation map AND names
    docs/DEVELOPMENT.md in the visible on-demand pointer; the full class keeps
    the body with NO pointer entry; low ignores the flag (full stays the low
    form); the pointer-only posture (include_development=False) is unaffected
    by the flag either way."""
    arch = "## Arch A\n\nARCHBODY\n"
    dev = "# Dev\n\n## Dev A\n\nDEVBODY\n"

    def _render(mode, dev_full, include_dev=True):
        return "\n\n".join(cl.reference_doc_sections(
            None,
            context_mode=mode,
            include_development=include_dev,
            architecture_text=arch,
            development_text=dev,
            development_full=dev_full,
        ))

    max_nav = _render("max", False)
    assert "DEVBODY" not in max_nav
    assert "## DEVELOPMENT.md (navigation map)" in max_nav
    assert "docs/DEVELOPMENT.md" in _pointer_listing(max_nav)

    max_full = _render("max", True)
    assert "DEVBODY" in max_full
    assert "docs/DEVELOPMENT.md" not in max_full  # no pointer entry when full

    low_full_flag = _render("low", False)
    assert "DEVBODY" in low_full_flag  # low ignores the flag

    external = _render("max", False, include_dev=False)
    assert "## DEVELOPMENT.md (navigation map)" not in external
    assert "docs/DEVELOPMENT.md" in _pointer_listing(external)

    external_full_flag = _render("max", True, include_dev=False)
    assert _pointer_listing(external_full_flag) == _pointer_listing(external)
