# 요구사항 문서

## 소개

GeekNews(`https://news.hada.io/new`) 최신 글 페이지를 매일 크롤링하여 IT 기사 정보를 수집하고, 로컬 Obsidian 저장소에 마크다운으로 정리한 뒤 Slack으로 요약 알림을 보내는 자동화 파이프라인이다. AWS Lambda와 Python으로 구현하며, 로컬 테스트 및 배포 패키징을 지원한다.

## 용어 정의

- **Pipeline**: GeekNews 크롤링, Obsidian 저장, Slack 알림의 전체 자동화 흐름
- **Crawler**: GeekNews 최신 글 페이지에서 기사 정보를 추출하는 모듈
- **Article**: 크롤링으로 수집된 개별 기사 데이터 (제목, 원본 링크, 요약 포함)
- **Markdown_Generator**: Article 목록을 Obsidian 호환 마크다운 파일로 변환하는 모듈
- **Obsidian_Storage**: 로컬 Obsidian Vault 내 지정된 경로에 마크다운 파일을 저장하는 모듈
- **Slack_Notifier**: 수집된 기사 요약을 Slack 채널로 전송하는 모듈
- **Lambda_Handler**: AWS Lambda 진입점으로, Pipeline 전체를 실행하는 함수
- **Config_Loader**: `.env` 파일에서 환경 변수를 로드하는 모듈
- **Package_Script**: Lambda 배포용 ZIP 패키지를 생성하는 스크립트

## 요구사항

### 요구사항 1: GeekNews 크롤링

**사용자 스토리:** 개발자로서, GeekNews 최신 글 목록에서 기사 정보를 자동으로 수집하고 싶다. 이를 통해 매일 수동으로 사이트를 확인하지 않아도 된다.

#### 인수 조건

1. WHEN Pipeline이 실행되면, THE Crawler SHALL `https://news.hada.io/new` 페이지의 HTML을 가져온다
2. WHEN HTML을 파싱하면, THE Crawler SHALL 각 기사의 제목, 원본 링크, 요약 텍스트를 추출하여 Article 목록으로 반환한다
3. IF 크롤링 대상 페이지에 접근할 수 없으면, THEN THE Crawler SHALL 에러 메시지를 로깅하고 빈 Article 목록을 반환한다
4. IF HTML 구조가 예상과 다르면, THEN THE Crawler SHALL 파싱 실패를 로깅하고 파싱 가능한 Article만 반환한다
5. THE Crawler SHALL 각 Article에 수집 일시(UTC)를 포함한다

### 요구사항 2: 마크다운 생성

**사용자 스토리:** 개발자로서, 수집된 기사 데이터를 Obsidian에서 읽기 좋은 마크다운 형식으로 변환하고 싶다.

#### 인수 조건

1. WHEN Article 목록이 제공되면, THE Markdown_Generator SHALL 날짜별 마크다운 파일을 생성한다
2. THE Markdown_Generator SHALL 각 Article을 제목, 원본 링크, 요약을 포함하는 마크다운 섹션으로 포맷한다
3. THE Markdown_Generator SHALL 파일명을 `YYYY-MM-DD-geeknews.md` 형식으로 생성한다
4. FOR ALL 유효한 Article 목록에 대해, 마크다운으로 변환한 뒤 다시 파싱하면 원본 Article 데이터와 동일한 정보를 포함해야 한다 (라운드트립 속성)

### 요구사항 3: Obsidian 저장소 저장

**사용자 스토리:** 개발자로서, 생성된 마크다운 파일을 로컬 Obsidian Vault에 자동으로 저장하고 싶다. 이를 통해 Obsidian에서 바로 기사를 열람할 수 있다.

#### 인수 조건

1. WHEN 마크다운 파일이 생성되면, THE Obsidian_Storage SHALL 환경 변수로 지정된 Obsidian Vault 경로에 파일을 저장한다
2. IF 동일 날짜의 파일이 이미 존재하면, THEN THE Obsidian_Storage SHALL 기존 파일을 덮어쓴다
3. IF Obsidian Vault 경로가 존재하지 않으면, THEN THE Obsidian_Storage SHALL 에러를 로깅하고 저장 실패를 반환한다
4. WHEN 파일 저장이 완료되면, THE Obsidian_Storage SHALL 저장된 파일의 전체 경로를 반환한다

### 요구사항 4: Slack 알림

**사용자 스토리:** 개발자로서, 수집된 기사 요약을 Slack 채널로 받고 싶다. 이를 통해 Obsidian을 열지 않아도 새 기사를 빠르게 확인할 수 있다.

#### 인수 조건

1. WHEN Obsidian 저장이 완료되면, THE Slack_Notifier SHALL 수집된 Article 목록의 요약을 Slack 채널로 전송한다
2. THE Slack_Notifier SHALL 각 기사의 제목과 원본 링크를 포함하는 메시지를 구성한다
3. THE Slack_Notifier SHALL 환경 변수에서 Slack Webhook URL을 읽어 사용한다
4. IF Slack 전송에 실패하면, THEN THE Slack_Notifier SHALL 에러를 로깅하고 Pipeline 실행을 중단하지 않는다
5. IF Article 목록이 비어있으면, THEN THE Slack_Notifier SHALL "새로운 기사가 없습니다" 메시지를 전송한다

### 요구사항 5: 환경 변수 관리

**사용자 스토리:** 개발자로서, 민감한 설정값을 `.env` 파일로 관리하고 싶다. 이를 통해 코드에 비밀 정보를 하드코딩하지 않아도 된다.

#### 인수 조건

1. THE Config_Loader SHALL `.env` 파일에서 환경 변수를 로드한다
2. THE Config_Loader SHALL 다음 환경 변수를 지원한다: `SLACK_WEBHOOK_URL`, `OBSIDIAN_VAULT_PATH`, `GEEKNEWS_URL`
3. IF 필수 환경 변수가 누락되면, THEN THE Config_Loader SHALL 누락된 변수명을 포함한 에러 메시지를 발생시킨다
4. WHEN Lambda 환경에서 실행되면, THE Config_Loader SHALL 시스템 환경 변수를 우선 사용하고, `.env` 파일이 없어도 정상 동작한다

### 요구사항 6: Lambda 핸들러 및 로컬 테스트

**사용자 스토리:** 개발자로서, Lambda 핸들러를 로컬에서 직접 실행하여 테스트하고 싶다. 이를 통해 배포 전에 파이프라인 동작을 검증할 수 있다.

#### 인수 조건

1. THE Lambda_Handler SHALL AWS Lambda 이벤트 핸들러 시그니처(`handler(event, context)`)를 따른다
2. WHEN Lambda_Handler가 호출되면, THE Lambda_Handler SHALL Crawler, Markdown_Generator, Obsidian_Storage, Slack_Notifier를 순서대로 실행한다
3. THE Lambda_Handler SHALL `python -m` 명령어로 로컬에서 직접 실행 가능한 `__main__` 블록을 포함한다
4. WHEN 로컬에서 실행되면, THE Lambda_Handler SHALL `.env` 파일에서 환경 변수를 로드한다
5. IF Pipeline 실행 중 에러가 발생하면, THEN THE Lambda_Handler SHALL 에러를 로깅하고 실패 상태를 반환한다

### 요구사항 7: Lambda 배포 패키징

**사용자 스토리:** 개발자로서, Lambda 배포용 ZIP 패키지를 쉽게 생성하고 싶다. 이를 통해 수동 패키징 없이 빠르게 배포할 수 있다.

#### 인수 조건

1. THE Package_Script SHALL 소스 코드와 의존성을 포함한 Lambda 배포용 ZIP 파일을 생성한다
2. THE Package_Script SHALL `requirements.txt`에 명시된 의존성을 ZIP에 포함한다
3. THE Package_Script SHALL 불필요한 파일(`.env`, `__pycache__`, 테스트 파일)을 ZIP에서 제외한다
4. WHEN 패키징이 완료되면, THE Package_Script SHALL 생성된 ZIP 파일의 경로와 크기를 출력한다

### 요구사항 8: 스케줄링

**사용자 스토리:** 개발자로서, 파이프라인이 매일 오전 8시(KST)에 자동으로 실행되기를 원한다.

#### 인수 조건

1. THE Pipeline SHALL AWS EventBridge(CloudWatch Events) 스케줄 규칙을 통해 매일 KST 오전 8시(UTC 23:00 전일)에 트리거된다
2. THE Pipeline SHALL 스케줄 설정을 위한 cron 표현식을 문서 또는 IaC 코드에 명시한다
