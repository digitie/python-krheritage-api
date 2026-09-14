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
조회를 native async로 제공한다. 각 호출은 await, 순회는 async for를 사용한다.

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
$env:KHERITAGE_RUN_LIVE="1"
python -m pytest -m live -vv
```

에이전트 작업은 고정 worktree에서 진행한다. ChatGPT Codex는 `F:\dev\python-krheritage-api-codex`,
Claude Code는 `F:\dev\python-krheritage-api-claude`, Google Antigravity는
`F:\dev\python-krheritage-api-antigravity`를 사용한다.

## 3. 디렉토리 지도

```
src/krheritage/
  client.py       — HeritageClient(native async) 진입점
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
  integration_kor_travel_map.md — kor-travel-map(구 python-krtour-map) 연동 방식
  quickstart.md           — 사용 예제
```

## 4. 절대 하지 말 것 (DO NOT)

1. **동기 HTTP와 Async 접두사 별칭을 다시 추가하지 말 것**: HeritageClient 하나로 native async를 제공한다.
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


## 비동기 호출과 TPS

HeritageClient의 네트워크 메서드는 await, 페이지·상세·월별 반복은 async for,
종료는 async with 또는 await client.aclose()를 사용한다. 동기 HTTP와
AsyncHeritageClient 자리표시자·aio 팩터리는 제거했다. 코드표·파싱·메타데이터는
일반 함수로 유지한다. 기존 서비스 인자와 반환 모델은 동일하다.

max_rps는 기본 5이며 KHERITAGE_MAX_RPS 환경변수로 설정할 수 있다.
AsyncTokenBucket을 rate_limiter에 주입하면 클라이언트 여러 개의 요청 예산을
합산하고 max_rps보다 우선한다. 버킷의 기본 capacity는 max(1, max_rps)이며
초기에 가득 차 있으므로 burst를 허용한다. 일정한 송신 간격이 필요하면 capacity=1을
사용한다. 모든 서비스·debug·페이지, 각 재시도와 리다이렉트마다 토큰을 소비한다.
대기 취소는 토큰을 쓰지 않는다. 버킷은 한 이벤트 루프에서만 사용한다.

내부 생성 HTTPX 세션은 문맥 종료 시 닫는다. session으로 주입한 AsyncClient는
호출자가 닫는다. 본문 스트리밍 중 취소·50MB 상한 오류에도 응답을 닫는다.
HTTP 429와 5xx 및 전송 오류는 재시도하며 나머지 HTTP 4xx는 즉시 반환한다.
사용자 정의 인증·transport 내부의 추가 요청은 라이브러리 밖의 동작이다.
files.write_bytes의 파일 쓰기는 작업 스레드에서 실행한다. 취소는 이미 시작한
디스크 쓰기를 되돌리지 않는다.

```python
import asyncio
from krheritage import AsyncTokenBucket, HeritageClient


async def main() -> None:
    bucket = AsyncTokenBucket(2, capacity=1)
    async with HeritageClient(rate_limiter=bucket) as client:
        page = await client.search.list(page_size=1)
        print(page.items)
        async for detail in client.heritage.iter_all_details(page_size=1, max_pages=1):
            print(detail.name_ko)


asyncio.run(main())
```
