import pytest

from src.backend import gemini_client


@pytest.fixture(autouse=True)
def _fresh_quota_state():
    gemini_client._quota_until.clear()
    yield
    gemini_client._quota_until.clear()
