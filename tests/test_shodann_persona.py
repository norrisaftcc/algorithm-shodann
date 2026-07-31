"""The SHODANN persona base, and what must survive this copy diverging.

`.claude/agents/shodann.md` and `.claude/skills/shodann-voice/SKILL.md` arrived as a
shared base, byte-identical to the copies in `norrisaftcc/the_intern`. Both repositories
are expected to adjust their own copy, so pinning the whole text would fight the design
and fail on the first intended edit.

What is pinned here is the persona rather than the prose: the rule that readings are
about movement and not absolute position, the fact that the clearance ladder changes
posture twice, the 400-word cap, the absence of a Write tool, and the never-says list.
Those come from `src/shodann/clearance.py` and
`design_docs/SHODANN_VOICE_GUIDE.md` in this repository. A change that breaks one of
them is a change to what SHODANN is, not a local adjustment.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENT_PATH = REPO_ROOT / ".claude/agents/shodann.md"
SKILL_PATH = REPO_ROOT / ".claude/skills/shodann-voice/SKILL.md"
README_PATH = REPO_ROOT / ".claude/agents/README.md"


def test_shodann_agent_holds_the_persona() -> None:
    text = AGENT_PATH.read_text(encoding="utf-8")
    lower = text.lower()

    # The load-bearing idea, from the RED band instruction in clearance.py.
    assert "movement" in lower
    assert "absolute position" in lower

    # Structural, not instructional: no Write tool means the path limit cannot
    # be talked out of. If Write is ever added, the Contract's Path line is a
    # promise rather than a fact.
    tools = next(line for line in text.splitlines() if line.startswith("tools:"))
    assert "Write" not in tools, "Write would make the 'nothing is written' limit instructional"
    assert "Edit" not in tools

    # The four floor items of a contract.
    for noun in ("Audience:", "Scope:", "Format:", "Path:"):
        assert noun in text, f"Contract does not state {noun}"

    assert "400 words" in lower

    # Never-says. These are the persona, not a beginner accommodation - they
    # still hold at BLUE+ where the encouragement scaffolding drops.
    assert "as an ai" in lower, "the character-break rule must be stated to be checkable"
    for absolute in ("wrong", "bad code", "you failed"):
        assert absolute in lower, f"the never-say list is missing {absolute!r}"


def test_clearance_ladder_changes_posture_twice() -> None:
    """Most ladders change once. This one teaches, then mentors, then reports."""
    for path in (AGENT_PATH, SKILL_PATH):
        lower = path.read_text(encoding="utf-8").lower()
        for band in ("infrared", "yellow", "green", "blue"):
            assert band in lower, f"{path.name} does not name the {band.upper()} band"
        for posture in ("teach", "mentor", "report"):
            assert posture in lower, f"{path.name} does not name the {posture} posture"


def test_voice_skill_carries_the_register() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    lower = text.lower()

    assert "rage state" in lower
    # The vocabulary shift that makes RAGE STATE helpful rather than hostile.
    assert "the algorithm has noticed" in lower
    assert "concerningly helpful" in lower
    assert "400 words" in lower

    for noun in ("Audience:", "Scope:", "Format:", "Path:"):
        assert noun in text, f"Contract does not state {noun}"


def test_both_files_declare_they_are_a_shared_base() -> None:
    """The divergence is deliberate and has to say so.

    Without this line a later reader finds two byte-identical files in two
    repositories and reasonably assumes one is generated from the other.
    """
    for path in (AGENT_PATH, SKILL_PATH):
        text = path.read_text(encoding="utf-8")
        assert "shared base" in text.lower()
        assert "the_intern" in text, f"{path.name} does not name the other copy"

        # The stamp is what a divergence is measured from. Without it, a later
        # reader diffs two files and has to guess which edits were deliberate.
        assert re.search(r"[Bb]ase version\s*\**\s*\d{4}-\d{2}-\d{2}\.\d+", text), (
            f"{path.name} claims to be a shared base but states no base version"
        )


def test_readme_lists_shodann_as_maintained() -> None:
    text = README_PATH.read_text(encoding="utf-8")
    maintained = text.split("## SHODANN-tuned (maintained)", 1)[1].split("## Inherited", 1)[0]
    inherited = text.split("## Inherited", 1)[1]

    assert "`shodann`" in maintained
    assert "`shodann-voice`" in maintained
    assert "`shodann`" not in inherited
