# Implementation Plan: GeekNews Daily Pipeline

## 개요

GeekNews 크롤링 → Obsidian 마크다운 저장 → Slack 알림의 자동화 파이프라인을 Python + AWS Lambda로 구현한다. 각 모듈을 독립적으로 구현하고, 속성 기반 테스트와 단위 테스트로 검증한 뒤, Lambda 핸들러로 통합하고 배포 패키징까지 완료한다.

## Tasks

- [x] 1. 프로젝트 구조 및 기본 설정
  - [x] 1.1 프로젝트 디렉토리 구조 생성 및 의존성 파일 작성
    - `src/`, `tests/`, `scripts/` 디렉토리 생성
    - `src/__init__.py`, `tests/__init__.py` 생성
    - `requirements.txt` 작성 (`requests`, `beautifulsoup4`, `python-dotenv`)
    - `requirements-dev.txt` 작성 (`pytest`, `hypothesis`, `responses`)
    - `.env.example` 작성 (`SLACK_WEBHOOK_URL`, `OBSIDIAN_VAULT_PATH`, `GEEKNEWS_URL`)
    - _Requirements: 5.2, 7.2_

  - [x] 1.2 Config Loader 모듈 구현 (`src/config.py`)
    - `Config` dataclass 정의 (`slack_webhook_url`, `obsidian_vault_path`, `geeknews_url`)
    - `load_config()` 함수 구현: `.env` 파일 로드 + 시스템 환경 변수 우선
    - 필수 변수 누락 시 변수명 포함 `ValueError` 발생
    - Lambda 환경에서 `.env` 파일 없이도 정상 동작
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [x]* 1.3 Config Loader 속성 기반 테스트 작성 (`tests/test_config.py`)
    - **Property 8: Config에서 지원하는 환경 변수 로드**
    - **Validates: Requirements 5.2**
    - **Property 9: 필수 환경 변수 누락 시 에러 메시지에 변수명 포함**
    - **Validates: Requirements 5.3**
    - **Property 10: 시스템 환경 변수가 .env 파일보다 우선**
    - **Validates: Requirements 5.4**

- [x] 2. Checkpoint - 기본 설정 검증
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. GeekNews 크롤러 구현
  - [x] 3.1 Crawler 모듈 구현 (`src/crawler.py`)
    - `Article` dataclass 정의 (`title`, `original_url`, `summary`, `crawled_at`)
    - `crawl(url)` 함수 구현: HTTP GET → BeautifulSoup 파싱 → Article 목록 반환
    - `div.topics > div.topic_row` 선택자로 각 포스팅 파싱
    - `div.topictitle h1`에서 제목, `a[rel=nofollow]`에서 원본 링크, `div.topicdesc a`에서 요약 추출
    - `html.unescape()`로 HTML 엔티티 처리
    - 접근 불가 시 에러 로깅 후 빈 리스트 반환
    - 개별 항목 파싱 실패 시 해당 항목 건너뛰기
    - 각 Article에 수집 일시(UTC, ISO 8601) 포함
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [x]* 3.2 Crawler 속성 기반 테스트 작성 (`tests/test_crawler.py`)
    - **Property 1: HTML 파싱 시 모든 Article 필드 추출**
    - **Validates: Requirements 1.2, 1.5**
    - **Property 2: 부분 파싱 실패 시 유효한 Article만 반환**
    - **Validates: Requirements 1.4**

  - [x]* 3.3 Crawler 단위 테스트 작성 (`tests/test_crawler.py`)
    - 실제 GeekNews HTML 스냅샷으로 파싱 검증
    - HTTP 에러 시나리오 테스트 (404, 500, timeout)
    - 접근 불가 시 빈 리스트 반환 검증
    - _Requirements: 1.1, 1.3_

- [x] 4. 마크다운 생성기 구현
  - [x] 4.1 Markdown Generator 모듈 구현 (`src/markdown_generator.py`)
    - `generate_markdown(articles, date)` 함수 구현: Article 목록 → (filename, markdown_content) 반환
    - 파일명 형식: `YYYY-MM-DD-geeknews.md`
    - 각 Article을 제목, 원본 링크, 요약 포함 마크다운 섹션으로 포맷
    - `parse_markdown(content)` 함수 구현: 라운드트립 검증용 파서
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x]* 4.2 Markdown Generator 속성 기반 테스트 작성 (`tests/test_markdown_generator.py`)
    - **Property 3: 마크다운 파일명 형식**
    - **Validates: Requirements 2.3**
    - **Property 4: 마크다운 라운드트립**
    - **Validates: Requirements 2.4**

  - [x]* 4.3 Markdown Generator 단위 테스트 작성 (`tests/test_markdown_generator.py`)
    - 빈 Article 목록 처리 검증
    - 요약이 None인 Article 포맷 검증
    - _Requirements: 2.1, 2.2_

- [x] 5. Checkpoint - 크롤러 및 마크다운 생성기 검증
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Obsidian 저장소 구현
  - [x] 6.1 Obsidian Storage 모듈 구현 (`src/obsidian_storage.py`)
    - `save_to_vault(vault_path, filename, content)` 함수 구현
    - 동일 파일 존재 시 덮어쓰기
    - Vault 경로 미존재 시 `FileNotFoundError` 로깅 후 에러 발생
    - 저장된 파일의 전체 경로 반환
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x]* 6.2 Obsidian Storage 속성 기반 테스트 작성 (`tests/test_obsidian_storage.py`)
    - **Property 5: 파일 저장 라운드트립**
    - **Validates: Requirements 3.1, 3.4**
    - **Property 6: 파일 저장 멱등성 (덮어쓰기)**
    - **Validates: Requirements 3.2**

  - [x]* 6.3 Obsidian Storage 단위 테스트 작성 (`tests/test_obsidian_storage.py`)
    - 존재하지 않는 vault 경로 에러 검증
    - 파일 권한 에러 검증
    - _Requirements: 3.3_

- [x] 7. Slack 알림 구현
  - [x] 7.1 Slack Notifier 모듈 구현 (`src/slack_notifier.py`)
    - `notify(webhook_url, articles)` 함수 구현
    - Block Kit 형식으로 메시지 구성 (header + section)
    - 각 기사의 제목과 원본 링크 포함
    - 빈 목록 시 "새로운 기사가 없습니다" 메시지 전송
    - 전송 실패 시 로깅 후 `False` 반환 (예외 미발생)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x]* 7.2 Slack Notifier 속성 기반 테스트 작성 (`tests/test_slack_notifier.py`)
    - **Property 7: Slack 메시지에 모든 기사 제목과 링크 포함**
    - **Validates: Requirements 4.2**

  - [x]* 7.3 Slack Notifier 단위 테스트 작성 (`tests/test_slack_notifier.py`)
    - 빈 목록 시 "새로운 기사가 없습니다" 메시지 검증
    - Webhook 실패 시 False 반환 검증
    - _Requirements: 4.4, 4.5_

- [x] 8. Checkpoint - 개별 모듈 검증
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Lambda 핸들러 및 파이프라인 통합
  - [x] 9.1 Lambda Handler 구현 (`src/handler.py`)
    - `handler(event, context)` 함수 구현: Config → Crawler → Markdown Generator → Obsidian Storage → Slack Notifier 순서 실행
    - 성공 시 `{"statusCode": 200, "body": {"articles_count": N, "saved_path": "..."}}` 반환
    - 에러 시 로깅 후 `{"statusCode": 500, "body": {"error": "..."}}` 반환
    - `if __name__ == "__main__"` 블록으로 로컬 실행 지원 (`python -m src.handler`)
    - 로컬 실행 시 `.env` 파일에서 환경 변수 로드
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x]* 9.2 Lambda Handler 속성 기반 테스트 작성 (`tests/test_handler.py`)
    - **Property 11: 파이프라인 에러 시 실패 상태 반환**
    - **Validates: Requirements 6.5**

  - [x]* 9.3 Lambda Handler 단위 테스트 작성 (`tests/test_handler.py`)
    - 정상 파이프라인 실행 흐름 검증 (모킹)
    - 로컬 실행 모드 검증
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 10. Checkpoint - 파이프라인 통합 검증
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Lambda 배포 패키징 및 스케줄링
  - [x] 11.1 배포 패키징 스크립트 작성 (`scripts/package.sh`)
    - 임시 디렉토리에 `requirements.txt` 의존성 설치
    - `src/` 코드 복사
    - `.env`, `__pycache__/`, `test_*.py` 파일 제외
    - ZIP 생성 후 경로와 크기 출력
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [x] 11.2 EventBridge 스케줄 cron 표현식 문서화 (`README.md`)
    - cron 표현식: `cron(0 23 * * ? *)` (UTC 23:00 = KST 08:00)
    - Lambda 핸들러 설정 및 배포 가이드 작성
    - _Requirements: 8.1, 8.2_

- [x] 12. Final Checkpoint - 전체 파이프라인 검증
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- `*` 표시된 태스크는 선택 사항이며, 빠른 MVP를 위해 건너뛸 수 있습니다
- 각 태스크는 추적 가능성을 위해 특정 요구사항을 참조합니다
- Checkpoint에서 모든 테스트가 통과하는지 확인합니다
- 속성 기반 테스트는 보편적 정확성 속성을 검증합니다
- 단위 테스트는 구체적 예시와 엣지 케이스를 검증합니다
