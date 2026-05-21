# Quickstart

Install from the repository or local checkout during development.

```bash
python -m pip install -e ".[dev]"
```

```python
from krheritage import HeritageClient, PROVIDER_NAME
from krheritage.codes import CityCode, HeritageType

with HeritageClient(max_rps=5) as client:
    print(PROVIDER_NAME)
    print(client.config.cache_dir)
    print(CityCode.CHUNGBUK.value, CityCode.CHUNGBUK.korean)
    print(HeritageType.NATIONAL_TREASURE.korean)
```

Environment variables:

- `DATA_GO_KR_SERVICE_KEY`
- `KHERITAGE_CACHE_DIR`
- `KHERITAGE_MAX_RPS`

