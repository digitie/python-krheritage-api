# 변경 기록

이 프로젝트의 주요 변경 사항을 기록한다.

## [0.1.0] - Unreleased

### 수정

- live `SearchKindOpenapiDt.do` 응답이 복합키(`ccbaKdcd`/`ccbaAsno`/`ccbaCtcd`)와 `longitude`/`latitude`를 `<result>` 레벨에만 두고 본문을 `<item>`에 중첩해, `details()`/`iter_all_details()`가 유효한 key로도 `HeritageDetail` ValidationError로 전량 실패하던 문제 수정 — result 레벨 leaf 필드를 item 필드와 병합한다 (#5).
- `HeritageKey` 구성요소를 `str | None`으로 완화해 live 목록의 결측 key row가 page 전체 파싱을 깨지 않게 하고, `iter_all_details()`는 결측 key row를 식별 정보가 담긴 warning 로그와 함께 skip한다 (#5).
- `HeritageDetail`은 복합키 완전성을 검증해 식별자 없는 detail payload를 fail-loud로 거른다. `HeritageSummary` 좌표는 빈 문자열을 `None`으로 정규화한다 (#5).

### 추가

- `python-krheritage-api` project 구조 초기화.
- Provider constant, config loading, common code, domain exception을 포함한 공개 `krheritage` package 추가.
- Test 전용 GitHub Actions workflow 추가. PyPI publishing은 현재 project 결정에 따라 의도적으로 제외한다.
