# TripMate 통합

TripMate는 `krheritage` 객체를 직접 소비해야 한다. 국가유산 관련 동작이 부족하면 TripMate 안에 provider wrapper를 만들지 말고 이 library의 public API를 안정화한다.

## Provider identity

모든 `source_type`, `provider`, `provider_sync_state` 참조에는 `python-krheritage-api`를 사용한다.

예시:

- `(python-krheritage-api, search_list)`
- `(python-krheritage-api, gis_3070426)`
- `(python-krheritage-api, 15145324)`

## 직접 model 사용

이 provider 주변에 TripMate 또는 `python-krtour-map` wrapper/adapter를 추가하지 않는다. `python-krheritage-api`가 안정 public client, typed model, pagination, raw payload 보존, provider exception을 소유한다. `python-krtour-map`은 이 model을 직접 소비해 `Feature`, `SourceRecord`, `SourceLink`, `PlaceDetail`, `AreaDetail`, `EventDetail`, RustFS file metadata로 변환한다.

```python
from krheritage import HeritageClient
from krtour_map.heritage import krheritage_heritage_item_to_feature_bundle

with HeritageClient() as client:
    detail = client.search.details("25", "0000001", "11")
    bundle = krheritage_heritage_item_to_feature_bundle(detail)
```

Scheduled ETL에서는 TripMate가 `HeritageClient` instance를 Dagster resource로 `python-krtour-map`에 전달한다. ETL body는 dataset key에 따라 `client.search.iter_all_details(...)`, `client.heritage.iter_all_details(...)`, `client.event.iter_months(...)`를 직접 호출한다.
