"""The one place SHODANN talks to a model.

Job 4 is the only LLM consumer in the design, and its contract is narrow:
assembled prompt in, under 400 words of markdown out. Everything upstream is
deterministic tooling. That makes the provider a *configuration value* rather
than an abstraction layer - which is the whole reason this file is twenty
lines of HTTP and not a plugin system.

Two wire formats are supported, and the second one is a port rather than a
config change - which is the whole reason it is spelled out here.

**OpenAI-compatible** ``/chat/completions`` is the default, and it is what
makes local inference a config change: Gemini publishes an OpenAI-compatible
endpoint and Ollama serves one natively, so swapping a hosted model for a
laptop means editing a base URL and a model name.

**Anthropic's Messages API** is the fallback, and it does *not* speak that
format - no ``/chat/completions``, a different request body, a different
response shape, ``x-api-key`` instead of a bearer token, and a ``refusal``
stop reason with no counterpart in the other format. Pretending one client
could serve both would have meant hand-rolling all of that; the official SDK
already has it right, so the fallback costs a dependency and a dispatch rather
than a second pile of HTTP.

The fallback exists for the case the deployment actually has: no local model
available, and a review still owed to a citizen.

Anthropic can also be the *primary*: ``SHODANN_LLM_WIRE=anthropic`` declares
it, the same way the fallback's wire is declared, never sniffed. Request
shaping then follows the newer models' rules rather than the OpenAI wire's: no
``temperature`` unless an operator sets one (Haiku 5.5 answers a non-default
value with a 400, which this module would turn into a silent degraded comment
that names no cause), and ``output_config.effort`` only when one is set.

Nothing here retries on a bad *response* - that is the validator's job, and it
knows what "bad" means. This retries on a flaky *connection* only.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field

__all__ = [
    "DEFAULT_FALLBACK_MODEL",
    "EFFORT_LEVELS",
    "WIRE_ANTHROPIC",
    "WIRE_OPENAI",
    "LLMConfig",
    "LLMUnavailable",
    "fallback_from_env",
    "generate",
]

DEFAULT_TIMEOUT = 45
DEFAULT_MAX_TOKENS = 900
DEFAULT_OPENAI_TEMPERATURE = 0.4

EFFORT_LEVELS = ("low", "medium", "high", "xhigh", "max")
"""The values ``output_config.effort`` accepts. Anything else is a typo."""

WIRE_OPENAI = "openai"
WIRE_ANTHROPIC = "anthropic"

DEFAULT_FALLBACK_MODEL = "claude-haiku-4-5"
"""The tier for a sub-400-word review, not the tier for hard reasoning.

Job 4's whole contract is: assembled prompt in, under 400 words of markdown
out. Everything that decides what the review *says* already happened in
deterministic tooling upstream, so the model is reframing facts rather than
finding them. Paying for a frontier model to do that would be spending on the
one step that cannot invent a metric anyway.
"""


class LLMUnavailable(RuntimeError):
    """No model could be reached. The caller degrades; it does not crash."""


@dataclass(frozen=True)
class LLMConfig:
    base_url: str = ""
    model: str = ""
    api_key: str = field(default="", repr=False)
    """Kept out of the auto-generated repr.

    Nothing logs this object today, but a live secret in a dataclass is one
    `logging.debug(config)` or one f-string typo away from a CI log that
    anyone with read access can see. `describe()` is the safe accessor.
    """

    wire: str = WIRE_OPENAI
    """Which request shape this endpoint speaks.

    Set explicitly, never sniffed from the base URL. Inferring the protocol
    from a hostname means a deployment can change providers by editing a
    string that looks like an address, and the first anyone hears about it is
    a malformed request.
    """

    timeout: int = DEFAULT_TIMEOUT
    max_tokens: int = DEFAULT_MAX_TOKENS
    temperature: float | None = DEFAULT_OPENAI_TEMPERATURE
    """``None`` means "send nothing", which the Anthropic wire honours.

    The default stays 0.4 so a literal ``LLMConfig(...)`` keeps its meaning on
    the OpenAI wire. ``from_env`` sets ``None`` on the Anthropic wire unless an
    operator asks for a value: current Haiku models reject any non-default
    sampling parameter.
    """

    effort: str | None = None
    """``output_config.effort`` for the Anthropic wire; ignored on the OpenAI wire."""

    @classmethod
    def from_env(cls, environ: dict | None = None) -> LLMConfig:
        """Read the primary model from ``SHODANN_LLM_*``.

        Every variable is read as "blank means unset": an unset GitHub Actions
        variable arrives as the empty string, not as an absent key.

        Raises ``ValueError`` naming the variable for a wire, effort or
        temperature that is not one of the allowed values. Silence would be
        worse: a typo in ``SHODANN_LLM_WIRE`` would pick the OpenAI wire and
        send a request the provider cannot parse.
        """
        env = environ if environ is not None else os.environ
        wire = _wire(env.get("SHODANN_LLM_WIRE"), "SHODANN_LLM_WIRE")
        temperature = _optional_float(env.get("SHODANN_LLM_TEMPERATURE"), "SHODANN_LLM_TEMPERATURE")
        if temperature is None and wire == WIRE_OPENAI:
            temperature = DEFAULT_OPENAI_TEMPERATURE
        return cls(
            base_url=_text(env.get("SHODANN_LLM_BASE_URL")).rstrip("/"),
            model=_text(env.get("SHODANN_LLM_MODEL")),
            api_key=env.get("SHODANN_LLM_API_KEY") or "",
            wire=wire,
            timeout=int(env.get("SHODANN_LLM_TIMEOUT") or DEFAULT_TIMEOUT),
            max_tokens=_positive_int(env.get("SHODANN_LLM_MAX_TOKENS"), DEFAULT_MAX_TOKENS),
            temperature=temperature,
            effort=_effort(env.get("SHODANN_LLM_EFFORT"), "SHODANN_LLM_EFFORT"),
        )

    @property
    def configured(self) -> bool:
        """A local endpoint needs no key; a hosted one does. Both need a URL and a model.

        The Anthropic wire is the exception: the SDK knows its own endpoint,
        so there is no base URL to supply and the key is not optional.
        """
        if self.wire == WIRE_ANTHROPIC:
            return bool(self.model and self.api_key)
        return bool(self.base_url and self.model)

    def describe(self) -> str:
        """Safe for logs. Never includes the key."""
        if not self.configured:
            return "not configured"
        return f"{self.model} at {self.base_url or self.wire}"


def fallback_from_env(environ: dict | None = None) -> LLMConfig | None:
    """The Anthropic model to fall back to, or ``None`` if none is configured.

    Keyed on ``ANTHROPIC_API_KEY`` alone: a deployment either has a key or it
    does not, and requiring a second opt-in variable to use a key someone
    already provided is a way to have a fallback that silently never fires.

    ``None`` rather than an unconfigured config, so a caller can tell "no
    fallback was set up" from "a fallback was set up and could not be reached".

    Sampling is left to the model's default unless ``SHODANN_FALLBACK_TEMPERATURE``
    is set. This used to send 0.4 always, which made
    ``SHODANN_FALLBACK_MODEL=claude-haiku-5-5`` fail on every call: the model
    rejects a non-default temperature, and the failure surfaced only as a
    degraded comment.
    """
    env = environ if environ is not None else os.environ
    key = env.get("ANTHROPIC_API_KEY", "")
    if not key:
        return None
    # `or DEFAULT`, never `get(key, DEFAULT)`. An unset GitHub Actions
    # variable arrives as the empty string rather than as an absent key, so
    # the two-argument form hands back "" and the model name disappears -
    # which `configured` then reports as "no fallback set up" on a deployment
    # that provided a key. Same reason the timeout parses defensively.
    return LLMConfig(
        model=(env.get("SHODANN_FALLBACK_MODEL") or "").strip() or DEFAULT_FALLBACK_MODEL,
        api_key=key,
        wire=WIRE_ANTHROPIC,
        timeout=_positive_int(env.get("SHODANN_LLM_TIMEOUT"), DEFAULT_TIMEOUT),
        max_tokens=_positive_int(env.get("SHODANN_FALLBACK_MAX_TOKENS"), DEFAULT_MAX_TOKENS),
        temperature=_optional_float(
            env.get("SHODANN_FALLBACK_TEMPERATURE"), "SHODANN_FALLBACK_TEMPERATURE"
        ),
        effort=_effort(env.get("SHODANN_FALLBACK_EFFORT"), "SHODANN_FALLBACK_EFFORT"),
    )


def _text(raw: str | None) -> str:
    """A stripped string, with absent and blank both meaning empty."""
    return (raw or "").strip()


def _wire(raw: str | None, name: str) -> str:
    value = _text(raw).lower()
    if not value:
        return WIRE_OPENAI
    if value not in (WIRE_OPENAI, WIRE_ANTHROPIC):
        raise ValueError(f"{name} must be '{WIRE_OPENAI}' or '{WIRE_ANTHROPIC}', got {raw!r}")
    return value


def _effort(raw: str | None, name: str) -> str | None:
    value = _text(raw).lower()
    if not value:
        return None
    if value not in EFFORT_LEVELS:
        raise ValueError(f"{name} must be one of {', '.join(EFFORT_LEVELS)}, got {raw!r}")
    return value


def _optional_float(raw: str | None, name: str) -> float | None:
    value = _text(raw)
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        raise ValueError(f"{name} must be a number, got {raw!r}") from None


def _positive_int(raw: str | None, default: int) -> int:
    """Whatever the operator typed, or the default. Never an exception."""
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


def generate(prompt: str, config: LLMConfig, *, opener=urllib.request.urlopen, client=None) -> str:
    """Send one prompt, return the model's text.

    Both transports are injectable so the whole path is testable without a
    network or a key - which matters, because the degraded path is the one
    that runs when a student most needs feedback. ``opener`` serves the
    OpenAI-compatible wire, ``client`` the Anthropic one; each is ignored by
    the other.
    """
    if not config.configured:
        raise LLMUnavailable("no model configured")
    if config.wire == WIRE_ANTHROPIC:
        return _generate_anthropic(prompt, config, client=client)
    return _generate_openai(prompt, config, opener=opener)


def _generate_anthropic(prompt: str, config: LLMConfig, *, client=None) -> str:
    """The Messages API, through the official SDK.

    Imported here rather than at module scope so a broken or absent install
    degrades into a review that still posts, instead of taking the whole
    package down at import time.

    No `thinking` parameter: this model reframes facts that deterministic
    tooling already established. Nothing here needs the model to reason its
    way to an answer.

    `temperature` and `output_config` are sent only when set. Haiku 5.5 returns
    a 400 for any temperature other than the default, so an unconditional
    value turns every call into a degraded comment.
    """
    try:
        import anthropic
    except ImportError as missing:  # pragma: no cover - exercised by removing the dep
        raise LLMUnavailable(f"the anthropic SDK is not installed: {missing}") from missing

    talker = client or anthropic.Anthropic(api_key=config.api_key, timeout=config.timeout)
    request: dict = {
        "model": config.model,
        "max_tokens": config.max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if config.temperature is not None:
        request["temperature"] = config.temperature
    if config.effort:
        request["output_config"] = {"effort": config.effort}
    try:
        message = talker.messages.create(**request)
    except anthropic.AnthropicError as error:
        # Every failure is the same outcome here - the citizen gets the
        # facts-only comment - so this catches the SDK's root rather than
        # enumerating statuses it would only re-join.
        raise LLMUnavailable(f"{config.describe()} unreachable: {error}") from error

    # A refusal is a successful HTTP 200 with no usable content. Read it
    # before the content, or the first index raises on an empty list.
    if getattr(message, "stop_reason", None) == "refusal":
        raise LLMUnavailable(f"{config.describe()} declined the request")

    text = "".join(
        block.text for block in message.content if getattr(block, "type", None) == "text"
    ).strip()
    if not text:
        raise LLMUnavailable(f"{config.describe()} returned no text")
    return text


def _generate_openai(prompt: str, config: LLMConfig, *, opener=urllib.request.urlopen) -> str:
    """OpenAI-compatible `/chat/completions` - Gemini, Ollama, vLLM, and friends."""
    body = {
        "model": config.model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": config.max_tokens,
    }
    if config.temperature is not None:
        body["temperature"] = config.temperature
    payload = json.dumps(body).encode("utf-8")

    headers = {"Content-Type": "application/json"}
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"

    request = urllib.request.Request(  # noqa: S310 - scheme is operator config, not user input
        f"{config.base_url}/chat/completions", data=payload, headers=headers, method="POST"
    )

    try:
        with opener(request, timeout=config.timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise LLMUnavailable(f"{config.describe()} unreachable: {error}") from error
    except json.JSONDecodeError as error:
        raise LLMUnavailable(f"{config.describe()} returned unparseable JSON") from error

    try:
        return body["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, AttributeError) as error:
        raise LLMUnavailable(f"{config.describe()} returned an unexpected shape") from error
