# 변경 기록

이 프로젝트의 주요 변경 사항을 기록한다.

## [0.1.0] - Unreleased

### 수정

- 4인 전문 리뷰어 서브에이전트의 적대적 코드 리뷰로 발견·검증된 버그 수정: API 오류 envelope(잘못된
  서비스키, 파라미터 오류, 업스트림 오류를 HTTP 200으로 감싼 경우)가 예외 없이 빈 결과로 조용히
  둔갑하던 문제(`gis.spca()`를 bbox 없이 호출하면 실제로는 서버 오류인데 "경계 안에 유산이 없음"과
  구분 불가능했음) — 알려진 오류 envelope 형태를 감지해 `ApiErrorResponse`를 발생시키도록 수정,
  `domain_for_type()`이 `HeritageType.UNDESIGNATED`/`NO_DESIGNATION`에 대해 처리되지 않은
  `KeyError`를 던지던 문제, `gis_source_identity()`가 프로세스마다 값이 달라지는 Python 내장
  `hash()`로 source_id를 만들어 재실행마다 안정적이지 않던 문제(SHA-256 기반으로 교체),
  `_with_service_key()`의 호스트 검사가 부분 문자열 매칭이라 `apis.data.go.kr`를 포함하는 악성
  호스트에도 서비스키가 전송될 수 있던 문제, HTTP 오류 메시지에 `serviceKey` 쿼리파라미터가 그대로
  노출되던 문제, 응답 크기 제한 없이 전체를 메모리에 버퍼링하던 문제(스트리밍 + 50MB 캡 추가), 실제
  존재하지 않거나 검증되지 않은 `python-krtour-map` 선택적 의존성 제거 등. GitHub Actions CI
  (`lint`/`typecheck`/`test`)는 기존 `test.yml`이 이미 커버하고 있어 별도 추가하지 않음.
- live `SearchKindOpenapiDt.do` 응답이 복합키(`ccbaKdcd`/`ccbaAsno`/`ccbaCtcd`)와 `longitude`/`latitude`를 `<result>` 레벨에만 두고 본문을 `<item>`에 중첩해, `details()`/`iter_all_details()`가 유효한 key로도 `HeritageDetail` ValidationError로 전량 실패하던 문제 수정 — result 레벨 leaf 필드를 item 필드와 병합한다 (#5).
- `HeritageKey` 구성요소를 `str | None`으로 완화해 live 목록의 결측 key row가 page 전체 파싱을 깨지 않게 하고, `iter_all_details()`는 결측 key row를 식별 정보가 담긴 warning 로그와 함께 skip한다 (#5).
- `HeritageDetail`은 복합키 완전성을 검증해 식별자 없는 detail payload를 fail-loud로 거른다. `HeritageSummary` 좌표는 빈 문자열을 `None`으로 정규화한다 (#5).

### 추가

- `python-krheritage-api` project 구조 초기화.
- Provider constant, config loading, common code, domain exception을 포함한 공개 `krheritage` package 추가.
- Test 전용 GitHub Actions workflow 추가. PyPI publishing은 현재 project 결정에 따라 의도적으로 제외한다.
