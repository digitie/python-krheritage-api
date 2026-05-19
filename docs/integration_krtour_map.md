# TripMate Integration

TripMate should consume `krheritage` objects directly. Do not add a provider
wrapper inside TripMate for missing heritage behavior; stabilize missing behavior
in this library's public API instead.

## Provider Identity

Use `python-krheritage-api` for all `source_type`, `provider`, and
`provider_sync_state` references.

Examples:

- `(python-krheritage-api, search_list)`
- `(python-krheritage-api, gis_3070426)`
- `(python-krheritage-api, 15145324)`

## Direct Model Usage

Do not add a TripMate or python-krtour-map wrapper/adapter around this provider.
`python-krheritage-api` owns stable public clients, typed models, pagination, raw
payload preservation, and provider exceptions. `python-krtour-map` consumes those
models directly and converts them into `Feature`, `SourceRecord`, `SourceLink`,
`PlaceDetail`, `AreaDetail`, `EventDetail`, and RustFS file metadata.

```python
from krheritage import HeritageClient
from krtour_map.heritage import krheritage_heritage_item_to_feature_bundle

with HeritageClient() as client:
    detail = client.search.details("25", "0000001", "11")
    bundle = krheritage_heritage_item_to_feature_bundle(detail)
```

For scheduled ETL, TripMate should pass the `HeritageClient` instance as a
Dagster resource to `python-krtour-map`. The ETL body calls
`client.search.iter_all_details(...)`, `client.heritage.iter_all_details(...)`,
or `client.event.iter_months(...)` directly depending on the dataset key.
