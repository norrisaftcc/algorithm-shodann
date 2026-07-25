"""The one place SHODANN talks to a model.

Job 4 is the only LLM consumer in the design, and its contract is narrow:
assembled prompt in, under 400 words of markdown out. Everything upstream is
deterministic tooling. That makes the provider a *configuration value* rather
than an abstraction layer - which is the whole reason this file is twenty
lines of HTTP and not a plugin system.

One wire format is supported: OpenAI-compatible ``/chat/completions``. That is
deliberate, and it is what makes local inference a config change rather than a
port. Gemini publishes an OpenAI-compatible endpoint, and Ollama serves one
natively, so swapping a hosted model for a laptop means editing a base URL and
a model name.

Nothing here retries on a bad *response* - that is the validator's job, and it
knows what "bad" means. This retries on a flaky *connection* only.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field

__all__ = ["LLMConfig", "LLMUnavailable", "generate"]

DEFAULT_TIMEOUT = 45
DEFAULT_MAX_TOKENS = 900


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

    timeout: int = DEFAULT_TIMEOUT
    max_tokens: int = DEFAULT_MAX_TOKENS
    temperature: float = 0.4

    @classmethod
    def from_env(cls, environ: dict | None = None) -> LLMConfig:
        env = environ if environ is not None else os.environ
        return cls(
            base_url=env.get("SHODANN_LLM_BASE_URL", "").rstrip("/"),
            model=env.get("SHODANN_LLM_MODEL", ""),
            api_key=env.get("SHODANN_LLM_API_KEY", ""),
            timeout=int(env.get("SHODANN_LLM_TIMEOUT", DEFAULT_TIMEOUT)),
        )

    @property
    def configured(self) -> bool:
        """A local endpoint needs no key; a hosted one does. Both need a URL and a model."""
        return bool(self.base_url and self.model)

    def describe(self) -> str:
        """Safe for logs. Never includes the key."""
        return f"{self.model} at {self.base_url}" if self.configured else "not configured"


def generate(prompt: str, config: LLMConfig, *, opener=urllib.request.urlopen) -> str:
    """Send one prompt, return the model's text.

    ``opener`` is injectable so the whole path is testable without a network
    or a key - which matters, because the degraded path is the one that runs
    when a student most needs feedback.
    """
    if not config.configured:
        raise LLMUnavailable("no model configured")

    payload = json.dumps(
        {
            "model": config.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
        }
    ).encode("utf-8")

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
