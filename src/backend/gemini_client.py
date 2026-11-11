"""D5: Gemini wrapper with retries, timeout, fallback model and friendly errors.

One client is created lazily and kept for the whole app (a client that is garbage
collected closes its connection, which caused 'client has been closed' errors).

generate() returns text or raises GeminiError. GeminiError.user_message is safe to show
in the UI; the technical detail stays in .detail for logs.
"""
import json
import random
import re
import time

from src.backend import config

_client = None


class GeminiError(Exception):
    def __init__(self, kind, user_message, detail=""):
        super().__init__(f"{kind}: {detail or user_message}")
        self.kind = kind  # rate_limit | timeout | server | auth | bad_request | empty | network
        self.user_message = user_message
        self.detail = detail


_MESSAGES = {
    "rate_limit": "The AI service is busy right now. Please try again in a minute.",
    "timeout": "The AI service took too long to respond. Please try again.",
    "server": "The AI service is having problems. Please try again shortly.",
    "network": "Could not reach the AI service. Check your internet connection.",
    "auth": "The AI service rejected our credentials. Please contact the project team.",
    "bad_request": "The AI service could not process this request.",
    "empty": "The AI returned no answer. Please rephrase your question and try again.",
}
_RETRIABLE = {"rate_limit", "timeout", "server", "network", "empty"}


def classify(exc):
    """Map any exception from the SDK / network to one of our error kinds."""
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    text = f"{type(exc).__name__} {exc}".lower()
    if isinstance(code, int):
        if code == 429:
            return "rate_limit"
        if code in (401, 403):
            return "auth"
        if code == 408 or code == 504:
            return "timeout"
        if code >= 500:
            return "server"
        if 400 <= code < 500:
            return "bad_request"
    if "timeout" in text or "timed out" in text or "deadline" in text:
        return "timeout"
    if "connect" in text or "network" in text or "name resolution" in text:
        return "network"
    return "server"


def get_client():
    global _client
    if _client is None:
        from google import genai
        from google.genai import types
        _client = genai.Client(
            api_key=config.get_gemini_key(),
            http_options=types.HttpOptions(timeout=config.GEMINI_TIMEOUT_S * 1000),
        )
    return _client


def _build_config(system, json_mode, temperature):
    from google.genai import types
    kwargs = {"temperature": temperature}
    if system:
        kwargs["system_instruction"] = system
    if json_mode:
        kwargs["response_mime_type"] = "application/json"
    return types.GenerateContentConfig(**kwargs)


def _call(client, model, prompt, system, json_mode, temperature):
    resp = client.models.generate_content(
        model=model, contents=prompt, config=_build_config(system, json_mode, temperature))
    text = (getattr(resp, "text", None) or "").strip()
    if not text:
        raise GeminiError("empty", _MESSAGES["empty"], "empty or blocked response")
    return text


def generate(prompt, system=None, json_mode=False, temperature=0.2, client=None,
             max_retries=None, sleep=time.sleep):
    """Call Gemini. Retries transient errors with backoff, then tries the fallback model."""
    client = client or get_client()
    retries = config.GEMINI_MAX_RETRIES if max_retries is None else max_retries
    models = [config.GEMINI_MODEL]
    if config.GEMINI_FALLBACK_MODEL and config.GEMINI_FALLBACK_MODEL != config.GEMINI_MODEL:
        models.append(config.GEMINI_FALLBACK_MODEL)

    last = None
    for model in models:
        for attempt in range(retries + 1):
            try:
                return _call(client, model, prompt, system, json_mode, temperature)
            except GeminiError as e:
                last = e
            except Exception as e:  # SDK / network errors
                kind = classify(e)
                last = GeminiError(kind, _MESSAGES[kind], f"{model}: {e}")
            if last.kind not in _RETRIABLE:
                raise last  # auth / bad request: retrying will not help
            if attempt < retries:
                sleep(min(2 ** attempt, 8) + random.random() * 0.5)
        # retries exhausted on this model -> loop moves on to the fallback model
    raise last


def parse_json(text):
    """Parse model JSON, tolerating ```json fences. Raises ValueError if invalid."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    return json.loads(cleaned)


def generate_json(prompt, system=None, validate=None, attempts=3, **kw):
    """generate() in JSON mode, re-asking when the output is not valid JSON (or fails validate)."""
    last = None
    for _ in range(attempts):
        text = generate(prompt, system=system, json_mode=True, **kw)
        try:
            data = parse_json(text)
            if validate:
                validate(data)
            return data
        except ValueError as e:
            last = e
    raise GeminiError("empty", _MESSAGES["empty"], f"invalid JSON after {attempts} attempts: {last}")
