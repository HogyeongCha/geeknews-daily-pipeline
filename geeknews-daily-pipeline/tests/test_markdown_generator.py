"""Tests for Markdown Generator module.

# Feature: geeknews-daily-pipeline, Property 3: filename format validation
# Feature: geeknews-daily-pipeline, Property 4: round-trip validation
# Feature: geeknews-daily-pipeline, Unit: empty list and None summary handling
"""
import re
from datetime import date
from hypothesis import given, settings, assume
import hypothesis.strategies as st

from src.markdown_generator import generate_markdown, parse_markdown
from src.crawler import Article


# Strategies - filtered to avoid markdown parsing edge cases
article_strategy = st.builds(
    Article,
    title=st.text(min_size=1, max_size=200).filter(
        lambda t: t.strip() and t == t.strip() and not t.startswith('#') and '\n' not in t and '(' not in t and ')' not in t
    ),
    original_url=st.from_regex(r"https://[a-z]+\.[a-z]+/[a-z0-9]+", fullmatch=True),
    summary=st.one_of(
        st.none(),
        st.text(min_size=1, max_size=500).filter(
            lambda s: s == s.strip() and '\n' not in s and '(' not in s and ')' not in s and not any(ord(c) < 32 for c in s)
        )
    ),
    crawled_at=st.datetimes().map(lambda dt: dt.isoformat() + "Z"),
)

date_strategy = st.dates().map(lambda d: d.isoformat())


# Property 3: Filename format validation
@given(date_strategy)
@settings(max_examples=100)
def test_property_3_filename_format(date_str: str):
    """For any valid date string, filename matches YYYY-MM-DD-geeknews.md."""
    articles = [Article(title="Test", original_url="https://example.com/1", summary=None, crawled_at="2024-01-01T00:00:00Z")]
    filename, _ = generate_markdown(articles, date_str)
    assert re.match(r"^\d{4}-\d{2}-\d{2}-geeknews\.md$", filename), f"Invalid filename: {filename}"


# Property 4: Round-trip validation
@given(st.lists(article_strategy, min_size=1, max_size=10), date_strategy)
@settings(max_examples=100)
def test_property_4_round_trip(articles: list[Article], date_str: str):
    """generate_markdown then parse_markdown yields same title, original_url, summary."""
    filename, markdown = generate_markdown(articles, date_str)
    parsed = parse_markdown(markdown)
    
    assert len(parsed) == len(articles)
    for orig, parsed_article in zip(articles, parsed):
        assert parsed_article["title"] == orig.title
        assert parsed_article["original_url"] == orig.original_url
        # Articles without ai_summary fall back to summary field in new format
        if orig.ai_summary:
            assert parsed_article["ai_summary"] is not None
        else:
            assert parsed_article.get("summary") == orig.summary or parsed_article.get("ai_summary") is None


# Unit test: Empty article list
def test_empty_article_list():
    """Empty Article list produces valid markdown with only header."""
    filename, content = generate_markdown([], "2024-01-15")
    assert filename == "2024-01-15-geeknews.md"
    assert "GeekNews" in content
    assert content.count("## ") == 0


# Unit test: Article with ai_summary renders properly
def test_ai_summary_renders():
    """Article with ai_summary should render the AI summary section."""
    articles = [
        Article(
            title="Test Article",
            original_url="https://example.com/1",
            summary="Original summary",
            crawled_at="2024-01-15T00:00:00Z",
            ai_summary="- AI가 생성한 요약입니다",
            ai_insight="개발자에게 중요한 이유입니다",
        )
    ]
    _, content = generate_markdown(articles, "2024-01-15")
    assert "### 핵심 요약" in content
    assert "AI가 생성한 요약입니다" in content
    assert "### 💡 왜 중요한가" in content
    assert "개발자에게 중요한 이유입니다" in content


# Unit test: Article without ai_summary falls back to original summary
def test_fallback_to_original_summary():
    """Article without ai_summary should show original summary with 📝 prefix."""
    articles = [
        Article(
            title="Test Article",
            original_url="https://example.com/1",
            summary="Original summary",
            crawled_at="2024-01-15T00:00:00Z",
        )
    ]
    _, content = generate_markdown(articles, "2024-01-15")
    assert "📝 Original summary" in content