import logging
import os
from datetime import datetime, timezone, timedelta

from src.config import load_config
from src.crawler import crawl
from src.markdown_generator import generate_markdown
from src.obsidian_storage import save_to_vault
from src.slack_notifier import notify
from src.summarizer import summarize_articles

logger = logging.getLogger(__name__)


def handler(event: dict, context) -> dict:
    """AWS Lambda handler that orchestrates the pipeline."""
    try:
        # 1. Load config
        config = load_config()

        # 2. Crawl GeekNews
        articles = crawl(config.geeknews_url)

        # 3. AI summarization (if token configured)
        if articles and config.github_token:
            summaries = summarize_articles(
                articles, config.github_token, config.github_model
            )
            for article, (ai_summary, ai_insight) in zip(articles, summaries):
                article.ai_summary = ai_summary
                article.ai_insight = ai_insight
        elif not config.github_token:
            logger.info("GITHUB_TOKEN not set, skipping AI summarization")

        # 4. Generate markdown (use KST date)
        kst = timezone(timedelta(hours=9))
        today = datetime.now(kst).strftime("%Y-%m-%d")
        filename, content = generate_markdown(articles, today)

        # 5. Save markdown
        saved_path = None
        if config.obsidian_vault_path:
            # Local mode: save to Obsidian Vault
            saved_path = save_to_vault(config.obsidian_vault_path, filename, content)
        else:
            # CI mode: save to output/ directory (for GitHub Actions commit)
            output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
            os.makedirs(output_dir, exist_ok=True)
            saved_path = os.path.join(output_dir, filename)
            with open(saved_path, "w", encoding="utf-8") as f:
                f.write(content)

        # 6. Send Slack notification
        notify(config.slack_webhook_url, articles)

        return {
            "statusCode": 200,
            "body": {
                "articles_count": len(articles),
                "saved_path": saved_path,
            },
        }

    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        return {"statusCode": 500, "body": {"error": str(e)}}


if __name__ == "__main__":
    result = handler({}, None)
    print(result)
