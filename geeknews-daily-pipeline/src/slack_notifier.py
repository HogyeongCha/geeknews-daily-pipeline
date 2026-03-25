import logging
from datetime import datetime, timezone, timedelta

import requests

from src.crawler import Article

logger = logging.getLogger(__name__)


def _truncate(text: str, max_len: int = 150) -> str:
    """Truncate text to max_len, adding ellipsis if needed."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _build_article_block(idx: int, article: Article) -> list[dict]:
    """Build Slack blocks for a single article."""
    # Title with link
    title_line = f"*{idx}. <{article.original_url}|{article.title}>*"

    # Summary line
    if article.ai_summary:
        first_line = article.ai_summary.split("\n")[0].lstrip("- ").strip()
        summary_line = _truncate(first_line)
    elif article.summary:
        summary_line = _truncate(article.summary)
    else:
        summary_line = ""

    # Insight line
    insight_line = ""
    if article.ai_insight:
        insight_line = f"💡 {_truncate(article.ai_insight.split(chr(10))[0])}"

    parts = [title_line]
    if summary_line:
        parts.append(f"   {summary_line}")
    if insight_line:
        parts.append(f"   {insight_line}")

    text = "\n".join(parts)
    return {"type": "section", "text": {"type": "mrkdwn", "text": text}}


def notify(webhook_url: str, articles: list[Article]) -> bool:
    """Send article summary to Slack via webhook."""
    kst = timezone(timedelta(hours=9))
    today = datetime.now(kst).strftime("%Y-%m-%d")

    if not articles:
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📰 GeekNews 데일리 - {today}",
                },
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "새로운 기사가 없습니다"},
            },
        ]
    else:
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📰 GeekNews 데일리 - {today} ({len(articles)}건)",
                },
            },
        ]
        for idx, article in enumerate(articles, 1):
            blocks.append(_build_article_block(idx, article))
            if idx < len(articles):
                blocks.append({"type": "divider"})

    try:
        response = requests.post(webhook_url, json={"blocks": blocks}, timeout=10)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to send Slack notification: {e}")
        return False
