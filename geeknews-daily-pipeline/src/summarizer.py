import logging
from typing import Optional

import requests

from src.crawler import Article

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """당신은 IT/개발 뉴스 전문 요약가입니다.
주어진 기사 정보를 바탕으로 한국어로 핵심 요약과 인사이트를 제공합니다.

반드시 아래 형식으로만 응답하세요:
[핵심 요약]
- (3~5개의 핵심 포인트를 각각 한 줄로)

[왜 중요한가]
(개발자/IT 종사자에게 이 기사가 왜 중요한지 1~2문장으로)"""


def _build_user_prompt(article: Article) -> str:
    parts = [f"제목: {article.title}", f"원본 URL: {article.original_url}"]
    if article.summary:
        parts.append(f"요약: {article.summary}")
    return "\n".join(parts)


def _parse_ai_response(text: str) -> tuple[Optional[str], Optional[str]]:
    """Parse AI response into (ai_summary, ai_insight)."""
    ai_summary = None
    ai_insight = None

    if "[핵심 요약]" in text:
        after_summary = text.split("[핵심 요약]", 1)[1]
        if "[왜 중요한가]" in after_summary:
            summary_part = after_summary.split("[왜 중요한가]", 1)[0].strip()
            insight_part = after_summary.split("[왜 중요한가]", 1)[1].strip()
            ai_summary = summary_part
            ai_insight = insight_part
        else:
            ai_summary = after_summary.strip()
    elif "[왜 중요한가]" in text:
        ai_insight = text.split("[왜 중요한가]", 1)[1].strip()
    else:
        ai_summary = text.strip()

    return ai_summary, ai_insight


def summarize_article(
    article: Article, github_token: str, model: str = "openai/gpt-4o-mini"
) -> tuple[Optional[str], Optional[str]]:
    """Call GitHub Models API to generate Korean summary for an article.

    Returns: (ai_summary, ai_insight)
    """
    url = "https://models.github.ai/inference/chat/completions"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(article)},
        ],
        "temperature": 0.3,
        "max_tokens": 500,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return _parse_ai_response(content)
    except Exception as e:
        logger.warning(f"Failed to summarize '{article.title}': {e}")
        return None, None


def summarize_articles(
    articles: list[Article],
    github_token: str,
    model: str = "openai/gpt-4o-mini",
) -> list[tuple[Optional[str], Optional[str]]]:
    """Summarize all articles. Returns list of (ai_summary, ai_insight) tuples."""
    results = []
    for article in articles:
        ai_summary, ai_insight = summarize_article(article, github_token, model)
        results.append((ai_summary, ai_insight))
    return results
