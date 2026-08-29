# kor-travel-map 통합

kor-travel-map(옛 이름 `python-krtour-map`)은 `krheritage` 객체를 직접 소비해야 한다. 국가유산 관련 동작이 부족하면 kor-travel-map 안에 provider wrapper를 만들지 말고 이 library의 public API를 안정화한다.

## Provider identity

모든 `source_type`, `provider`, `provider_sync_state` 참조에는 `python-krheritage-api`를 사용한다.

예시:

- `(python-krheritage-api, search_list)`
- `(python-krheritage-api, gis_3070426)`
- `(python-krheritage-api, 15145324)`

## 직접 model 사용 (Protocol 기반, import 없음)

이 provider 주변에 kor-travel-map 또는 자체 wrapper/adapter를 추가하지 않는다. `python-krheritage-api`가 안정 public client, typed model, pagination, raw payload 보존, provider exception을 소유한다.

kor-travel-map 쪽 변환 모듈(`kortravelmap.providers.krheritage`, ADR-006)은 이 패키지를
**import하지 않는다** — 대신 structural Protocol(`KrHeritageItem`/`KrHeritageEvent`)로
입력 shape만 의존한다. 이 저장소의 `krheritage.models.HeritageDetail`(`HeritageSummary`
상속)이 그 Protocol을 필드명 그대로(`key`, `name_ko`, `designated_at` 등) 만족하도록
맞춰져 있으므로, 필드명을 바꾸는 변경은 kor-travel-map 쪽 Protocol도 함께 깨뜨린다 —
`models/heritage.py`의 필드명을 바꾸기 전에 kor-travel-map의
`src/kortravelmap/providers/krheritage.py` docstring(ADR-044)을 확인할 것.

```python
from krheritage import HeritageClient

with HeritageClient() as client:
    detail = client.search.details("25", "0000001", "11")
    # detail은 krheritage.models.HeritageDetail이며, kor-travel-map은 이를
    # import 없이 구조적으로(duck typing) KrHeritageItem으로 소비한다.
    # 실제 변환 호출부는 kor-travel-map 저장소 자신의 ETL/파이프라인 코드를 확인할 것 —
    # 이 문서는 그 호출부의 정확한 함수명을 보증하지 않는다.
```

호출 순서(ETL 오케스트레이션, 정확한 클래스/모듈명은 kor-travel-map 쪽 문서가 정본)는 이
저장소 밖에서 `client.search.iter_all_details(...)`, `client.heritage.iter_all_details(...)`,
`client.event.iter_months(...)`를 직접 호출하는 형태를 따른다.
