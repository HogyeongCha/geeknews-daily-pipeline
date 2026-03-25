from dataclasses import dataclass
from datetime import datetime, timezone
import html
import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class Article:
    title: str
    original_url: str
    summary: Optional[str]
    crawled_at: str  # ISO 8601 UTC
    ai_summary: Optional[str] = None
    ai_insight: Optional[str] = None


def crawl(url: str) -> list[Article]:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    topics_container = soup.select_one("div.topics")
    if not topics_container:
        logger.warning("div.topics not found in response")
        return []

    articles = []
    for row in topics_container.select("div.topic_row"):
        try:
            title_elem = row.select_one("div.topictitle h1")
            if not title_elem:
                continue
            title = html.unescape(title_elem.get_text(strip=True))
            if not title:
                continue

            link_elem = row.select_one("div.topictitle > a[rel='nofollow']")
            if not link_elem:
                continue
            original_url = link_elem.get("href", "")

            summary = None
            desc_elem = row.select_one("div.topicdesc a")
            if desc_elem:
                summary = html.unescape(desc_elem.get_text(strip=True))

            articles.append(
                Article(
                    title=title,
                    original_url=original_url,
                    summary=summary,
                    crawled_at=datetime.now(timezone.utc).isoformat(),
                )
            )
        except Exception as e:
            logger.warning(f"Failed to parse topic_row: {e}")
            continue

    return articles