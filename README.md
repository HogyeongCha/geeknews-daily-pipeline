# GeekNews Daily Pipeline

GeekNews 최신 글을 매일 크롤링하여 AI 한국어 요약을 생성하고, Obsidian 마크다운으로 저장한 뒤 Slack으로 알림을 보내는 자동화 파이프라인.

## 출력 예시

### Obsidian 마크다운

```markdown
# 📰 GeekNews 데일리 - 2026-03-25

> 총 20건의 기사가 수집되었습니다.

## 1. Claude Code로 20년 전 상용 게임을 브라우저로 이식하기까지

🔗 [원문 보기](https://example.com/article)

### 핵심 요약

- WebAssembly와 WebGL 기술을 활용하여 설치 없이 크롬에서 실행 가능
- 기존 게임의 코드와 자산을 거의 수정하지 않고 이식하는 데 성공
- 브라우저 기반 게임의 가능성을 보여주는 사례로 주목받음

### 💡 왜 중요한가

기존 게임을 현대 기술로 재구성하는 방법을 보여주며, 브라우저 기반 게임 개발의 새로운 가능성을 제시한다.
```

### Slack 알림

각 기사별로 제목, 요약 한 줄, 인사이트가 포함된 블록 형태로 전송됩니다.

## 아키텍처

```
EventBridge (cron: 0 23 * * ? *)
  ↓
Lambda Handler
  ├─ Config 로드 (.env / 시스템 환경 변수)
  ├─ GeekNews 크롤링 (BeautifulSoup)
  ├─ AI 한국어 요약 생성 (GitHub Models API)
  ├─ Obsidian Vault에 마크다운 저장
  └─ Slack Webhook 알림 전송
```

### 모듈 구조

```
geeknews-daily-pipeline/
├── src/
│   ├── handler.py            # Lambda 핸들러 (파이프라인 오케스트레이션)
│   ├── crawler.py            # GeekNews 크롤러
│   ├── summarizer.py         # GitHub Models API 기반 AI 요약
│   ├── markdown_generator.py # Obsidian 마크다운 생성
│   ├── obsidian_storage.py   # Obsidian Vault 파일 저장
│   ├── slack_notifier.py     # Slack 알림
│   └── config.py             # 환경 변수 관리
├── tests/                    # pytest + hypothesis 테스트
├── scripts/
│   └── package.sh            # Lambda 배포 패키징
├── .kiro/                    # Kiro spec 및 steering 파일
├── requirements.txt
└── requirements-dev.txt
```

## 설정

```bash
pip install -r requirements.txt

cp geeknews-daily-pipeline/.env.example geeknews-daily-pipeline/.env
```

`.env` 파일에 아래 값을 설정:

| 변수 | 설명 | 필수 |
|------|------|------|
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL | ✅ |
| `OBSIDIAN_VAULT_PATH` | Obsidian Vault 로컬 경로 | ✅ |
| `GEEKNEWS_URL` | GeekNews URL (기본값: `https://news.hada.io/new`) | |
| `GITHUB_TOKEN` | GitHub PAT (`models:read` 스코프) | AI 요약 사용 시 |
| `GITHUB_MODEL` | 사용할 모델 (기본값: `openai/gpt-4o-mini`) | |

### GitHub Token 발급

GitHub Models API를 사용하려면 `models:read` 스코프가 있는 Personal Access Token이 필요합니다.
GitHub 학생 계정이면 무료로 사용 가능합니다.

Settings → Developer settings → Personal access tokens → Fine-grained tokens

## 실행

```bash
# 로컬 실행
cd geeknews-daily-pipeline
python -m src.handler

# 테스트
pip install -r requirements-dev.txt
pytest
```

## 배포

```bash
./scripts/package.sh
```

생성된 ZIP을 AWS Lambda에 업로드하고, EventBridge 스케줄 규칙을 설정합니다:

```
cron(0 23 * * ? *)   # UTC 23:00 = KST 08:00
```
