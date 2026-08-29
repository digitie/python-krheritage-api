# WSL kor-travel-geo debug UI note

> **이름 변경 + 무관 안내**: 이 문서는 `python-kraddr-geo`/`kraddr_geo_api`/`pykraddr` 경로명으로
> 작성됐지만, 그 프로젝트는 `kor-travel-geo`(Python 패키지 `kortravelgeo`)로 리네임됐고
> SpatiaLite/SQLite 기반 구현도 PostgreSQL + PostGIS로 재구현됐습니다. 아래의 옛 경로·모듈명·명령은
> 더 이상 유효하지 않습니다. 이 저장소(`python-krheritage-api`)는 `kor-travel-geo`를 코드에서
> import하거나 의존하지 않으므로(국가유산청 API 래퍼로, 지오코딩과 무관) 이 노트를 정본으로 유지할
> 필요가 없습니다.
>
> `kor-travel-geo`의 로컬 디버그 UI를 WSL에서 띄우는 현재 방법이 필요하다면 그 저장소 자신의 문서
> (`docs/agent-guide.md` 등)를 확인하세요. 제공 표면은 그 저장소 README 기준으로 REST API
> `uvicorn kortravelgeo.api.app:app`, 관리 UI는 별도 Next.js 패키지 `kor-travel-geo-ui`입니다 —
> 정확한 포트/플래그는 그쪽 문서에서 확인해야 이 저장소가 다시 오래된 정보를 복제하지 않습니다.
