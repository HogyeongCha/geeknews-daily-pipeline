# Repository Guidelines

## Project Structure & Module Organization

This repository is a wrapper around the main Python app in `geeknews-daily-pipeline/`. Core pipeline code lives in `geeknews-daily-pipeline/src/`:
`handler.py` orchestrates the run, `crawler.py` fetches GeekNews, `summarizer.py` calls GitHub Models, `markdown_generator.py` builds the note, and `slack_notifier.py` sends alerts. Tests live in `geeknews-daily-pipeline/tests/` and follow the source module layout. Generated markdown is written to `geeknews-daily-pipeline/output/`. Automation lives in `.github/workflows/daily-pipeline.yml`; Kiro notes and specs live in `.kiro/`.

## Build, Test, and Development Commands

Run commands from the repository root unless noted.

- `pip install -r geeknews-daily-pipeline/requirements.txt` installs runtime dependencies.
- `pip install -r geeknews-daily-pipeline/requirements-dev.txt` installs `pytest`, `hypothesis`, and `responses`.
- `cd geeknews-daily-pipeline && python -m src.handler` runs the pipeline locally.
- `cd geeknews-daily-pipeline && pytest` runs the full test suite.
- `bash geeknews-daily-pipeline/scripts/package.sh` builds the deployment package.
- `powershell -ExecutionPolicy Bypass -File geeknews-daily-pipeline/scripts/sync-to-obsidian.ps1` syncs generated notes into an Obsidian vault on Windows.

## Coding Style & Naming Conventions

Target Python 3.12 to match GitHub Actions. Follow existing style: 4-space indentation, small focused modules, `snake_case` for functions and variables, and short docstrings on public functions and tests. Keep imports explicit (`from src...`) and preserve the current module-per-responsibility structure. No formatter or linter is configured here, so keep changes consistent with adjacent code and avoid opportunistic rewrites.

## Testing Guidelines

Use `pytest` for unit tests and `hypothesis` for property-based coverage where behavior benefits from input variation. Add tests in `geeknews-daily-pipeline/tests/test_<module>.py`. Prefer mocking external calls to Slack, HTTP, and model APIs so tests stay deterministic. Cover both success and failure paths for pipeline stages.

## Commit & Pull Request Guidelines

Recent history uses short conventional prefixes such as `feat:`, `fix:`, `docs:`, and `chore:`. Keep that format, for example: `fix: handle missing GitHub token in CI`. PRs should include a concise summary, any config or secret changes, linked issues when applicable, and sample output or screenshots when the generated markdown or workflow behavior changes.

## Security & Configuration Tips

Treat `geeknews-daily-pipeline/.env` and GitHub Actions secrets as sensitive. Do not hardcode `SLACK_WEBHOOK_URL`, `GITHUB_TOKEN`, or vault paths. Validate changes to `.github/workflows/daily-pipeline.yml` carefully because they affect the scheduled production run.
