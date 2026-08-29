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
- **동기 전용입니다.** `AsyncHeritageClient`는 자리표시자이며 생성 시 항상
  `NotImplementedError`를 던집니다 — 비동기 코드를 생성하지 마세요.
- feature 변환, 도메인 카테고리 매핑, ETL 로직은 이 라이브러리의 책임이 **아닙니다**. 그런
  관심사는 소비자 앱(`python-krtour-map`)에서 직접 구성합니다.

## 2. 핵심 퍼블릭 API 가이드

```python
from krheritage import HeritageClient, PROVIDER_NAME
from krheritage.codes import CityCode, HeritageType

with HeritageClient() as client:
    print(client.config.cache_dir)
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

- `AsyncHeritageClient`를 호출하는 코드를 생성하지 마세요 — 항상 예외가 발생합니다.
- 이 라이브러리의 반환 모델을 직접 변형해 도메인 특화 필드를 추가하지 마세요 — 변환은 소비자 앱
  쪽 ETL에서 수행합니다.
- `apis.data.go.kr`의 legacy/이동된 URL을 직접 하드코딩하지 마세요 — 라이브러리가
  `docs/anti_corruption.md`에 기록된 별칭 처리를 대신 수행합니다.
