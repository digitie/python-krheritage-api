# python-krheritage-api

국가유산청, 국립문화유산연구원, 국립무형유산원, 공공데이터포털의 국가유산 관련
API와 파일데이터를 하나의 Python 인터페이스로 감싸는 TripMate용 라이브러리입니다.

PyPI 공개 배포는 현재 범위에서 제외합니다. 이 저장소는 GitHub 원격 저장소
`https://github.com/digitie/python-krheritage-api` 기준으로 관리합니다.

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

TripMate/python-krtour-map은 이 public client와 typed model을 직접 사용합니다. feature 변환은
provider wrapper/adapter가 아니라 `python-krtour-map`의 ETL 함수에서 수행합니다.

## Debug UI

Streamlit 기반 디버그 UI는 국가유산청 공개 XML 엔드포인트, GIS 응답, data.go.kr 커스텀
경로를 빠르게 호출하고 Raw Response, Parsed Payload, Pydantic Model, Processed Result,
Validation Errors, Debug Trace, Fixture / Testcase 탭으로 결과를 확인합니다.

```powershell
pip install -e ".[debug-ui]"
streamlit run tools/debug_streamlit.py
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
