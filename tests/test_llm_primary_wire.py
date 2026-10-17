"""Anthropic as the *primary* model, declared by configuration.

The shape that matters is Haiku 5.5's: it answers any non-default
``temperature`` with a 400, and ``LLMUnavailable`` turns a 400 into a quiet
degraded comment that names no cause. So a request that carries a temperature
it should not have is not a loud failure here - it is a review that quietly
stops using the model. Every test below that guards the request body asserts on
what the fake SDK client actually received.
"""

from __future__ import annotations

import io
import json
from dataclasses import dataclass

import pytest

from shodann.llm import (
    DEFAULT_FALLBACK_MODEL,
    EFFORT_LEVELS,
    WIRE_ANTHROPIC,
    WIRE_OPENAI,
    LLMConfig,
    fallback_from_env,
    generate,
)
from shodann.review import review

HAIKU_5_5 = "claude-haiku-5-5"
PRIMARY_ENV = {
    "SHODANN_LLM_WIRE": "anthropic",
    "SHODANN_LLM_MODEL": HAIKU_5_5,
    "SHODANN_LLM_API_KEY": "sk-test",
}


@dataclass
class Block:
    text: str
    type: str = "text"


@dataclass
class Message:
    content: list
    stop_reason: str = "end_turn"


class FakeClient:
    """Stands in for `anthropic.Anthropic`, which is duck-typed at one call."""

    def __init__(self, text: str = "ok"):
        self._text, self.seen = text, []
        self.messages = self

    def create(self, **kwargs):
        self.seen.append(kwargs)
        return Message(content=[Block(self._text)])


# --- the sanity check that the parametrised lists below are not empty -------


def test_the_effort_levels_are_the_five_the_api_defines() -> None:
    """Guards the parametrisations that iterate this tuple against going silent."""
    assert EFFORT_LEVELS == ("low", "medium", "high", "xhigh", "max")


# --- resolving the primary --------------------------------------------------


def test_an_unset_wire_is_the_openai_wire_exactly_as_before() -> None:
    config = LLMConfig.from_env(
        {"SHODANN_LLM_BASE_URL": "http://localhost:11434/v1/", "SHODANN_LLM_MODEL": "llama3.2"}
    )
    assert config.wire == WIRE_OPENAI
    assert config.temperature == 0.4
    assert config.max_tokens == 900
    assert config.effort is None
    assert config.configured


def test_the_openai_request_body_is_unchanged() -> None:
    config = LLMConfig.from_env(
        {
            "SHODANN_LLM_BASE_URL": "http://x/v1",
            "SHODANN_LLM_MODEL": "m",
            "SHODANN_LLM_API_KEY": "k",
        }
    )
    seen: list[dict] = []

    def opener(request, timeout=None):
        seen.append(json.loads(request.data))
        return io.BytesIO(json.dumps({"choices": [{"message": {"content": "ok"}}]}).encode())

    assert generate("p", config, opener=opener) == "ok"
    assert seen == [
        {"model": "m", "messages": [{"role": "user", "content": "p"}], "max_tokens": 900,
         "temperature": 0.4}
    ]


def test_the_anthropic_wire_is_configured_by_model_and_key_alone() -> None:
    config = LLMConfig.from_env(PRIMARY_ENV)
    assert config.wire == WIRE_ANTHROPIC
    assert config.configured
    assert config.model == HAIKU_5_5
    assert config.base_url == ""


def test_the_anthropic_primary_needs_its_key() -> None:
    env = {k: v for k, v in PRIMARY_ENV.items() if k != "SHODANN_LLM_API_KEY"}
    assert not LLMConfig.from_env(env).configured


def test_the_anthropic_primary_leaves_sampling_to_the_model_by_default() -> None:
    assert LLMConfig.from_env(PRIMARY_ENV).temperature is None


def test_an_operator_can_still_ask_for_a_temperature() -> None:
    config = LLMConfig.from_env({**PRIMARY_ENV, "SHODANN_LLM_TEMPERATURE": "1.0"})
    assert config.temperature == 1.0


def test_the_wire_is_case_and_whitespace_tolerant() -> None:
    assert LLMConfig.from_env({**PRIMARY_ENV, "SHODANN_LLM_WIRE": " Anthropic "}).wire == (
        WIRE_ANTHROPIC
    )


@pytest.mark.parametrize("bogus", ["anthropik", "claude", "gemini"])
def test_a_bogus_wire_names_the_variable(bogus: str) -> None:
    with pytest.raises(ValueError, match="SHODANN_LLM_WIRE"):
        LLMConfig.from_env({**PRIMARY_ENV, "SHODANN_LLM_WIRE": bogus})


@pytest.mark.parametrize("bogus", ["extreme", "minimal", "3"])
def test_a_bogus_effort_names_the_variable(bogus: str) -> None:
    with pytest.raises(ValueError, match="SHODANN_LLM_EFFORT"):
        LLMConfig.from_env({**PRIMARY_ENV, "SHODANN_LLM_EFFORT": bogus})


def test_a_bogus_temperature_names_the_variable() -> None:
    with pytest.raises(ValueError, match="SHODANN_LLM_TEMPERATURE"):
        LLMConfig.from_env({**PRIMARY_ENV, "SHODANN_LLM_TEMPERATURE": "warm"})


@pytest.mark.parametrize("level", EFFORT_LEVELS)
def test_every_documented_effort_level_is_accepted(level: str) -> None:
    assert LLMConfig.from_env({**PRIMARY_ENV, "SHODANN_LLM_EFFORT": level}).effort == level


@pytest.mark.parametrize(
    "name",
    [
        "SHODANN_LLM_WIRE",
        "SHODANN_LLM_EFFORT",
        "SHODANN_LLM_MAX_TOKENS",
        "SHODANN_LLM_TEMPERATURE",
        "SHODANN_LLM_BASE_URL",
        "SHODANN_LLM_MODEL",
    ],
)
@pytest.mark.parametrize("blank", ["", "   "])
def test_an_unset_actions_variable_behaves_as_unset(name: str, blank: str) -> None:
    """An unset GitHub Actions variable arrives as "", not as an absent key.

    Same trap as `test_an_unset_actions_variable_does_not_erase_the_model` in
    test_llm_fallback.py, for each variable this module added.
    """
    base = {
        "SHODANN_LLM_BASE_URL": "http://x/v1",
        "SHODANN_LLM_MODEL": "m",
        "SHODANN_LLM_WIRE": "",
    }
    config = LLMConfig.from_env({**base, name: blank})
    reference = LLMConfig.from_env({k: v for k, v in base.items() if k != name})
    if name in ("SHODANN_LLM_BASE_URL", "SHODANN_LLM_MODEL"):
        assert not config.configured
        return
    assert config == reference


@pytest.mark.parametrize("raw", ["", "nope", "0", "-5"])
def test_a_nonsense_max_tokens_falls_back_to_the_wires_default(raw: str) -> None:
    anthropic = LLMConfig.from_env({**PRIMARY_ENV, "SHODANN_LLM_MAX_TOKENS": raw})
    assert anthropic.max_tokens == 2000
    openai = LLMConfig.from_env(
        {"SHODANN_LLM_BASE_URL": "http://x", "SHODANN_LLM_MODEL": "m",
         "SHODANN_LLM_MAX_TOKENS": raw}
    )
    assert openai.max_tokens == 900


def test_the_anthropic_wire_defaults_to_the_template_ceiling_and_openai_does_not() -> None:
    """900 leaves no room beside thinking; the template already asks for 2000."""
    assert LLMConfig.from_env(PRIMARY_ENV).max_tokens == 2000
    openai_env = {"SHODANN_LLM_BASE_URL": "http://x", "SHODANN_LLM_MODEL": "m"}
    assert LLMConfig.from_env(openai_env).max_tokens == 900
    assert fallback_from_env({"ANTHROPIC_API_KEY": "k"}).max_tokens == 2000


@pytest.mark.parametrize("raw", ["45s", "-1", "0", "abc", "1.5"])
def test_a_nonsense_primary_timeout_falls_back_to_the_default_instead_of_raising(raw: str) -> None:
    """`int("45s")` raised a bare ValueError and a negative value was accepted.

    The fallback path already used `_positive_int`; the two read one variable.
    """
    env = {**PRIMARY_ENV, "SHODANN_LLM_TIMEOUT": raw}
    assert LLMConfig.from_env(env).timeout == 45
    assert fallback_from_env({"ANTHROPIC_API_KEY": "k", "SHODANN_LLM_TIMEOUT": raw}).timeout == 45


def test_a_real_primary_timeout_is_honoured() -> None:
    assert LLMConfig.from_env({**PRIMARY_ENV, "SHODANN_LLM_TIMEOUT": "12"}).timeout == 12


def test_max_tokens_is_read_from_the_environment() -> None:
    assert LLMConfig.from_env({**PRIMARY_ENV, "SHODANN_LLM_MAX_TOKENS": "2000"}).max_tokens == 2000


def test_describe_never_prints_the_key() -> None:
    config = LLMConfig.from_env(PRIMARY_ENV)
    assert "sk-test" not in config.describe()
    assert "sk-test" not in repr(config)
    assert HAIKU_5_5 in config.describe()


# --- the request the SDK actually receives (the Haiku 5.5 shape) ------------


def test_the_haiku_5_5_request_carries_no_temperature_and_the_configured_effort() -> None:
    """The guard the whole package exists for.

    A temperature in this request is a 400 from the model, which the caller
    then reports as a degraded comment with no cause attached.
    """
    config = LLMConfig.from_env(
        {**PRIMARY_ENV, "SHODANN_LLM_EFFORT": "low", "SHODANN_LLM_MAX_TOKENS": "2000"}
    )
    client = FakeClient()
    generate("prompt", config, client=client)

    assert len(client.seen) == 1
    sent = client.seen[0]
    assert sent["model"] == HAIKU_5_5
    assert "temperature" not in sent
    assert sent["output_config"] == {"effort": "low"}
    assert sent["max_tokens"] == 2000
    assert sent["messages"] == [{"role": "user", "content": "prompt"}]
    assert "thinking" not in sent


def test_no_effort_means_no_output_config() -> None:
    client = FakeClient()
    generate("p", LLMConfig.from_env(PRIMARY_ENV), client=client)
    assert "output_config" not in client.seen[0]
    assert "temperature" not in client.seen[0]


def test_an_explicit_temperature_is_sent_when_an_operator_sets_one() -> None:
    client = FakeClient()
    config = LLMConfig.from_env({**PRIMARY_ENV, "SHODANN_LLM_TEMPERATURE": "1"})
    generate("p", config, client=client)
    assert client.seen[0]["temperature"] == 1.0


def test_effort_does_not_reach_the_openai_wire() -> None:
    config = LLMConfig.from_env(
        {
            "SHODANN_LLM_BASE_URL": "http://x/v1",
            "SHODANN_LLM_MODEL": "m",
            "SHODANN_LLM_EFFORT": "low",
        }
    )
    seen: list[dict] = []

    def opener(request, timeout=None):
        seen.append(json.loads(request.data))
        return io.BytesIO(json.dumps({"choices": [{"message": {"content": "ok"}}]}).encode())

    generate("p", config, opener=opener)
    assert "output_config" not in seen[0]
    assert "effort" not in json.dumps(seen[0])


# --- the fallback no longer pins a temperature -------------------------------


def test_a_haiku_5_fallback_sends_no_temperature_by_default() -> None:
    """What makes `SHODANN_FALLBACK_MODEL=claude-haiku-5-5` work at all."""
    config = fallback_from_env(
        {"ANTHROPIC_API_KEY": "sk-test", "SHODANN_FALLBACK_MODEL": HAIKU_5_5}
    )
    client = FakeClient()
    generate("p", config, client=client)

    assert client.seen[0]["model"] == HAIKU_5_5
    assert "temperature" not in client.seen[0]
    assert "output_config" not in client.seen[0]
    assert client.seen[0]["max_tokens"] == 2000


@pytest.mark.parametrize("model", [HAIKU_5_5, "claude-haiku-5-5-20260301", "Claude-Haiku-5-6"])
def test_the_whole_haiku_5_family_is_spared_a_temperature(model: str) -> None:
    config = fallback_from_env({"ANTHROPIC_API_KEY": "k", "SHODANN_FALLBACK_MODEL": model})
    assert config.temperature is None


@pytest.mark.parametrize("model", ["", "claude-haiku-4-5", "claude-sonnet-5"])
def test_every_other_fallback_keeps_the_previous_0_4(model: str) -> None:
    """Dropping temperature everywhere changed the default fallback with no benefit."""
    config = fallback_from_env({"ANTHROPIC_API_KEY": "k", "SHODANN_FALLBACK_MODEL": model})
    client = FakeClient()
    generate("p", config, client=client)
    assert client.seen[0]["temperature"] == 0.4


def test_an_explicit_fallback_temperature_beats_the_model_rule() -> None:
    config = fallback_from_env(
        {"ANTHROPIC_API_KEY": "k", "SHODANN_FALLBACK_MODEL": HAIKU_5_5,
         "SHODANN_FALLBACK_TEMPERATURE": "1"}
    )
    assert config.temperature == 1.0


def test_effort_is_not_sent_to_haiku_4_5_even_when_asked_for() -> None:
    """`SHODANN_FALLBACK_EFFORT` set for Haiku 5.5 must not 400 the 4.5 default."""
    config = fallback_from_env({"ANTHROPIC_API_KEY": "k", "SHODANN_FALLBACK_EFFORT": "low"})
    client = FakeClient()
    generate("p", config, client=client)
    assert config.model == "claude-haiku-4-5"
    assert "output_config" not in client.seen[0]


def test_effort_is_sent_to_a_model_that_takes_it() -> None:
    config = fallback_from_env(
        {"ANTHROPIC_API_KEY": "k", "SHODANN_FALLBACK_MODEL": HAIKU_5_5,
         "SHODANN_FALLBACK_EFFORT": "low"}
    )
    client = FakeClient()
    generate("p", config, client=client)
    assert client.seen[0]["output_config"] == {"effort": "low"}


def test_the_default_fallback_model_is_unchanged() -> None:
    assert fallback_from_env({"ANTHROPIC_API_KEY": "k"}).model == DEFAULT_FALLBACK_MODEL
    assert DEFAULT_FALLBACK_MODEL == "claude-haiku-4-5"


def test_the_fallback_temperature_is_read_from_the_environment() -> None:
    config = fallback_from_env({"ANTHROPIC_API_KEY": "k", "SHODANN_FALLBACK_TEMPERATURE": "0.7"})
    client = FakeClient()
    generate("p", config, client=client)
    assert client.seen[0]["temperature"] == 0.7


def test_the_fallback_effort_and_max_tokens_are_read() -> None:
    config = fallback_from_env(
        {
            "ANTHROPIC_API_KEY": "k",
            "SHODANN_FALLBACK_MODEL": HAIKU_5_5,
            "SHODANN_FALLBACK_EFFORT": "medium",
            "SHODANN_FALLBACK_MAX_TOKENS": "1500",
        }
    )
    client = FakeClient()
    generate("p", config, client=client)
    assert client.seen[0]["output_config"] == {"effort": "medium"}
    assert client.seen[0]["max_tokens"] == 1500


@pytest.mark.parametrize("blank", ["", "  "])
def test_blank_fallback_variables_behave_as_unset(blank: str) -> None:
    config = fallback_from_env(
        {
            "ANTHROPIC_API_KEY": "k",
            "SHODANN_FALLBACK_TEMPERATURE": blank,
            "SHODANN_FALLBACK_EFFORT": blank,
            "SHODANN_FALLBACK_MAX_TOKENS": blank,
        }
    )
    assert config.temperature == 0.4, "blank is unset, and unset on Haiku 4.5 is the old 0.4"
    assert config.effort is None
    assert config.max_tokens == 2000


def test_a_bogus_fallback_effort_or_temperature_names_the_variable() -> None:
    with pytest.raises(ValueError, match="SHODANN_FALLBACK_EFFORT"):
        fallback_from_env({"ANTHROPIC_API_KEY": "k", "SHODANN_FALLBACK_EFFORT": "ultra"})
    with pytest.raises(ValueError, match="SHODANN_FALLBACK_TEMPERATURE"):
        fallback_from_env({"ANTHROPIC_API_KEY": "k", "SHODANN_FALLBACK_TEMPERATURE": "hot"})


# --- a max_tokens stop is a failure with a cause, not a short review ---------


class TruncatingClient(FakeClient):
    def create(self, **kwargs):
        self.seen.append(kwargs)
        return Message(content=[Block("The Algorithm obs")], stop_reason="max_tokens")


def test_a_max_tokens_stop_is_unavailable_and_names_the_cause() -> None:
    from shodann.llm import LLMUnavailable

    config = LLMConfig.from_env(PRIMARY_ENV)
    with pytest.raises(LLMUnavailable, match="max_tokens"):
        generate("p", config, client=TruncatingClient())


# --- end to end: a primary on the anthropic wire produces a real review ------

EVENT = {
    "pull_request": {
        "number": 42,
        "title": "Add inventory tests",
        "changed_files": 4,
        "additions": 120,
        "deletions": 18,
        "commits": 3,
        "user": {"login": "octocat"},
    }
}

GOOD_RESPONSE = """## \U0001f916 SHODANN Analysis Complete

**Citizen**: @octocat | **Clearance**: RED | **Velocity**: 9.0

### \U0001f680 Shipping Velocity Report

Four files moved and three commits landed. The Algorithm has observed steady progress.

### ✅ Algorithm-Approved Patterns

- Tests arrived with the feature.

### \U0001f4c8 Growth Opportunities

- The Algorithm suggests naming the helper for what it returns.

### \U0001f527 Recommended Iteration

Add one test for the empty branch.

*The Algorithm sees your growth. The Algorithm is pleased.*
"""


def test_review_with_an_anthropic_primary_is_not_degraded(tmp_path) -> None:
    config = LLMConfig.from_env(
        {**PRIMARY_ENV, "SHODANN_LLM_EFFORT": "low", "SHODANN_LLM_MAX_TOKENS": "2000"}
    )
    client = FakeClient(GOOD_RESPONSE)

    body = review(EVENT, root=tmp_path, config=config, client=client, write_state=False)

    assert body == GOOD_RESPONSE.strip()
    assert "MINIMAL RESPONSE" not in body
    assert len(client.seen) == 1, "served on the first attempt, no retry"
    sent = client.seen[0]
    assert sent["model"] == HAIKU_5_5
    assert "temperature" not in sent
    assert sent["output_config"] == {"effort": "low"}


def test_review_reads_an_anthropic_primary_from_the_environment(tmp_path, monkeypatch) -> None:
    """`review()` with no explicit config is the path the workflow takes."""
    for name, value in PRIMARY_ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    client = FakeClient(GOOD_RESPONSE)

    body = review(EVENT, root=tmp_path, client=client, write_state=False)

    assert "MINIMAL RESPONSE" not in body
    assert "temperature" not in client.seen[0]


# --- the SDK floor ----------------------------------------------------------

# Measured against the published wheels: `messages.create` has no `output_config`
# parameter before 0.77, and `OutputConfigParam` carries `effort` from 0.78. An
# older client raises TypeError on `SHODANN_LLM_EFFORT`, which is not an
# `AnthropicError`, so it would escape the graceful-degradation handler.
MINIMUM_SDK_WITH_EFFORT = (0, 78)


def test_the_anthropic_dependency_floor_admits_only_sdks_that_know_effort() -> None:
    import re
    from pathlib import Path

    project = (Path(__file__).parent.parent / "pyproject.toml").read_text(encoding="utf-8")
    requirement = re.search(r'"anthropic>=(\d+)\.(\d+)[^"]*"', project)

    assert requirement, "pyproject.toml no longer declares a lower bound for anthropic"
    floor = (int(requirement.group(1)), int(requirement.group(2)))
    assert floor >= MINIMUM_SDK_WITH_EFFORT, (
        f"anthropic>={floor[0]}.{floor[1]} admits a client with no output_config.effort"
    )


class ModelSensitiveClient(FakeClient):
    """The primary is cut off at `max_tokens`; any other model answers."""

    def create(self, **kwargs):
        self.seen.append(kwargs)
        if kwargs["model"] == HAIKU_5_5:
            return Message(content=[Block("The Algorithm obs")], stop_reason="max_tokens")
        return Message(content=[Block(GOOD_RESPONSE)])


def test_a_truncated_primary_reaches_the_fallback_and_the_review_is_not_degraded(tmp_path) -> None:
    """Without the check a half-sentence is a short review that fails validation,
    is retried at the same ceiling, and degrades without ever asking the fallback."""
    config = LLMConfig.from_env(PRIMARY_ENV)
    fallback = fallback_from_env({"ANTHROPIC_API_KEY": "k"})
    client = ModelSensitiveClient()

    body = review(
        EVENT, root=tmp_path, config=config, fallback=fallback, client=client, write_state=False
    )

    assert body == GOOD_RESPONSE.strip()
    assert [c["model"] for c in client.seen] == [HAIKU_5_5, "claude-haiku-4-5"]
