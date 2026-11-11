import pytest

from src.backend import config, gemini_client as gc


class FakeAPIError(Exception):
    def __init__(self, code, msg="boom"):
        super().__init__(msg)
        self.code = code


class Resp:
    def __init__(self, text):
        self.text = text


class FakeClient:
    """Plays back a script of outcomes (exception instances or text), one per call."""
    def __init__(self, script):
        self.script, self.calls = list(script), []
        self.models = self

    def generate_content(self, model, contents, config):
        self.calls.append(model)
        out = self.script.pop(0)
        if isinstance(out, Exception):
            raise out
        return Resp(out)


NOSLEEP = lambda s: None


@pytest.fixture(autouse=True)
def no_fallback(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_FALLBACK_MODEL", "")


def test_success_first_try():
    c = FakeClient(["hello"])
    assert gc.generate("hi", client=c, sleep=NOSLEEP) == "hello"
    assert len(c.calls) == 1


def test_rate_limit_is_retried_then_succeeds():
    c = FakeClient([FakeAPIError(429), FakeAPIError(429), "ok"])
    assert gc.generate("hi", client=c, sleep=NOSLEEP) == "ok"
    assert len(c.calls) == 3


def test_server_error_and_timeout_are_retried():
    c = FakeClient([FakeAPIError(503), FakeAPIError(504), "ok"])
    assert gc.generate("hi", client=c, sleep=NOSLEEP) == "ok"


@pytest.mark.parametrize("code,kind", [(400, "bad_request"), (401, "auth"), (403, "auth"), (404, "bad_request")])
def test_client_errors_are_not_retried(code, kind):
    c = FakeClient([FakeAPIError(code), "never reached"])
    with pytest.raises(gc.GeminiError) as e:
        gc.generate("hi", client=c, sleep=NOSLEEP)
    assert e.value.kind == kind and len(c.calls) == 1


def test_retries_exhausted_raises_friendly_error():
    c = FakeClient([FakeAPIError(429)] * 4)
    with pytest.raises(gc.GeminiError) as e:
        gc.generate("hi", client=c, max_retries=3, sleep=NOSLEEP)
    assert e.value.kind == "rate_limit"
    assert "busy" in e.value.user_message and "429" not in e.value.user_message
    assert len(c.calls) == 4


def test_fallback_model_used_after_primary_exhausted(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_FALLBACK_MODEL", "backup-model")
    c = FakeClient([FakeAPIError(503)] * 2 + ["from backup"])
    assert gc.generate("hi", client=c, max_retries=1, sleep=NOSLEEP) == "from backup"
    assert c.calls == [config.GEMINI_MODEL, config.GEMINI_MODEL, "backup-model"]


def test_fallback_not_tried_for_auth_errors(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_FALLBACK_MODEL", "backup-model")
    c = FakeClient([FakeAPIError(401)])
    with pytest.raises(gc.GeminiError):
        gc.generate("hi", client=c, sleep=NOSLEEP)
    assert len(c.calls) == 1


def test_empty_response_is_retried_then_raises():
    c = FakeClient(["", "  ", "", ""])
    with pytest.raises(gc.GeminiError) as e:
        gc.generate("hi", client=c, max_retries=3, sleep=NOSLEEP)
    assert e.value.kind == "empty"


def test_timeout_and_network_text_errors_are_classified():
    assert gc.classify(TimeoutError("request timed out")) == "timeout"
    assert gc.classify(ConnectionError("connect failed")) == "network"
    assert gc.classify(FakeAPIError(504)) == "timeout"


def test_backoff_sleeps_between_retries():
    slept = []
    c = FakeClient([FakeAPIError(429), FakeAPIError(429), "ok"])
    gc.generate("hi", client=c, sleep=slept.append)
    assert len(slept) == 2 and slept[1] > slept[0] - 0.5


def test_parse_json_handles_code_fences():
    assert gc.parse_json('```json\n[{"a": 1}]\n```') == [{"a": 1}]
    with pytest.raises(ValueError):
        gc.parse_json("not json")


GOOD_QUIZ = '[{"question":"Q?","options":["a","b","c","d"],"correct_index":2,"explanation":"because"}]'


def test_generate_json_retries_invalid_json_then_succeeds():
    from src.backend.prompts import validate_quiz
    c = FakeClient(["garbage", GOOD_QUIZ])
    data = gc.generate_json("quiz", client=c, validate=validate_quiz, sleep=NOSLEEP)
    assert data[0]["correct_index"] == 2 and len(c.calls) == 2


def test_generate_json_rejects_malformed_quiz_items():
    from src.backend.prompts import validate_quiz
    bad = '[{"question":"Q?","options":["a","b"],"correct_index":9,"explanation":"x"}]'
    c = FakeClient([bad, bad, bad])
    with pytest.raises(gc.GeminiError):
        gc.generate_json("quiz", client=c, validate=validate_quiz, attempts=3, sleep=NOSLEEP)


def test_giving_up_logs_the_technical_detail(caplog):
    import logging
    c = FakeClient([FakeAPIError(429, "RESOURCE_EXHAUSTED quota exceeded")] * 2)
    with caplog.at_level(logging.WARNING):
        with pytest.raises(gc.GeminiError):
            gc.generate("hi", client=c, max_retries=1, sleep=NOSLEEP)
    assert "RESOURCE_EXHAUSTED" in caplog.text and "rate_limit" in caplog.text


QUOTA_MSG = ("429 RESOURCE_EXHAUSTED: Generate content requests per day limit exceeded on Free Tier. "
             "quotaId GenerateRequestsPerDayPerProjectPerModel-FreeTier")


def test_daily_quota_is_a_different_kind_from_per_minute_limit():
    assert gc.classify(FakeAPIError(429, QUOTA_MSG)) == "quota"
    assert gc.classify(FakeAPIError(429, "Too many requests per minute")) == "rate_limit"


def test_daily_quota_skips_retries_and_goes_straight_to_fallback(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_FALLBACK_MODEL", "backup-lite")
    slept = []
    c = FakeClient([FakeAPIError(429, QUOTA_MSG), "answer from lite"])
    assert gc.generate("hi", client=c, sleep=slept.append) == "answer from lite"
    assert c.calls == [config.GEMINI_MODEL, "backup-lite"] and slept == []  # no wasted retries or waiting


def test_daily_quota_on_every_model_gives_clear_message_without_waiting(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_FALLBACK_MODEL", "backup-lite")
    slept = []
    c = FakeClient([FakeAPIError(429, QUOTA_MSG)] * 2)
    with pytest.raises(gc.GeminiError) as e:
        gc.generate("hi", client=c, sleep=slept.append)
    assert e.value.kind == "quota" and "tomorrow" in e.value.user_message and slept == [] and len(c.calls) == 2


def test_quota_message_counts_as_service_error_in_evaluation():
    from src.backend.evaluation import SERVICE_ERRORS
    assert gc._MESSAGES["quota"] in SERVICE_ERRORS
