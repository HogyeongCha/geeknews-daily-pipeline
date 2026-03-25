from dataclasses import dataclass
import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


@dataclass
class Config:
    slack_webhook_url: str
    obsidian_vault_path: str
    geeknews_url: str = "https://news.hada.io/new"
    github_token: str = ""
    github_model: str = "openai/gpt-4o-mini"


def load_config() -> Config:
    if load_dotenv:
        load_dotenv(override=False)

    slack_webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    obsidian_vault_path = os.environ.get("OBSIDIAN_VAULT_PATH")
    geeknews_url = os.environ.get("GEEKNEWS_URL")
    github_token = os.environ.get("GITHUB_TOKEN", "")
    github_model = os.environ.get("GITHUB_MODEL", "openai/gpt-4o-mini")

    missing = []
    if not slack_webhook_url:
        missing.append("SLACK_WEBHOOK_URL")
    if not obsidian_vault_path:
        missing.append("OBSIDIAN_VAULT_PATH")

    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    return Config(
        slack_webhook_url=slack_webhook_url,
        obsidian_vault_path=obsidian_vault_path,
        geeknews_url=geeknews_url or "https://news.hada.io/new",
        github_token=github_token,
        github_model=github_model,
    )