# 변경 기록

이 프로젝트의 주요 변경 사항을 기록한다.

## [0.1.1] - 2026-10-22

### 수정

- `HeritageEvent`를 live `selectEventListOpenapi.do` 응답 형태에 맞췄다. 기존 alias(`sn`/`startDate`/`endDate`/`siteName`/`telName`/`mainImage`)는 실제 응답에 없는 이름이라 운영에서 `sn`·기간·장소·주소·연락처가 전부 `None`이었다(kor-travel-map에서 5,306/5,306 행사 row 탈락). 새 매핑: `seqNo`→`sn`, `siteCode`→`site_code`, `subContent`→`contents`, `sDate`/`eDate`(`YYYYMMDD`)→`starts_on`/`ends_on`, `groupName`→`group_name`, `contact`→`tel_name`, `subDesc`→`place`, `subPath`→`url`, `subDesc_2`→`target_audience`, `subDesc_3`→`fee`, `mainImageTemp`→`main_image`, `subDate`→`schedule_text`, `sido`/`gugun` 신규. `address`는 `"{sido} {gugun}"` best-effort 파생. 응답에 좌표가 없어 `longitude`/`latitude`는 `None`.
- 숫자로 온 문자열 필드·날짜(JSON 응답 대비)를 받고, 빈 CDATA 값은 `None`, 달력상 불가능한 날짜는 row 하나로 월 전체가 깨지지 않도록 `None`(원문은 `raw`).

### 추가

- `HeritageEvent.occurrence_key`(`{sn}::{starts_on}::{ends_on}`): live `seqNo`는 프로그램 식별자라 회차마다 반복된다(2026-10 실측 2,006 row 중 1,378 row가 중복 `seqNo`; 조합 키는 그 실측에서 유일).
- live 응답 원문 fixture `tests/fixtures/event_list_2026_10.xml`.

### 변경 — async-only와 TPS (#11)

HeritageClient의 서비스·페이지·디버그를 native async로 전환했다. AsyncTokenBucket을 공개하고 max_rps/rate_limiter로 요청·재시도·리다이렉트의 TPS를 제어한다. 동기 클라이언트와 비동기 자리표시자·aio를 제거했다. HTTP 상태를 보존한 재시도 판별, 스트림 취소 정리, 사용자 주입 세션 수명을 검증했다.

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
