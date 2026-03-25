import re
from src.crawler import Article


def generate_markdown(articles: list[Article], date: str) -> tuple[str, str]:
    """Generate markdown content from Article list.

    Returns: (filename, markdown_content)
    filename format: "YYYY-MM-DD-geeknews.md"
    """
    filename = f"{date}-geeknews.md"

    lines = [f"# 📰 GeekNews 데일리 - {date}", ""]
    lines.append(f"> 총 {len(articles)}건의 기사가 수집되었습니다.")
    lines.append("")

    for idx, article in enumerate(articles, 1):
        lines.append(f"## {idx}. {article.title}")
        lines.append("")
        lines.append(f"🔗 [원문 보기]({article.original_url})")
        lines.append("")

        if article.ai_summary:
            lines.append("### 핵심 요약")
            lines.append("")
            lines.append(article.ai_summary)
            lines.append("")

        if article.ai_insight:
            lines.append("### 💡 왜 중요한가")
            lines.append("")
            lines.append(article.ai_insight)
            lines.append("")
        elif article.summary:
            lines.append(f"📝 {article.summary}")
            lines.append("")

        lines.append("---")
        lines.append("")

    return filename, "\n".join(lines)


def parse_markdown(content: str) -> list[dict]:
    """Parse markdown content back to list of dicts.

    Returns list of dicts with keys: title, original_url, summary, ai_summary, ai_insight
    """
    result = []
    lines = content.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Match "## 1. Title" or "## Title"
        heading_match = re.match(r"^## (?:\d+\.\s+)?(.+)$", line)
        if heading_match:
            title = heading_match.group(1).strip()
            i += 1

            original_url = None
            summary = None
            ai_summary = None
            ai_insight = None

            while i < len(lines):
                line = lines[i].strip()
                if line.startswith("## ") or line.startswith("# "):
                    break

                # Parse original URL
                url_match = re.search(r"🔗 \[원문 보기\]\((.+)\)", line)
                if url_match:
                    original_url = url_match.group(1)
                    i += 1
                    continue

                # Legacy format support
                legacy_url_match = re.search(
                    r"- 🔗 원본 링크: \[.+\]\((.+)\)$", line
                )
                if legacy_url_match:
                    original_url = legacy_url_match.group(1)
                    i += 1
                    continue

                if line.startswith("- 📝 요약: "):
                    summary = line[len("- 📝 요약: "):]
                    if summary == "요약 없음":
                        summary = None
                    i += 1
                    continue

                if line.startswith("📝 "):
                    summary = line[len("📝 "):]
                    i += 1
                    continue

                # Parse AI summary section
                if line == "### 핵심 요약":
                    i += 1
                    summary_lines = []
                    while i < len(lines):
                        l = lines[i].strip()
                        if l.startswith("### ") or l.startswith("## ") or l.startswith("# ") or l == "---":
                            break
                        if l:
                            summary_lines.append(l)
                        i += 1
                    ai_summary = "\n".join(summary_lines) if summary_lines else None
                    continue

                # Parse AI insight section
                if line == "### 💡 왜 중요한가":
                    i += 1
                    insight_lines = []
                    while i < len(lines):
                        l = lines[i].strip()
                        if l.startswith("### ") or l.startswith("## ") or l.startswith("# ") or l == "---":
                            break
                        if l:
                            insight_lines.append(l)
                        i += 1
                    ai_insight = "\n".join(insight_lines) if insight_lines else None
                    continue

                i += 1

            if title and original_url:
                result.append({
                    "title": title,
                    "original_url": original_url,
                    "summary": summary,
                    "ai_summary": ai_summary,
                    "ai_insight": ai_insight,
                })
        else:
            i += 1

    return result
