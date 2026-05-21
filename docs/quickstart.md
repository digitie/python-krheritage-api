# 빠른 시작

개발 중에는 repository 또는 local checkout에서 editable install을 사용한다.

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

환경 변수:

- `DATA_GO_KR_SERVICE_KEY`
- `KHERITAGE_CACHE_DIR`
- `KHERITAGE_MAX_RPS`
