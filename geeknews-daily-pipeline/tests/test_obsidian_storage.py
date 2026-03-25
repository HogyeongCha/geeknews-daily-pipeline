"""Tests for Obsidian Storage module."""
import pytest
from hypothesis import given, settings, HealthCheck
import hypothesis.strategies as st

from src.obsidian_storage import save_to_vault


# Property 5: save_to_vault round-trip
# Validates: Requirements 3.1, 3.4
@given(content=st.text(min_size=1, max_size=1000), filename=st.from_regex(r"[a-zA-Z0-9_-]+\.md", fullmatch=True))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_5_save_roundtrip(tmp_path, content, filename):
    """Saved file content equals original content."""
    result_path = save_to_vault(str(tmp_path), filename, content)
    with open(result_path, "rb") as f:
        saved_content = f.read().decode("utf-8")
    assert saved_content == content


# Property 6: save_to_vault idempotency
# Validates: Requirements 3.2
@given(
    content1=st.text(min_size=1, max_size=500),
    content2=st.text(min_size=1, max_size=500),
    filename=st.from_regex(r"[a-zA-Z0-9_-]+\.md", fullmatch=True),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_6_idempotency(tmp_path, content1, content2, filename):
    """Second save overwrites first, only second content remains."""
    save_to_vault(str(tmp_path), filename, content1)
    result_path = save_to_vault(str(tmp_path), filename, content2)
    with open(result_path, encoding="utf-8") as f:
        saved_content = f.read()
    assert saved_content == content2


# Unit test: FileNotFoundError on missing vault path
# Validates: Requirements 3.3
def test_save_to_vault_missing_vault_path():
    """Raises FileNotFoundError when vault path doesn't exist."""
    with pytest.raises(FileNotFoundError):
        save_to_vault("/nonexistent/path/vault", "test.md", "content")