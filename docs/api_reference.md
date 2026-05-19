# API Reference

## Public Constants

- `krheritage.PROVIDER_NAME`: `python-krheritage-api`
- `krheritage.__version__`: package version

## Configuration

`HeritageConfig.from_env()` resolves explicit arguments first, then environment
variables, then defaults.

## Public Services

`HeritageClient` exposes stable service attributes that downstream ETL can call
directly:

- `client.search.list(...)`: `SearchKindOpenapiList.do`
- `client.search.details(ccba_kdcd, ccba_asno, ccba_ctcd)`: `SearchKindOpenapiDt.do`
- `client.search.iter_all_details(...)`: paginated list scan followed by detail fetches
- `client.heritage.iter_all_details(...)`: detail-focused alias over the same public service
- `client.event.by_month(year=..., month=...)`: `selectEventListOpenapi.do`
- `client.event.iter_months(...)`: event scan for a fixed month or rolling range
- `client.gis.spca(...)`: GIS coordinate payload as `GeoFeatureCollection`

The services return `krheritage.models` instances. They do not create TripMate
features and do not wrap python-krtour-map.

## Codes

- `CityCode`
- `HeritageType`
- `HeritageDomain`
- `KoglLicense`
- `Lang`

## Models

- `HeritageKey`
- `HeritageSummary`
- `HeritageDetail`
- `HeritageEvent`
- `GeoFeature`
- `GeoFeatureCollection`
- `PaginatedResult`
