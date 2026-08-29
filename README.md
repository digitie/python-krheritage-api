# python-krheritage-api

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![MIT 라이선스](https://img.shields.io/badge/License-MIT-blue.svg)
![Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)

국가유산청, 국립문화유산연구원, 국립무형유산원, 공공데이터포털의 국가유산 관련
API와 파일데이터를 하나의 Python 인터페이스로 감싸는 TripMate용 라이브러리입니다.

PyPI 공개 배포는 현재 범위에서 제외합니다. 이 저장소는 GitHub 원격 저장소
`https://github.com/digitie/python-krheritage-api` 기준으로 관리합니다.

## 먼저 읽을 문서

README는 입구 역할만 합니다. 세부 절차와 결정은 아래 문서를 정본으로 봅니다.

| 필요 정보 | 문서 |
|-----------|------|
| 프로젝트 개요, scope | [`docs/index.md`](docs/index.md) |
| API 상세(path/파라미터) | [`docs/api_reference.md`](docs/api_reference.md) |
| 응답 필드 사전 | [`docs/data_dictionary.md`](docs/data_dictionary.md) |
| 알려진 endpoint 이동/별칭 | [`docs/anti_corruption.md`](docs/anti_corruption.md) |
| `kor-travel-map`(구 `python-krtour-map`) 연동 방식 | [`docs/integration_kor_travel_map.md`](docs/integration_kor_travel_map.md) |
| 사용 예제 | [`docs/quickstart.md`](docs/quickstart.md) |
| 설계 결정 | [`docs/decisions.md`](docs/decisions.md) |
| 변경 이력 | [`CHANGELOG.md`](CHANGELOG.md) |

## Quick Start

```python
from krheritage import HeritageClient, PROVIDER_NAME
from krheritage.codes import CityCode, HeritageType

print(PROVIDER_NAME)  # python-krheritage-api

with HeritageClient() as client:
    print(client.config.cache_dir)
    print(CityCode.SEOUL.korean, HeritageType.NATIONAL_TREASURE.korean)
```

현재 제공하는 public service 표면은 아래와 같습니다.

- `client.search.list(...)`: `SearchKindOpenapiList.do` 목록 조회
- `client.search.details(ccba_kdcd, ccba_asno, ccba_ctcd)`: `SearchKindOpenapiDt.do` 상세 조회
- `client.search.iter_all_details(...)` / `client.heritage.iter_all_details(...)`: 목록 페이지를 순회하며 상세 모델을 산출
- `client.event.by_month(year=..., month=...)` / `client.event.iter_months(...)`: 국가유산 행사 월별 순회
- `client.gis.spca(...)`: GIS 위치정보를 `GeoFeatureCollection`으로 반환

TripMate/`kor-travel-map`(구 `python-krtour-map`)은 이 public client와 typed model을 직접
사용합니다. feature 변환은 provider wrapper/adapter가 아니라 `kor-travel-map`의 ETL 함수에서
수행합니다.

## Debug UI

Streamlit 기반 디버그 UI는 국가유산청 공개 XML 엔드포인트, GIS 응답, data.go.kr 커스텀
경로를 빠르게 호출하고 Raw Response, Pydantic Model, Processed Result,
Validation Errors, Debug Trace, Fixture / Testcase 탭으로 결과를 확인합니다. 요청 파라미터
폼은 `krheritage.catalog`의 `required_params`/`optional_params` 메타데이터에서 자동
생성되며, 실제 호출은 `HeritageClient.debug_fetch()` 하나로 라우팅됩니다.

```powershell
pip install -e ".[debug-ui]"
streamlit run examples/streamlit_debug_ui.py
```

인증키가 필요한 data.go.kr 엔드포인트는 `DATA_GO_KR_SERVICE_KEY`
또는 수동 입력을 사용할 수 있습니다. `.env`와 `.env.local`은 Git에서
제외됩니다.

## English

`python-krheritage-api` is a TripMate-oriented Python wrapper for Korea Heritage
Administration open data APIs and file datasets. The import module is
`krheritage`; the provider/source identifier is `python-krheritage-api`.

This project is not configured for PyPI publishing. Install it directly from the
repository or as an editable local package during development.

## 법적 고지

이 저장소의 라이선스(MIT, [`LICENSE`](LICENSE))는 이 저장소의 코드에만 적용됩니다.
국가유산청, 국립문화유산연구원, 국립무형유산원, 공공데이터포털이 제공하는 상위
데이터/API의 이용은 각 제공기관의 이용약관과 재배포 조건을 따라야 하며, 이 저장소가
그 준수를 보장하지 않습니다.
