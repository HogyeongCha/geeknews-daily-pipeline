---
inclusion: auto
---

# GeekNews (news.hada.io) 크롤링 가이드

이 문서는 GeekNews 최신글 페이지(`https://news.hada.io/new`)의 HTML 구조 분석 결과를 정리한 것입니다.
Spec 작성 및 구현 시 이 구조를 기준으로 파싱 로직을 설계하세요.

---

## 1. 페이지 특성

- 서버사이드 렌더링(SSR) 방식으로 JavaScript 실행 없이 HTML 파싱만으로 크롤링 가능
- jQuery 기반의 전통적인 웹 구조 (SPA 아님)
- 페이지당 약 20개 포스팅 표시
- 페이지네이션: `?page=2`, `?page=3` 쿼리 파라미터 방식

## 2. DOM 계층 구조

```
<html lang="KR">
└── <body>
    ├── <header> → <nav> (네비게이션)
    ├── <main>
    │   └── <article>
    │       └── div.topics              ← 포스팅 목록 컨테이너
    │           ├── div.topic_row       ← 포스팅 1개 (반복)
    │           └── div.next.commentTD  ← 페이지네이션 ("토픽 더 불러오기")
    └── <footer>
```

## 3. 포스팅 1개(div.topic_row) 내부 구조

```html
<div class="topic_row">
  <div class="votenum">{순번}</div>
  <div class="vote">
    <span id="vote{TOPIC_ID}">
      <a class="upvote" href='javascript:vote({TOPIC_ID}, "up");'>▲</a>
    </span>
  </div>
  <div class="topictitle">
    <a href="{원본_URL}" rel="nofollow" id="tr{순번}">
      <h1>{기사 제목}</h1>
    </a>
    <span class="topicurl">({출처_도메인})</span>
  </div>
  <!-- ⚠️ topicdesc는 요약이 없는 글에서 생략될 수 있음 -->
  <div class="topicdesc">
    <a href="topic?id={TOPIC_ID}" class="c99 breakall">{요약 텍스트}</a>
  </div>
  <div class="topicinfo">
    <span id="tp{TOPIC_ID}">{포인트수}</span> point(s) by
    <a href="/user?id={작성자}">{작성자}</a> {시간}전
    <span id="unvote{TOPIC_ID}"></span> |
    <a href="topic?id={TOPIC_ID}&go=comments" class="u">{댓글 N개 | 댓글과 토론}</a>
  </div>
</div>
```

## 4. CSS 셀렉터 맵

| 데이터 | 셀렉터 | 추출 방식 |
|--------|--------|-----------|
| 포스팅 목록 | `div.topics > div.topic_row` | 전체 반복 |
| 순번 | `div.votenum` | `.text` |
| 제목 | `div.topictitle h1` | `.text` |
| 원본 링크 | `div.topictitle > a[rel=nofollow]` | `["href"]` |
| 출처 도메인 | `span.topicurl` | `.text.strip("()")` |
| 요약 | `div.topicdesc a` | `.text` (None 가능) |
| 토픽 ID | `div.topicinfo span[id^=tp]` | `id` 속성에서 숫자 추출 |
| 포인트 | `div.topicinfo span[id^=tp]` | `.text` → int |
| 작성자 | `div.topicinfo a[href^='/user']` | `.text` |
| 댓글 링크 | `div.topicinfo a.u` | `["href"]` |
| 다음 페이지 | `div.next a` | `["href"]` (없으면 마지막 페이지) |

## 5. 파싱 결과 JSON 스키마

```json
{
  "source": "https://news.hada.io/new",
  "crawled_at": "ISO8601 timestamp",
  "page": 1,
  "items": [
    {
      "rank": 1,
      "topic_id": 27843,
      "title": "string",
      "original_url": "string",
      "source_domain": "string",
      "discussion_url": "https://news.hada.io/topic?id={topic_id}",
      "summary": "string | null",
      "points": 1,
      "author": "string",
      "author_url": "https://news.hada.io/user?id={author}",
      "time_ago": "2시간전",
      "comments_text": "댓글과 토론 | 댓글 N개",
      "comments_count": "number | null"
    }
  ],
  "next_page_url": "string | null"
}
```

## 6. 예외처리 필수 항목

| 항목 | 상세 | 대응 |
|------|------|------|
| `topicdesc` 누락 | 요약 없는 글은 `div.topicdesc` 자체가 없음 | `None` 체크 필수 |
| 댓글 수 패턴 | "댓글과 토론" vs "댓글 N개" 두 가지 | 정규식 `댓글 (\d+)개`로 추출, 실패 시 `null` |
| HTML 엔티티 | 요약에 `&quot;` 등 포함 | `html.unescape()` 처리 |
| 상대 시간 | "N시간전", "N일전" 등 절대 시간 없음 | 크롤링 시점 기준 변환 필요 |
| 마크다운 in 요약 | `##`, `-`, `*` 등 마크다운 문법 포함 | 플레인텍스트 변환 고려 |
| Rate Limiting | 과도한 요청 시 차단 가능 | 딜레이 + User-Agent 설정 + robots.txt 준수 |
| 로그인 상태 차이 | 로그인 시 vote 영역 구조 변경 가능 | 비로그인 상태로 크롤링 권장 |
| 페이지네이션 종료 | 마지막 페이지에는 `div.next` 없음 | 다음 페이지 링크 존재 여부로 판단 |

## 7. 구현 시 참고사항

- HTTP 요청만으로 충분 (Playwright/Selenium 불필요)
- Python: `requests` + `BeautifulSoup4` 조합 권장
- Node.js: `axios` + `cheerio` 조합 권장
- 상대 URL(`topic?id=...`, `/user?id=...`)은 base URL `https://news.hada.io/`와 결합 필요
- 원본 링크(`a[rel=nofollow]`)는 절대 URL로 제공됨
