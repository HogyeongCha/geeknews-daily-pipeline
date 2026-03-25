# Feature: geeknews-daily-pipeline, Property 8: Config loads supported env vars
# Feature: geeknews-daily-pipeline, Property 9: Missing required vars raises ValueError with var names
# Feature: geeknews-daily-pipeline, Property 10: System env vars override .env file

import os
import pytest
from hypothesis import given, settings, assume
import hypothesis.strategies as st
from hypothesis import HealthCheck

from src.config import load_config, Config


# Filter out null bytes which are invalid in env vars
valid_env_value = st.text(min_size=1).filter(lambda s: "\x00" not in s)


@given(
    slack=valid_env_value,
    vault=valid_env_value,
    geeknews=st.one_of(st.none(), valid_env_value),
)
@settings(max_examples=100)
def test_property_8_env_vars_loaded(slack, vault, geeknews):
    """Property 8: load_config returns Config with matching fields for valid env vars."""
    os.environ["SLACK_WEBHOOK_URL"] = slack
    os.environ["OBSIDIAN_VAULT_PATH"] = vault
    if geeknews:
        os.environ["GEEKNEWS_URL"] = geeknews
    elif "GEEKNEWS_URL" in os.environ:
        del os.environ["GEEKNEWS_URL"]

    try:
        config = load_config()
        assert config.slack_webhook_url == slack
        assert config.obsidian_vault_path == vault
        expected_geeknews = geeknews if geeknews else "https://news.hada.io/new"
        assert config.geeknews_url == expected_geeknews
    finally:
        del os.environ["SLACK_WEBHOOK_URL"]
        del os.environ["OBSIDIAN_VAULT_PATH"]
        if "GEEKNEWS_URL" in os.environ:
            del os.environ["GEEKNEWS_URL"]


@given(missing_vars=st.lists(st.sampled_from(["SLACK_WEBHOOK_URL", "OBSIDIAN_VAULT_PATH"]), min_size=1, max_size=2, unique=True))
@settings(max_examples=100)
def test_property_9_missing_vars_error(missing_vars):
    """Property 9: Missing required vars raises ValueError containing missing var names."""
    # Clear env
    env_to_clear = ["SLACK_WEBHOOK_URL", "OBSIDIAN_VAULT_PATH", "GEEKNEWS_URL"]
    for key in env_to_clear:
        os.environ.pop(key, None)

    # Set only the vars in missing_vars, leave others unset
    for var in missing_vars:
        os.environ[var] = "dummy_value"

    # Determine which vars should be missing
    should_be_missing = [v for v in ["SLACK_WEBHOOK_URL", "OBSIDIAN_VAULT_PATH"] if v not in missing_vars]

    try:
        if should_be_missing:
            with pytest.raises(ValueError) as exc_info:
                load_config()
            error_msg = str(exc_info.value)
            for m in should_be_missing:
                assert m in error_msg
        else:
            # Both present - should not raise
            config = load_config()
            assert config.slack_webhook_url == "dummy_value"
    finally:
        for key in env_to_clear:
            os.environ.pop(key, None)


def test_property_10_system_env_overrides_dotenv(monkeypatch, tmp_path):
    """Property 10: System env vars override .env file values."""
    # Create .env file with one set of values
    dotenv_file = tmp_path / ".env"
    dotenv_file.write_text("SLACK_WEBHOOK_URL=from_dotenv\nOBSIDIAN_VAULT_PATH=from_dotenv\n")

    # Set system env vars (should override)
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "from_system")
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", "from_system")

    # Mock load_dotenv to load from our temp file
    import sys
    from dotenv import load_dotenv
    monkeypatch.setattr("src.config.load_dotenv", lambda override=False: load_dotenv(dotenv_file, override=override))

    config = load_config()
    assert config.slack_webhook_url == "from_system"
    assert config.obsidian_vault_path == "from_system"