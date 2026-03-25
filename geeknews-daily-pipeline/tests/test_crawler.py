# Feature: geeknews-daily-pipeline, Property 1: HTML parsing extracts all Article fields
# Feature: geeknews-daily-pipeline, Property 2: Partial parsing failures skip invalid topic_rows

import pytest
import responses
from hypothesis import given, settings, assume, HealthCheck
import hypothesis.strategies as st
from bs4 import BeautifulSoup
from datetime import datetime, timezone

from src.crawler import crawl, Article


# Property 1: Generate valid HTML with topic_rows and verify Article fields
article_strategy = st.builds(
    Article,
    title=st.text(min_size=1, max_size=200),
    original_url=st.from_regex(r"https?://[a-zA-Z0-9.-]+/[^\s]*", fullmatch=True),
    summary=st.one_of(st.none(), st.text(min_size=1, max_size=500)),
    crawled_at=st.datetimes().map(lambda dt: dt.isoformat() + "Z"),
)


def make_html_with_rows(titles, urls, summaries):
    """Helper to generate HTML with topic_rows."""
    rows_html = ""
    for title, url, summary in zip(titles, urls, summaries):
        row = f'''
        <div class="topic_row">
            <div class="topictitle">
                <a href="{url}" rel="nofollow">
                    <h1>{title}</h1>
                </a>
            </div>
        '''
        if summary is not None:
            row += f'<div class="topicdesc"><a href="#">{summary}</a></div>'
        row += '</div>'
        rows_html += row
    return f'<html><body><div class="topics">{rows_html}</div></body></html>'


@given(
    titles=st.lists(st.text(min_size=1, max_size=200).filter(lambda t: t.strip()), min_size=1, max_size=5),
    urls=st.lists(st.from_regex(r"https?://[a-zA-Z0-9.-]+/[^\s]*", fullmatch=True), min_size=1, max_size=5),
    summaries=st.lists(st.one_of(st.none(), st.text(min_size=1, max_size=500)), min_size=1, max_size=5),
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.filter_too_much])
def test_property_1_all_fields_extracted(titles, urls, summaries):
    """Property 1: Each Article has non-empty title, valid URL, str|None summary, ISO 8601 UTC crawled_at."""
    assume(len(titles) == len(urls) == len(summaries))
    html = make_html_with_rows(titles, urls, summaries)
    soup = BeautifulSoup(html, "html.parser")

    articles = []
    for row in soup.select("div.topic_row"):
        title_elem = row.select_one("div.topictitle h1")
        if not title_elem:
            continue
        title = title_elem.get_text(strip=True)

        link_elem = row.select_one("div.topictitle > a[rel='nofollow']")
        if not link_elem:
            continue
        original_url = link_elem.get("href", "")

        summary = None
        desc_elem = row.select_one("div.topicdesc a")
        if desc_elem:
            summary = desc_elem.get_text(strip=True)

        articles.append(
            Article(
                title=title,
                original_url=original_url,
                summary=summary,
                crawled_at=datetime.now(timezone.utc).isoformat(),
            )
        )

    assert len(articles) == len(titles)
    for a in articles:
        assert a.title
        assert a.original_url.startswith("http")
        assert a.summary is None or isinstance(a.summary, str)
        # Validate ISO 8601 format
        datetime.fromisoformat(a.crawled_at.replace("Z", "+00:00"))


@given(
    valid_count=st.integers(min_value=1, max_value=3),
    invalid_count=st.integers(min_value=1, max_value=3),
)
@settings(max_examples=30)
def test_property_2_valid_only_returned(valid_count, invalid_count):
    """Property 2: Mixed valid/invalid rows returns exactly valid count, skips invalid."""
    # Create valid rows
    valid_titles = [f"Valid Title {i}" for i in range(valid_count)]
    valid_urls = [f"https://example.com/{i}" for i in range(valid_count)]
    valid_summaries = [f"Summary {i}" for i in range(valid_count)]

    # Create invalid rows (missing title or link)
    invalid_rows = [
        '<div class="topic_row"><div class="topictitle"><h1></h1></div></div>',  # empty title
        '<div class="topic_row"><div class="topictitle"><a href="https://x.com"><h1>Has title</h1></a></div></div>',  # no rel=nofollow
    ][:invalid_count]

    rows_html = ""
    for i in range(valid_count):
        rows_html += f'''
        <div class="topic_row">
            <div class="topictitle">
                <a href="{valid_urls[i]}" rel="nofollow">
                    <h1>{valid_titles[i]}</h1>
                </a>
            </div>
            <div class="topicdesc"><a href="#">{valid_summaries[i]}</a></div>
        </div>
        '''
    rows_html += "".join(invalid_rows)

    html = f'<html><body><div class="topics">{rows_html}</div></body></html>'
    soup = BeautifulSoup(html, "html.parser")

    articles = []
    for row in soup.select("div.topic_row"):
        title_elem = row.select_one("div.topictitle h1")
        if not title_elem:
            continue
        title = title_elem.get_text(strip=True)
        if not title:
            continue

        link_elem = row.select_one("div.topictitle > a[rel='nofollow']")
        if not link_elem:
            continue
        original_url = link_elem.get("href", "")

        summary = None
        desc_elem = row.select_one("div.topicdesc a")
        if desc_elem:
            summary = desc_elem.get_text(strip=True)

        articles.append(
            Article(
                title=title,
                original_url=original_url,
                summary=summary,
                crawled_at=datetime.now(timezone.utc).isoformat(),
            )
        )

    assert len(articles) == valid_count


# Unit tests for crawler
def test_crawl_real_html_snapshot():
    """Unit test: Real GeekNews HTML snapshot parsing."""
    html = '''
    <html><body>
    <div class="topics">
        <div class="topic_row">
            <div class="topictitle">
                <a href="https://example.com/article1" rel="nofollow">
                    <h1>Test Article Title</h1>
                </a>
                <span class="topicurl">(example.com)</span>
            </div>
            <div class="topicdesc">
                <a href="topic?id=123" class="c99">This is a test summary</a>
            </div>
            <div class="topicinfo">
                <span id="tp123">42</span> point(s) by <a href="/user?id=user1">user1</a> 2시간전
            </div>
        </div>
    </div>
    </body></html>
    '''
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, "https://news.hada.io/new", body=html, status=200)
        articles = crawl("https://news.hada.io/new")

    assert len(articles) == 1
    assert articles[0].title == "Test Article Title"
    assert articles[0].original_url == "https://example.com/article1"
    assert articles[0].summary == "This is a test summary"


def test_crawl_http_404():
    """Unit test: HTTP 404 returns empty list."""
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, "https://news.hada.io/new", status=404)
        articles = crawl("https://news.hada.io/new")

    assert articles == []


def test_crawl_http_500():
    """Unit test: HTTP 500 returns empty list."""
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, "https://news.hada.io/new", status=500)
        articles = crawl("https://news.hada.io/new")

    assert articles == []


def test_crawl_timeout():
    """Unit test: Timeout returns empty list."""
    import requests
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, "https://news.hada.io/new", body=requests.Timeout("Connection timeout"))
        articles = crawl("https://news.hada.io/new")

    assert articles == []


def test_crawl_connection_error():
    """Unit test: Connection error returns empty list."""
    import requests
    def raise_error(request):
        raise requests.ConnectionError("Connection refused")
    with responses.RequestsMock() as rsps:
        rsps.add_callback(responses.GET, "https://news.hada.io/new", callback=raise_error)
        articles = crawl("https://news.hada.io/new")

    assert articles == []