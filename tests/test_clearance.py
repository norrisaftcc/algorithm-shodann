"""The prompt and the validator must not be able to disagree.

Before this, the template instructed "Recommended Iteration" while the
validator demanded "Observations" at BLUE+, so every review at that band was
rejected, retried, rejected, and dropped to the facts-only fallback. The
format rules the prompt states are now derived from the spec the validator
enforces, and these tests assert that for every band and every mode.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from shodann.clearance import clearance_disclosure, clearance_instructions
from shodann.prompts import build_context, render_prompt
from shodann.state import CitizenRecord, clearance_name, read_clearance
from shodann.validator import SPECS, STANDARD, for_clearance
from shodann.velocity import CodeMetrics, calculate_velocity

BANDS = [1, 2, 3, 4, 5, 6]
HEADING = re.compile(r"^### .*?([A-Z][A-Za-z +-]+)$", re.MULTILINE)


def rendered_for(level: int, spec=None) -> str:
    record = CitizenRecord(citizen="octocat", clearance_level=level, pr_count=3)
    result = calculate_velocity(CodeMetrics(test_count=8), None, 2)
    return render_prompt(
        build_context(
            result,
            record,
            pr_title="Add inventory tests",
            files_changed=2,
            lines_added=40,
            lines_removed=3,
            spec=spec,
            coverage_instrumented=False,
        )
    )


@pytest.mark.parametrize("level", BANDS)
def test_the_prompt_asks_for_the_heading_the_validator_requires(level: int) -> None:
    spec = for_clearance(STANDARD, level)
    rendered = rendered_for(level, spec)

    mark = "\U0001f50d" if spec.headings[-1] == "Observations" else "\U0001f527"
    assert f"### {mark} {spec.headings[-1]}" in rendered


@pytest.mark.parametrize("level", BANDS)
def test_the_prompt_states_the_word_cap_the_validator_enforces(level: int) -> None:
    spec = for_clearance(STANDARD, level)
    assert f"under {spec.max_words} words" in rendered_for(level, spec)


@pytest.mark.parametrize("level", BANDS)
def test_the_prompt_states_the_opportunity_cap_the_validator_enforces(level: int) -> None:
    spec = for_clearance(STANDARD, level)
    assert f"at MOST {spec.max_opportunities} growth" in rendered_for(level, spec)


@pytest.mark.parametrize("mode", sorted(SPECS))
def test_every_mode_agrees_with_its_own_spec(mode: str) -> None:
    """Not just the clearance bands - the edge-case handlers too."""
    spec = SPECS[mode]
    rendered = rendered_for(2, spec)

    mark = "\U0001f50d" if spec.headings[-1] == "Observations" else "\U0001f527"
    assert f"### {mark} {spec.headings[-1]}" in rendered
    assert f"under {spec.max_words} words" in rendered


# --- the clearance layer is no longer empty -------------------------------


@pytest.mark.parametrize("level", BANDS)
def test_layer_three_carries_guidance_for_every_band(level: int) -> None:
    guidance = clearance_instructions(level)

    assert guidance.strip(), "the clearance slot rendered as an empty string for months"
    assert guidance in rendered_for(level)


def test_the_bands_change_posture_twice() -> None:
    """Teaches, then mentors at GREEN, then reports at BLUE+."""
    assert "one concept at a time" in clearance_instructions(2)
    assert "consequence" in clearance_instructions(5)
    assert "do not teach" in clearance_instructions(6).lower()


def test_beginners_get_a_shorter_timebox_than_seniors() -> None:
    assert "under 15 minutes" in clearance_instructions(1)
    assert "under 30 minutes" in clearance_instructions(2)
    assert "up to an hour" in clearance_instructions(5)


def test_blue_plus_is_not_assigned_homework() -> None:
    rendered = rendered_for(6, for_clearance(STANDARD, 6))

    assert "Observations" in rendered
    assert "Recommended Iteration" not in rendered
    assert "open questions to a peer" in rendered
    assert "under 250 words" in rendered


def test_an_out_of_range_band_still_renders() -> None:
    assert clearance_instructions(99).strip()
    assert clearance_instructions(0).strip()


# --- the register is read, not inferred -----------------------------------


def test_the_band_comes_from_the_file(tmp_path) -> None:
    """The defect this closes: nothing ever read a clearance source.

    `clearance_level` round-tripped the ledger and nothing else wrote it, so
    every citizen was permanently RED and the INFRARED and BLUE+ branches were
    built, tested, and unreachable.
    """
    (tmp_path / ".shodann").mkdir()
    (tmp_path / ".shodann" / "clearances.json").write_text(
        json.dumps({"octocat": "5", "hubot": 6}), encoding="utf-8"
    )

    assert read_clearance("octocat", tmp_path) == 5
    assert read_clearance("hubot", tmp_path) == 6, "integers are accepted too"


def test_unset_is_not_red_it_is_unset(tmp_path) -> None:
    """`None` lets the caller decide. Collapsing it to 2 here hides the gap."""
    assert read_clearance("octocat", tmp_path) is None, "no file at all"

    (tmp_path / ".shodann").mkdir()
    (tmp_path / ".shodann" / "clearances.json").write_text(
        '{"someone-else": "4"}', encoding="utf-8"
    )
    assert read_clearance("octocat", tmp_path) is None, "file exists, citizen unlisted"


@pytest.mark.parametrize(
    "payload", ['{"octocat": "3",}', "not json at all", '["octocat"]', '{"octocat": "BLUE+"}']
)
def test_a_broken_register_never_costs_a_citizen_their_review(payload: str, tmp_path) -> None:
    """A trailing comma in a config file must not raise on the review path."""
    (tmp_path / ".shodann").mkdir()
    (tmp_path / ".shodann" / "clearances.json").write_text(payload, encoding="utf-8")
    assert read_clearance("octocat", tmp_path) is None


def test_out_of_range_bands_saturate(tmp_path) -> None:
    """A band of 9 is a typo, not grounds for refusing to review someone."""
    (tmp_path / ".shodann").mkdir()
    (tmp_path / ".shodann" / "clearances.json").write_text(
        json.dumps({"high": "9", "low": "0", "negative": "-3"}), encoding="utf-8"
    )
    assert read_clearance("high", tmp_path) == 6
    assert read_clearance("low", tmp_path) == 1
    assert read_clearance("negative", tmp_path) == 1


def test_the_shipped_register_parses_and_starts_everyone_at_red() -> None:
    """Landmine 8: no example existed anywhere, though MVP needs one."""
    shipped = Path(__file__).parent.parent / ".shodann" / "clearances.json"
    table = json.loads(shipped.read_text(encoding="utf-8"))
    assert table, "an empty register teaches nothing about the shape"
    assert all(int(level) == 2 for level in table.values()), "everyone starts at RED"


# --- the disclosure waits for ORANGE --------------------------------------


@pytest.mark.parametrize("level", [1, 2])
def test_below_orange_the_register_is_not_advertised(level: int) -> None:
    assert clearance_disclosure(level) == ""


@pytest.mark.parametrize("level", [3, 4, 5, 6])
def test_from_orange_up_the_citizen_is_told_where_their_band_lives(level: int) -> None:
    """Being told is the promotion, not being able to read the file."""
    footer = clearance_disclosure(level)
    assert ".shodann/clearances.json" in footer
    assert clearance_name(level) in footer
    assert "CLEARANCE_REGISTER" in footer, "point at the reasoning, not just the knob"


def test_the_disclosure_keeps_the_voice() -> None:
    """It is appended to a citizen-facing comment, so the vocabulary rules apply."""
    footer = clearance_disclosure(6)
    for forbidden in ("You should", "You need to", "Unfortunately", "wrong", "failed"):
        assert forbidden not in footer


def test_the_footer_stays_inside_its_reservation() -> None:
    """The allowance is subtracted from the model's budget, so it must hold.

    A footer that outgrows this silently puts every ORANGE-and-above comment
    over the cap the output contract states.
    """
    from shodann.clearance import DISCLOSURE_ALLOWANCE

    for level in (3, 4, 5, 6):
        words = len(clearance_disclosure(level).split())
        assert words <= DISCLOSURE_ALLOWANCE, f"band {level} footer is {words} words"
