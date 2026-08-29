---
name: python-krheritage-api
description: 국가유산청/국립문화유산연구원/국립무형유산원/공공데이터포털 국가유산 API를 감싸는 python-krheritage-api를 구현, 확장, test, troubleshooting할 때 사용한다.
---

# SKILL — python-krheritage-api 에이전트 매뉴얼

> 이 파일은 당신(AI 에이전트)이 작업을 시작하기 전 반드시 읽어야 한다.
> 1회만 읽으면 30분 이상의 디버깅을 줄일 수 있다.

## 1. 정체성

이 프로젝트(GitHub 이름 `python-krheritage-api`, import 패키지 이름 `krheritage`)는 국가유산청,
국립문화유산연구원, 국립무형유산원, 공공데이터포털이 제공하는 국가유산 관련 API와 파일데이터를
TripMate에서 소비할 수 있는 하나의 Python 인터페이스로 감싸는 **OpenAPI 클라이언트 라이브러리**다.

`HeritageClient`가 목록(`search.list`)/상세(`search.details`)/행사(`event.by_month`)/GIS(`gis.spca`)
조회를 제공한다. `AsyncHeritageClient`는 아직 자리표시자이며 생성 시 항상
`NotImplementedError`를 던진다 — 비동기 서비스 레이어가 실제로 구현되기 전까지는 사용할 수 없다.

feature 변환/도메인 매핑 로직은 이 저장소의 책임이 아니다(`python-krtour-map`의 ETL 함수가 담당).

### 식별자 매핑

| 항목 | 값 |
|------|----|
| GitHub 저장소 | `python-krheritage-api` |
| import | `import krheritage` / `from krheritage import HeritageClient` |
| 인증 환경변수 | `DATA_GO_KR_SERVICE_KEY` |
| 패키지 전용 설정 환경변수 | `KHERITAGE_CACHE_DIR`, `KHERITAGE_MAX_RPS` |
| PyPI 배포 | 현재 범위 제외 (`docs/index.md`) |

## 2. 빠른 시작

```bash
cd F:\dev\python-krheritage-api
python -m pytest
python -m ruff check .
python -m mypy src/krheritage
```

실제 API 호출을 통한 검증을 진행할 경우:
```powershell
$env:DATA_GO_KR_SERVICE_KEY="..."
python -m pytest -m live -vv
```

에이전트 작업은 고정 worktree에서 진행한다. ChatGPT Codex는 `F:\dev\python-krheritage-api-codex`,
Claude Code는 `F:\dev\python-krheritage-api-claude`, Google Antigravity는
`F:\dev\python-krheritage-api-antigravity`를 사용한다.

## 3. 디렉토리 지도

```
src/krheritage/
  client.py       — HeritageClient(sync)/AsyncHeritageClient(placeholder) 진입점
  config.py       — DATA_GO_KR_SERVICE_KEY, KHERITAGE_CACHE_DIR, KHERITAGE_MAX_RPS 로딩
  services/       — search/event/gis/heritage/intangible/legacy/media/research 서비스 클래스
  models/         — 공개 Pydantic 반환 모델
  codes/          — area/district/domain/heritage_type/lang/license 코드 테이블
  transport/      — HTTP transport, anti-corruption 별칭 처리(`_aliases`)
  exceptions.py   — 공통 예외 및 오류 envelope 매핑
  catalog.py      — 구현 API 카탈로그
  sync/, files/, ai/, integrations/, schemas/ — 부가 기능 모듈
tests/
  unit/, property/, integration/, krtour_compat/, fixtures/
docs/
  index.md               — 프로젝트 개요, scope
  api_reference.md        — 구현된 API의 path/파라미터 상세
  data_dictionary.md      — 응답 필드 사전
  anti_corruption.md      — 알려진 endpoint 이동/별칭
  integration_krtour_map.md — python-krtour-map(kor-travel-map) 연동 방식
  quickstart.md           — 사용 예제
```

## 4. 절대 하지 말 것 (DO NOT)

1. **`AsyncHeritageClient`를 사용 가능한 것처럼 문서화 금지**: 현재는 항상 `NotImplementedError`를
   던지는 자리표시자다.
2. **API 오류 envelope을 빈 결과로 조용히 처리 금지**: HTTP 200으로 감싸진 국가유산청 오류 응답은
   `ApiErrorResponse`로 명시적으로 raise해야 한다.
3. **`docs/anti_corruption.md`에 기록된 legacy URL을 별도 처리 없이 직접 호출 금지**: `transport._aliases`의
   별칭 처리를 거쳐야 한다.
4. **feature 변환/도메인 매핑 로직을 이 저장소에 추가 금지**: 그 책임은 `python-krtour-map`(kor-travel-map)의
   ETL 함수에 있다.
5. **서비스키를 예외 메시지·로그에 평문으로 노출 금지**: `apis.data.go.kr` 호스트 검사는 정확한 host
   매칭이어야 하며 부분 문자열 매칭을 쓰지 않는다.
6. **응답을 무제한으로 메모리에 버퍼링 금지**: 스트리밍 + 크기 상한을 유지한다.
7. **API Key 평문 커밋 금지**: `.env`/`.env.local`은 Git에서 제외한다.

## 5. 자주 묻는 작업

| 작업 | 시작 파일 |
|------|-----------|
| 새 API endpoint 추가 | `src/krheritage/services/`에 서비스 메서드 추가 → `src/krheritage/models/`에 반환 모델 정의 → `src/krheritage/catalog.py`에 등록 |
| 오류 envelope 처리 추가 | `src/krheritage/exceptions.py`의 기존 타입 계층을 따를 것 |
| legacy URL 별칭 추가 | `src/krheritage/transport/_aliases`와 `docs/anti_corruption.md` 동시 갱신 |
| 코드 테이블 추가/수정 | `src/krheritage/codes/`, 공식 출처 확인 후 반영 |
