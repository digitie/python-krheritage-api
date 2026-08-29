# decisions.md — 의사결정 기록

이 문서는 이 프로젝트의 구조적 결정을 결정 시점 순서로 누적한다.
결정이 뒤집힐 때는 새 항목을 추가하고, 옛 항목은 지우지 않은 채
`(supersedes: 위 항목)`으로 표시한다.

## D-001: PyPI 공개 배포는 현재 범위에서 제외한다

- 상태: accepted
- 날짜: 2026-05-27

### 컨텍스트
`python-krheritage-api`는 TripMate/`kor-travel-map` 내부에서만 소비되는 라이브러리다.

### 결정
PyPI에 공개 배포하지 않는다. GitHub 저장소(`https://github.com/digitie/python-krheritage-api`)를
직접 의존성으로 설치한다.

### 근거
외부 공개 없이 내부 소비자만 있는 상태에서 배포 파이프라인을 유지할 이유가 없다.

### 결과
`README.md`/`docs/index.md`가 이 결정을 명시하고, `CHANGELOG.md`도 이를 "project 결정"으로
기록한다.

## D-002: `AsyncHeritageClient`는 실제 비동기 서비스 레이어가 붙기 전까지 자리표시자로 둔다

- 상태: accepted
- 날짜: 2026-05-27 (초기 구현부터)

### 컨텍스트
`HeritageClient`(sync)만 실제 서비스 레이어(search/event/gis 등)를 갖고 있다.

### 결정
`AsyncHeritageClient.__init__`은 항상 `NotImplementedError`를 던진다. 비동기 지원을 흉내만
내는 빈 구현을 두지 않는다.

### 근거
동작하지 않는 비동기 API를 조용히 노출하면 소비자 앱이 이를 실제로 쓸 수 있다고 오해할 수
있다. 명시적으로 실패시켜 오용을 막는다.

### 결과
`AI_AGENT_GUIDE.md`/`AGENTS.md`/`SKILL.md`가 이를 명시한다. 비동기 서비스 레이어를 실제로
추가할 때는 이 항목을 supersede하는 새 결정을 남긴다.

## D-003: 인증키는 형제 저장소와 `DATA_GO_KR_SERVICE_KEY`를 공유하고, 로컬 설정은 `KHERITAGE_*` 프리픽스를 쓴다

- 상태: accepted
- 날짜: 2026-05-27

### 컨텍스트
`config.py`는 `DATA_GO_KR_SERVICE_KEY`(API 인증)와 `KHERITAGE_CACHE_DIR`/`KHERITAGE_MAX_RPS`(로컬
동작 설정)를 함께 읽는다.

### 결정
API 인증키는 같은 data.go.kr 발급 키를 쓰는 다른 형제 저장소(mois, kasi, airkorea 등)와 이름을
통일해 `DATA_GO_KR_SERVICE_KEY`로 둔다. 인증키가 아닌, 이 패키지에만 의미 있는 설정값(캐시
경로, 초당 요청 제한)은 `KHERITAGE_*` 프리픽스로 구분한다.

### 근거
인증키는 실제로 동일한 발급 체계를 공유하므로 이름을 통일하면 여러 형제 라이브러리를 함께
쓰는 소비자 앱의 설정이 단순해진다. 반대로 로컬 전용 설정값까지 공용 이름으로 두면 다른
패키지와 충돌하거나 오해를 부를 수 있어 프리픽스로 분리한다.

### 결과
두 계열의 환경변수가 섞여 있는 것이 의도된 설계이며, 실수로 통일할 대상이 아니다.

## D-004: 알려진 endpoint 이동은 anti-corruption 별칭 계층에서만 흡수한다

- 상태: accepted
- 날짜: 2026-05-27

### 컨텍스트
국가유산청 API의 일부 URL이 오타/구조 변경으로 이동한 사례가 있다(예:
`recodeImageView` → `recordImageView`).

### 결정
알려진 legacy URL은 서비스 코드 여기저기서 직접 분기하지 않고, `krheritage.transport._aliases`
한 곳에서 이전 URL을 감지해 `DeprecationWarning`과 함께 새 URL로 치환한다. 새로 발견되는
이동/오타도 이 계층에 추가한다.

### 근거
URL 이동 처리를 서비스 코드에 흩뿌리면 같은 문제를 여러 곳에서 각자 다르게 처리하게 된다.
단일 anti-corruption 계층에 모아두면 유지보수와 감사가 쉽다.

### 결과
`docs/anti_corruption.md`가 알려진 이동 목록의 정본이다. 새 이동을 발견하면 이 표와
`_aliases.py`를 함께 갱신한다.
