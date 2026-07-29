"""The second wire format, and when the fallback is allowed to fire.

Anthropic's Messages API is not OpenAI-compatible, so this is a port rather
than a config change - and a port has its own failure modes, none of which may
cost a citizen their review.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from shodann.llm import (
    DEFAULT_FALLBACK_MODEL,
    WIRE_ANTHROPIC,
    LLMConfig,
    LLMUnavailable,
    fallback_from_env,
    generate,
)


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

    def __init__(self, message=None, raises=None):
        self._message, self._raises, self.seen = message, raises, []
        self.messages = self

    def create(self, **kwargs):
        self.seen.append(kwargs)
        if self._raises is not None:
            raise self._raises
        return self._message


ANTHROPIC = LLMConfig(model="claude-haiku-4-5", api_key="sk-test", wire=WIRE_ANTHROPIC)


# --- resolving the fallback -----------------------------------------------


def test_no_key_means_no_fallback() -> None:
    """None, not an unconfigured config: 'never set up' differs from 'unreachable'."""
    assert fallback_from_env({}) is None


def test_a_key_is_the_only_opt_in_needed() -> None:
    """A second variable to enable a key someone already provided is how a
    fallback ends up silently never firing."""
    config = fallback_from_env({"ANTHROPIC_API_KEY": "sk-test"})
    assert config is not None
    assert config.model == DEFAULT_FALLBACK_MODEL == "claude-haiku-4-5"
    assert config.wire == WIRE_ANTHROPIC
    assert config.configured


def test_the_fallback_model_is_overridable() -> None:
    config = fallback_from_env(
        {"ANTHROPIC_API_KEY": "sk-test", "SHODANN_FALLBACK_MODEL": "claude-sonnet-5"}
    )
    assert config.model == "claude-sonnet-5"


def test_the_anthropic_wire_needs_no_base_url() -> None:
    """The SDK knows its own endpoint; the key is what is not optional."""
    assert LLMConfig(model="m", api_key="k", wire=WIRE_ANTHROPIC).configured
    assert not LLMConfig(model="m", wire=WIRE_ANTHROPIC).configured, "a key is required"
    # The OpenAI wire is unchanged: a URL and a model, key optional for local.
    assert LLMConfig(base_url="http://x", model="m").configured
    assert not LLMConfig(model="m").configured, "still needs a base URL"


def test_describe_never_leaks_the_key() -> None:
    assert "sk-test" not in ANTHROPIC.describe()
    assert "sk-test" not in repr(ANTHROPIC)


# --- the Messages API path ------------------------------------------------


def test_text_is_joined_from_the_content_blocks() -> None:
    client = FakeClient(Message(content=[Block("## Review"), Block("\n\nbody")]))
    assert generate("prompt", ANTHROPIC, client=client) == "## Review\n\nbody"


def test_non_text_blocks_are_skipped_not_concatenated() -> None:
    client = FakeClient(Message(content=[Block("kept"), Block("dropped", type="thinking")]))
    assert generate("p", ANTHROPIC, client=client) == "kept"


def test_no_thinking_parameter_is_sent() -> None:
    """Haiku 4.5 predates adaptive thinking, and job 4 reframes facts that
    deterministic tooling already established - there is nothing to reason to."""
    client = FakeClient(Message(content=[Block("ok")]))
    generate("p", ANTHROPIC, client=client)
    assert "thinking" not in client.seen[0]
    assert client.seen[0]["model"] == "claude-haiku-4-5"
    assert client.seen[0]["messages"] == [{"role": "user", "content": "p"}]


def test_a_refusal_degrades_rather_than_raising_an_index_error() -> None:
    """A refusal is a successful HTTP 200 with empty content. Reading
    `content[0]` first is how that becomes a crash instead of a comment."""
    client = FakeClient(Message(content=[], stop_reason="refusal"))
    with pytest.raises(LLMUnavailable, match="declined"):
        generate("p", ANTHROPIC, client=client)


def test_an_empty_response_is_unavailable_not_an_empty_review() -> None:
    client = FakeClient(Message(content=[Block("   ")]))
    with pytest.raises(LLMUnavailable, match="no text"):
        generate("p", ANTHROPIC, client=client)


def test_sdk_errors_become_the_degraded_path() -> None:
    import anthropic

    client = FakeClient(raises=anthropic.APIConnectionError(request=None))
    with pytest.raises(LLMUnavailable, match="unreachable"):
        generate("p", ANTHROPIC, client=client)


def test_an_unconfigured_fallback_never_reaches_the_sdk() -> None:
    with pytest.raises(LLMUnavailable, match="no model configured"):
        generate("p", LLMConfig(wire=WIRE_ANTHROPIC), client=FakeClient())


def test_the_wire_is_chosen_explicitly_not_sniffed_from_the_url() -> None:
    """An OpenAI-wire config pointed at Anthropic stays on the OpenAI path.

    Inferring the protocol from a hostname means a deployment changes provider
    by editing something that looks like an address.
    """
    looks_anthropic = LLMConfig(
        base_url="https://api.anthropic.com/v1", model="claude-haiku-4-5", api_key="k"
    )
    sdk = FakeClient(Message(content=[Block("never")]))
    with pytest.raises(LLMUnavailable):
        # Falls to the urllib path and fails to connect, rather than silently
        # using the SDK client it was handed.
        generate("p", looks_anthropic, client=sdk)
    assert sdk.seen == []


# --- the empty-string trap ------------------------------------------------


@pytest.mark.parametrize("blank", ["", "   "])
def test_an_unset_actions_variable_does_not_erase_the_model(blank: str) -> None:
    """An unset GitHub Actions variable arrives as "", not as an absent key.

    `env.get(key, DEFAULT)` therefore returns the empty string, `configured`
    reports False, and a deployment that supplied a key is told it has no
    fallback. This is the same shape as the defects EARLY_RUNS.md collects:
    green everywhere, wrong in production.
    """
    config = fallback_from_env({"ANTHROPIC_API_KEY": "sk-test", "SHODANN_FALLBACK_MODEL": blank})
    assert config is not None
    assert config.model == DEFAULT_FALLBACK_MODEL
    assert config.configured


@pytest.mark.parametrize("raw", ["", "not a number", "0", "-5", None])
def test_a_nonsense_timeout_falls_back_to_the_default(raw) -> None:
    env = {"ANTHROPIC_API_KEY": "sk-test"}
    if raw is not None:
        env["SHODANN_LLM_TIMEOUT"] = raw
    assert fallback_from_env(env).timeout == 45


def test_a_real_timeout_is_still_honoured() -> None:
    assert fallback_from_env({"ANTHROPIC_API_KEY": "k", "SHODANN_LLM_TIMEOUT": "12"}).timeout == 12
