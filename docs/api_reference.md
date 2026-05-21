# API reference

## 공개 constant

- `krheritage.PROVIDER_NAME`: `python-krheritage-api`
- `krheritage.__version__`: package version

## 설정

`HeritageConfig.from_env()`는 명시 인자, 환경 변수, 기본값 순서로 설정을 결정한다.

## 공개 service

`HeritageClient`는 downstream ETL이 직접 호출할 수 있는 안정 service attribute를 제공한다.

- `client.search.list(...)`: `SearchKindOpenapiList.do`
- `client.search.details(ccba_kdcd, ccba_asno, ccba_ctcd)`: `SearchKindOpenapiDt.do`
- `client.search.iter_all_details(...)`: paginated list scan 후 detail fetch
- `client.heritage.iter_all_details(...)`: 같은 public service 위의 detail-focused alias
- `client.event.by_month(year=..., month=...)`: `selectEventListOpenapi.do`
- `client.event.iter_months(...)`: 고정 월 또는 rolling range event scan
- `client.gis.spca(...)`: `GeoFeatureCollection` 형태의 GIS coordinate payload

Service는 `krheritage.models` instance를 반환한다. TripMate feature를 직접 만들지 않고 `python-krtour-map`을 감싸지도 않는다.

## Code

- `CityCode`
- `HeritageType`
- `HeritageDomain`
- `KoglLicense`
- `Lang`

## Model

- `HeritageKey`
- `HeritageSummary`
- `HeritageDetail`
- `HeritageEvent`
- `GeoFeature`
- `GeoFeatureCollection`
- `PaginatedResult`
