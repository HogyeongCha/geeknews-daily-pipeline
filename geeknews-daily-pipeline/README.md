# GeekNews Daily Pipeline

Automatically crawl GeekNews latest articles daily, save as Obsidian markdown, and send Slack notifications.

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your settings:
#   SLACK_WEBHOOK_URL=...
#   OBSIDIAN_VAULT_PATH=...
```

## Local Execution

```bash
python -m src.handler
```

## Testing

```bash
pytest
```

## Deployment

```bash
# Create Lambda deployment ZIP
./scripts/package.sh
```

Upload the generated `geeknews-daily-pipeline.zip` to AWS Lambda.

### EventBridge Schedule

The pipeline runs daily at 8:00 AM (KST) via EventBridge:

```
cron(0 23 * * ? *)
```

This is UTC 23:00 = KST 08:00 (previous day).

## Architecture

- **Crawler**: Fetches GeekNews articles
- **Markdown Generator**: Converts articles to Obsidian markdown
- **Obsidian Storage**: Saves markdown to vault
- **Slack Notifier**: Sends summary to Slack
- **Lambda Handler**: Orchestrates the pipeline