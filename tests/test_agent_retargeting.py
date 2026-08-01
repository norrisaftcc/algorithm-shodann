from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENT_PATH = REPO_ROOT / ".claude/agents/linx-voice-readability-editor.md"
README_PATH = REPO_ROOT / ".claude/agents/README.md"


def test_linx_agent_is_retargeted_to_shodann() -> None:
    agent_text = AGENT_PATH.read_text(encoding="utf-8").lower()

    for banned in (
        "prism",
        "lpaa",
        "g++ -std=c++17",
        "module numbering",
        "gamefaqs",
        "dungeon",
    ):
        assert banned not in agent_text, f"Agent still contains CSC-134 vocabulary: {banned}"

    for required in (
        "shodann",
        "shodann_voice_guide.md",
        "validator.py",
        "400 words",
        "clearance-appropriate",
    ):
        assert required in agent_text, f"Agent is missing SHODANN-specific guidance: {required}"

    tools_line = next((line for line in agent_text.splitlines() if line.startswith("tools:")), "")
    assert tools_line, "Agent is missing a tools: frontmatter line"
    tools = {tool.strip() for tool in tools_line.split(":", 1)[1].split(",") if tool.strip()}
    assert tools == {"read", "grep", "glob", "bash"}

    assert "src/shodann/validator.py" in agent_text
    assert "400-word cap" in agent_text

    readme_text = README_PATH.read_text(encoding="utf-8")
    maintained_section = readme_text.split("## SHODANN-tuned (maintained)", 1)[1].split(
        "## Inherited", 1
    )[0]
    inherited_section = readme_text.split("## Inherited", 1)[1]

    assert "linx-voice-readability-editor" in maintained_section
    assert "linx-voice-readability-editor" not in inherited_section
    assert "kevin-repo-warden" in readme_text
