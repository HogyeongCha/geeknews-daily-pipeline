"""Tests for Slack Notifier module."""
import json
import pytest
import responses
from hypothesis import given, settings
import hypothesis.strategies as st

from src.crawler import Article
from src.slack_notifier import notify


# Hypothesis strategy for Article
article_strategy = st.builds(
    Article,
    title=st.text(min_size=1, max_size=200),
    original_url=st.from_regex(r"https://[a-z]+\.[a-z]+/[a-z0-9/_-]+", fullmatch=True),
    summary=st.one_of(st.none(), st.text(min_size=1, max_size=500)),
    crawled_at=st.datetimes().map(lambda dt: dt.isoformat() + "Z"),
)


# Property 7: Slack message contains all article titles and original_urls
# Validates: Requirements 4.2
@given(articles=st.lists(article_strategy, min_size=1, max_size=20))
@settings(max_examples=100)
@responses.activate
def test_property_7_slack_message_contains_all_articles(articles):
    """Slack message body contains all article titles and original_urls."""
    webhook_url = "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX"
    responses.add(responses.POST, webhook_url, json={"ok": True}, status=200)

    result = notify(webhook_url, articles)

    assert result is True
    assert len(responses.calls) == 1
    body = json.loads(responses.calls[0].request.body)
    # Collect all text from all blocks
    all_text = ""
    for block in body["blocks"]:
        if "text" in block and isinstance(block["text"], dict):
            all_text += block["text"].get("text", "") + "\n"

    for article in articles:
        assert article.title in all_text
        assert article.original_url in all_text


# Unit test: empty list sends "새로운 기사가 없습니다"
# Validates: Requirements 4.5
@responses.activate
def test_notify_empty_list_sends_no_articles_message():
    """When article list is empty, sends '새로운 기사가 없습니다'."""
    webhook_url = "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX"
    responses.add(responses.POST, webhook_url, json={"ok": True}, status=200)

    result = notify(webhook_url, [])

    assert result is True
    body = json.loads(responses.calls[0].request.body)
    section_text = body["blocks"][1]["text"]["text"]
    assert "새로운 기사가 없습니다" in section_text


# Unit test: webhook failure returns False
# Validates: Requirements 4.4
@responses.activate
def test_notify_webhook_failure_returns_false():
    """When webhook fails, returns False without raising exception."""
    webhook_url = "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX"
    responses.add(responses.POST, webhook_url, json={"ok": False}, status=500)

    article = Article(
        title="Test Article",
        original_url="https://example.com/article",
        summary="Test summary",
        crawled_at="2024-01-15T10:00:00Z",
    )
    result = notify(webhook_url, [article])

    assert result is False
    assert len(responses.calls) == 1