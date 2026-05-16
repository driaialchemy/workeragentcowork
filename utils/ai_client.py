"""
Shared OpenAI client helpers.

The worker modules use this wrapper so transient API/network failures produce
controlled, user-readable behavior instead of tracebacks.
"""

import os

from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    OpenAI,
    OpenAIError,
    PermissionDeniedError,
    RateLimitError,
)

from utils.retry import call_with_retry


DEFAULT_MODEL = "gpt-4o-mini"

_client = None


class AIServiceError(RuntimeError):
    """Raised when an OpenAI request fails after retry handling."""

    def __init__(self, message, *, recoverable=False):
        super().__init__(message)
        self.recoverable = recoverable


def get_model():
    """Return the configured OpenAI model."""
    return os.environ.get("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def get_client():
    """Create the OpenAI client lazily after environment variables are loaded."""
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def chat_completion(messages, *, max_tokens, temperature):
    """
    Run a chat completion with retries and normalize failures.

    Recoverable errors can be handled with local fallbacks by callers. Config
    errors should stop the run with a clear message.
    """
    try:
        return call_with_retry(
            get_client().chat.completions.create,
            model=get_model(),
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    except (APIConnectionError, APITimeoutError, RateLimitError, InternalServerError) as exc:
        raise AIServiceError(
            f"OpenAI request failed after retries: {exc.__class__.__name__}.",
            recoverable=True,
        ) from exc
    except AuthenticationError as exc:
        raise AIServiceError(
            "OpenAI authentication failed. Check OPENAI_API_KEY in your .env file.",
            recoverable=False,
        ) from exc
    except PermissionDeniedError as exc:
        raise AIServiceError(
            "OpenAI rejected the request for this account or model. Check API access and OPENAI_MODEL.",
            recoverable=False,
        ) from exc
    except BadRequestError as exc:
        raise AIServiceError(
            f"OpenAI rejected the request: {exc.__class__.__name__}.",
            recoverable=False,
        ) from exc
    except OpenAIError as exc:
        raise AIServiceError(
            f"OpenAI request failed: {exc.__class__.__name__}.",
            recoverable=False,
        ) from exc
