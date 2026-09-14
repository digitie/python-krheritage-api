# AI 에이전트 가이드: python-krheritage-api (krheritage)

이 라이브러리(`krheritage`)를 임포트하여 사용하는 소비자 앱(예: `python-krtour-map`/`kor-travel-map`,
TripMate)의 코드를 생성하는 AI 코딩 어시스턴트(Cursor, Copilot, ChatGPT, Claude Code 등)를 위한
컨텍스트 문서입니다.

> **본 저장소(`python-krheritage-api`) 자체를 수정하려는 에이전트는 다른 문서를 봅니다**:
> [`AGENTS.md`](./AGENTS.md)가 진입점, 한글 매뉴얼은 [`SKILL.md`](./SKILL.md), 설계 결정은
> [`docs/index.md`](./docs/index.md)와 [`docs/anti_corruption.md`](./docs/anti_corruption.md)에
> 있습니다. 이 문서는 **소비자 앱**(이 라이브러리를 import해서 쓰는 애플리케이션)을 작성하는
> AI 가이드입니다.

## 1. 이 라이브러리는 무엇인가

- 국가유산청, 국립문화유산연구원, 국립무형유산원, 공공데이터포털이 제공하는 국가유산 관련
  API/파일데이터를 하나의 Python 인터페이스로 감싸는 **TripMate 전용 클라이언트 라이브러리**입니다.
- import 패키지 이름은 `krheritage`입니다. PyPI 공개 배포는 현재 범위에서 제외되어 있으므로,
  GitHub 저장소(`https://github.com/digitie/python-krheritage-api`)를 직접 의존성으로 잡습니다.
- **비동기 전용입니다.** HeritageClient의 네트워크 메서드에 await를 사용하세요.
- feature 변환, 도메인 카테고리 매핑, ETL 로직은 이 라이브러리의 책임이 **아닙니다**. 그런
  관심사는 소비자 앱(`python-krtour-map`)에서 직접 구성합니다.

## 2. 핵심 퍼블릭 API 가이드

```python
import asyncio
from krheritage import HeritageClient, PROVIDER_NAME
from krheritage.codes import CityCode, HeritageType


async def main() -> None:
    async with HeritageClient() as client:
        print(client.config.cache_dir)


asyncio.run(main())
```

- `client.search.list(...)`: `SearchKindOpenapiList.do` 목록 조회
- `client.search.details(ccba_kdcd, ccba_asno, ccba_ctcd)`: `SearchKindOpenapiDt.do` 상세 조회
  (복합키 3요소가 모두 필요합니다)
- `client.search.iter_all_details(...)` / `client.heritage.iter_all_details(...)`: 목록 페이지를
  순회하며 상세 모델을 산출
- `client.event.by_month(year=..., month=...)` / `client.event.iter_months(...)`: 국가유산 행사
  월별 순회
- `client.gis.spca(...)`: GIS 위치정보를 `GeoFeatureCollection`으로 반환

## 3. 인증과 설정

- API 인증키는 `DATA_GO_KR_SERVICE_KEY` 환경변수(다른 data.go.kr 계열 형제 라이브러리와 공유하는
  키)를 사용합니다.
- `KHERITAGE_CACHE_DIR`/`KHERITAGE_MAX_RPS`는 인증키가 아니라 로컬 캐시 경로/요청 속도 제한
  설정입니다.

## 4. 소비자 앱이 하지 말아야 할 것

- 제거된 AsyncHeritageClient 대신 HeritageClient와 async with를 사용하세요.
- 이 라이브러리의 반환 모델을 직접 변형해 도메인 특화 필드를 추가하지 마세요 — 변환은 소비자 앱
  쪽 ETL에서 수행합니다.
- `apis.data.go.kr`의 legacy/이동된 URL을 직접 하드코딩하지 마세요 — 라이브러리가
  `docs/anti_corruption.md`에 기록된 별칭 처리를 대신 수행합니다.


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
