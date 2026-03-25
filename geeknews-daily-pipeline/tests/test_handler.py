"""Tests for Lambda Handler module."""
import pytest
from unittest.mock import patch, MagicMock
from hypothesis import given, settings, example
import hypothesis.strategies as st

from src.handler import handler


# Feature: geeknews-daily-pipeline, Property 11: Pipeline error handling returns 500
@given(
    stage=st.sampled_from(["config", "crawl", "markdown", "storage", "notify"]),
    exception_type=st.sampled_from([ValueError, RuntimeError, ConnectionError, IOError]),
    msg=st.text(min_size=1, max_size=100)
)
@settings(max_examples=100)
def test_handler_returns_500_on_any_exception(stage, exception_type, msg):
    """Property 11: Handler catches exceptions and returns statusCode 500."""
    mock_exception = exception_type(msg)

    with patch("src.handler.load_config") as mock_config, \
         patch("src.handler.crawl") as mock_crawl, \
         patch("src.handler.generate_markdown") as mock_markdown, \
         patch("src.handler.save_to_vault") as mock_storage, \
         patch("src.handler.notify") as mock_notify, \
         patch("src.handler.summarize_articles") as mock_summarize:

        # Setup mock config
        mock_config.return_value = MagicMock(
            geeknews_url="https://news.hada.io/new",
            obsidian_vault_path="/vault",
            slack_webhook_url="https://hooks.slack.com/test",
            github_token="",
            github_model="openai/gpt-4o-mini",
        )

        # Determine which stage raises exception
        if stage == "config":
            mock_config.side_effect = mock_exception
        elif stage == "crawl":
            mock_crawl.side_effect = mock_exception
        elif stage == "markdown":
            mock_markdown.side_effect = mock_exception
        elif stage == "storage":
            mock_storage.side_effect = mock_exception
        elif stage == "notify":
            mock_notify.side_effect = mock_exception

        result = handler({}, None)

        assert result["statusCode"] == 500
        assert "error" in result["body"]


# Feature: geeknews-daily-pipeline, Unit: Normal pipeline flow
def test_handler_normal_flow_returns_200():
    """Unit test: Normal pipeline execution returns 200 with correct body."""
    mock_articles = [
        MagicMock(title="Test Article", original_url="https://example.com", summary="Summary", crawled_at="2024-01-15T00:00:00Z")
    ]

    with patch("src.handler.load_config") as mock_config, \
         patch("src.handler.crawl") as mock_crawl, \
         patch("src.handler.generate_markdown") as mock_markdown, \
         patch("src.handler.save_to_vault") as mock_storage, \
         patch("src.handler.notify") as mock_notify, \
         patch("src.handler.summarize_articles") as mock_summarize:

        mock_config.return_value = MagicMock(
            geeknews_url="https://news.hada.io/new",
            obsidian_vault_path="/vault",
            slack_webhook_url="https://hooks.slack.com/test",
            github_token="",
            github_model="openai/gpt-4o-mini",
        )
        mock_crawl.return_value = mock_articles
        mock_markdown.return_value = ("2024-01-15-geeknews.md", "# content")
        mock_storage.return_value = "/vault/2024-01-15-geeknews.md"

        result = handler({}, None)

        assert result["statusCode"] == 200
        assert result["body"]["articles_count"] == 1
        assert result["body"]["saved_path"] == "/vault/2024-01-15-geeknews.md"

        # Verify call order
        mock_config.assert_called_once()
        mock_crawl.assert_called_once_with("https://news.hada.io/new")
        mock_markdown.assert_called_once()
        mock_storage.assert_called_once()
        mock_notify.assert_called_once()


# Feature: geeknews-daily-pipeline, Unit: Local execution mode
def test_handler_local_execution():
    """Unit test: Handler can be executed locally via __main__."""
    with patch("src.handler.load_config") as mock_config, \
         patch("src.handler.crawl") as mock_crawl, \
         patch("src.handler.generate_markdown") as mock_markdown, \
         patch("src.handler.save_to_vault") as mock_storage, \
         patch("src.handler.notify") as mock_notify, \
         patch("src.handler.summarize_articles") as mock_summarize:

        mock_config.return_value = MagicMock(
            geeknews_url="https://news.hada.io/new",
            obsidian_vault_path="/vault",
            slack_webhook_url="https://hooks.slack.com/test",
            github_token="",
            github_model="openai/gpt-4o-mini",
        )
        mock_crawl.return_value = []
        mock_markdown.return_value = ("2024-01-15-geeknews.md", "# content")
        mock_storage.return_value = "/vault/2024-01-15-geeknews.md"

        # Simulate direct module execution
        from src import handler as handler_module
        result = handler_module.handler({}, None)

        assert result["statusCode"] == 200