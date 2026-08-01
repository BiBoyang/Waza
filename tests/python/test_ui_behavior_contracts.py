from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "skills" / "ui"


def read(relative: str) -> str:
    return (UI / relative).read_text(encoding="utf-8")


def test_ui_mode_routes_remain_complete_and_distinct() -> None:
    skill = read("SKILL.md")
    routes = {
        "Bounded fix to an existing screen": "references/mode-quick-fix.md",
        "Screenshot supplied as the evidence": "references/mode-screenshot-iteration.md",
        "Generated image asset": "references/mode-generated-asset.md",
        "New page, component, or visual system": "Lock the Direction First",
    }
    for trigger, destination in routes.items():
        assert trigger in skill
        assert destination in skill


def test_direction_lock_resolves_all_dimensions_without_mandatory_interview() -> None:
    skill = read("SKILL.md")
    for dimension in (
        "Who uses this, and in what context?",
        "What is the aesthetic direction?",
        "What is the design signature?",
        "What are the hard constraints?",
        "What is the signature micro-interaction?",
    ):
        assert dimension in skill
    assert "Infer first" in skill
    assert "at most two sub-questions" in skill
    assert "Do not proceed until all five are answered" not in skill
    assert "list 2-3 mature products" not in skill
    assert "genuinely unfamiliar interaction pattern" in skill
    assert "when exact brand tokens would materially improve" in skill
    assert "Run the preset only with explicit approval" in skill
    assert "Skip it when screenshots, source tokens, or sibling components" in skill


def test_visual_repair_modes_lock_target_preserve_and_evidence() -> None:
    quick = read("references/mode-quick-fix.md")
    screenshot = read("references/mode-screenshot-iteration.md")
    for body in (quick, screenshot):
        assert "`target`" in body
        assert "`preserve`" in body
        assert "`evidence`" in body
        assert "render" in body.lower()
    assert "freeze a minimal visual matrix" in screenshot
    assert "re-check every `preserve` boundary" in screenshot
    assert "smallest" in quick


def test_generated_asset_keeps_six_part_spec_and_two_rejection_stop() -> None:
    generated = read("references/mode-generated-asset.md")
    for field in (
        "what the image says",
        "Language",
        "Aspect and where it will be seen",
        "Palette count",
        "Reference",
        "Must not appear",
    ):
        assert field in generated
    assert "Ask once only when any unresolved spec field" in generated
    assert "Two Rejections Is A Hard Stop" in generated
    assert "name the part that survives" in generated


def test_aesthetic_compatibility_file_maps_every_former_section_once() -> None:
    compatibility = read("references/design-aesthetic-quality.md")
    canonical = read("references/design-reference.md")
    former_sections = {
        "App Shell Rules": "app-shell-rules",
        "Options Guide": "options-guide",
        "DESIGN.md Scaffold": "designmd-scaffold-optional-production-uis",
        "Pre-Handoff Checklist: Strategic Omissions":
            "pre-handoff-checklist-strategic-omissions",
        "Reference Material Priority": "reference-material-priority",
        "Adding to Existing UI": "adding-to-existing-ui",
    }
    assert "one source of truth" in compatibility
    assert len(compatibility.splitlines()) < 30
    for section, anchor in former_sections.items():
        assert f"| {section} |" in compatibility
        assert section in canonical
        assert f"(design-reference.md#{anchor})" in compatibility
    assert "Decorative backgrounds default to off" not in compatibility
    assert "Decorative backgrounds default to off" in canonical


def test_ui_skill_docs_contain_no_em_dash() -> None:
    paths = [UI / "SKILL.md", *sorted((UI / "references").glob("*.md"))]
    offenders = [str(path.relative_to(ROOT)) for path in paths if "\u2014" in path.read_text(encoding="utf-8")]
    assert offenders == []
