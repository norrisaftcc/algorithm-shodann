"""The prompt and the validator must not be able to disagree.

Before this, the template instructed "Recommended Iteration" while the
validator demanded "Observations" at BLUE+, so every review at that band was
rejected, retried, rejected, and dropped to the facts-only fallback. The
format rules the prompt states are now derived from the spec the validator
enforces, and these tests assert that for every band and every mode.
"""

from __future__ import annotations

import re

import pytest

from shodann.clearance import clearance_instructions
from shodann.prompts import build_context, render_prompt
from shodann.state import CitizenRecord
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
