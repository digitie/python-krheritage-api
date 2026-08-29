# AGENTS.md

## 목표

`python-krheritage-api`(Python import 모듈 `krheritage`)는 국가유산청, 국립문화유산연구원,
국립무형유산원, 공공데이터포털이 제공하는 국가유산 관련 API와 파일데이터를 하나의 Python
인터페이스로 감싸는 TripMate용 라이브러리다. `HeritageClient`가 목록/상세/행사/GIS 조회를
제공하며, `python-krtour-map`은 이 public client와 typed model을 직접 소비한다.

## Think Before Coding

- 변경을 시작하기 전 `client.py`/`services/`/`transport/`의 관련 서비스 클래스를 먼저 읽을 것
- 새 endpoint를 추가하기 전 `docs/api_reference.md`와 `docs/anti_corruption.md`에 이미 기록된
  URL 이동/별칭이 있는지 확인할 것
- 응답 파싱 변경 전 `tests/fixtures/`의 실제 캡처 응답으로 가정을 검증할 것

## Simplicity First

- 요청을 완전히 해결하는 최소한의 코드만 작성할 것
- 요청되지 않은 기능을 추가하지 말 것
- 일회성 용도를 위해 추상화를 만들지 말 것
- 구체적인 필요 없이 설정 가능성이나 유연성을 늘리지 말 것
- 구현이 문제에 비해 커졌다고 느껴지면 줄일 것

## Surgical Changes

- 버그 수정은 원인이 되는 코드만 건드리고 주변 리팩터링을 곁들이지 말 것
- 기존 서비스 클래스(`search`/`event`/`gis`)의 공개 시그니처를 임의로 바꾸지 말 것
- `AsyncHeritageClient`가 왜 `NotImplementedError`만 던지는지 이해하지 못한 채 비동기 지원을
  "완성"시키려 하지 말 것 — 실제 확장은 별도 설계 결정이 필요하다

## Goal-Driven Execution

- 실제 사용자 요청(또는 이슈)이 요구하는 것만 구현할 것
- 국가유산청 오류 envelope(HTTP 200 + 오류 코드)을 새로 다룰 때는 `exceptions.py`의 기존
  타입 계층을 따를 것, 새 예외 타입을 즉흥적으로 추가하지 말 것
- 검증되지 않은 가정을 문서에 기록하지 말 것 — 실제 API 응답으로 확인한 것만 기록할 것

## Practical Bias

- 동작하는 최소 구현을 우선하고, 완벽한 일반화를 좇지 말 것
- provider가 원문에서 쓰는 필드명/코드값은 번역하지 말고 그대로 유지할 것
- 로컬에서 재현 가능한 테스트(fixture 기반)를 실전 API 호출보다 우선할 것

## 문서 언어 정책

이 저장소의 모든 Markdown 문서는 한글로 작성한다. 예외 없음.

다음 항목만 영어를 유지한다 — 한글로 옮기면 의미가 변하거나 정확성이 깨지기 때문:

- **코드 식별자**: 클래스/함수/모듈 이름(`HeritageClient`, `SearchKindOpenapiList.do`)
- **명령어와 경로**: `pytest`, `ruff check .`, `src/krheritage/client.py`
- **API 필드명과 provider 원문 용어**: `ccbaKdcd`, `ccbaAsno`, `ccbaCtcd`, 응답 XML/JSON 필드
- **URL**: `https://apis.data.go.kr/...`
- **표준 keyword**: CHANGELOG semver 라벨(`Added`/`Fixed`/`Security` 등), ADR

## 식별자 (혼동 방지)

| 항목 | 값 |
|------|----|
| GitHub 저장소 이름 | `python-krheritage-api` |
| Python import 모듈 | `krheritage` |
| PyPI 배포 | 현재 범위 제외 (`docs/index.md`) |
| 인증 환경변수 | `DATA_GO_KR_SERVICE_KEY` (다른 형제 저장소와 공유하는 data.go.kr 발급 키) |
| 패키지 전용 설정 환경변수 | `KHERITAGE_CACHE_DIR`, `KHERITAGE_MAX_RPS` (인증키가 아닌 로컬 동작 설정) |

## 절대 하지 말 것 (DO NOT)

- `AsyncHeritageClient`를 그대로 사용 가능한 것처럼 문서화하지 말 것 — 현재는 항상
  `NotImplementedError`를 던지는 자리표시자다
- feature 변환/도메인 매핑 로직을 이 저장소에 넣지 말 것 — 그 책임은 `python-krtour-map`의
  ETL 함수에 있다
- `docs/anti_corruption.md`에 기록된 legacy URL을 별도 안내 없이 직접 호출하지 말 것
- API 오류 envelope(HTTP 200 + 오류 코드로 감싸진 실패)를 빈 결과로 조용히 삼키지 말 것
- 서비스키나 기타 비밀정보를 예외 메시지·로그에 평문으로 남기지 말 것

## 검증

```bash
pytest
ruff check .
mypy src/krheritage
```
