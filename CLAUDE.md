# CLAUDE.md — 프로젝트 컨텍스트

이 파일은 Claude Code가 매 세션 시작 시 자동으로 읽는다.
프로젝트 규칙은 `AGENTS.md`에, 아키텍처는 `docs/architecture.md`에 있다.
이 파일은 **현재 상태**와 **세션 간 연속성**에 집중한다.

## 프로젝트 현황 (2026-05-27)

React + MapLibre GL JS 기반 VWorld(한국 공간정보 오픈플랫폼) 지도 라이브러리. npm 패키지 이름은 `maplibre-vworld`, GitHub 저장소는 `maplibre-vworld-js`. PR #1 ~ #24 머지 baseline 위에 T-001 ~ T-018, T-020 ~ T-025 완료 (T-019/T-026~T-029는 백로그). 현재 main은 외부 store + `useSyncExternalStore` 아키텍처와 `useEvent` 패턴이 정착되었고, 모든 문서는 한글로 작성되며(예외 조항 없음 — `AGENTS.md` 언어 정책), 문서 구조는 python-kraddr-geo 식으로 정리되었고, GitHub Actions/CI는 사용하지 않는다(ADR-10 — 로컬 게이트만 사용). 동적 z-index, 시멘틱 줌 manual expand, PriceMarker 다중 가격/LOD 같은 마커 UX가 ADR-11로 결정·구현된 상태. TripMate/tour-map 소비자 요구사항은 `docs/consumer-requirements.md`에 문서화되어 있고, CodeGraph + 에이전트별 고정 worktree 운영은 ADR-12로 기록되어 있다.

### 현재 작업

- (없음) — 다음 한 작업은 `docs/resume.md` 참고.

### 잔존 기술 부채

PR #14에서 PR #13 follow-up이 정리되고 PR #15에서 문서 구조가 정착되어 부채는 낮다.

- (없음 — 새 부채가 발견되면 `docs/tasks.md`에 T-NNN으로 등록한다)

### 브랜치 정리

머지 완료된 리모트 브랜치 (삭제 가능):
- `codex/tripmate-implementation-docs` — PR #10 merged.
- `codex/tripmate-map-primitives` — PR #11 merged.
- `refactor/generalize-and-cleanup` — PR #12 merged.
- `codex/main-review-fixes` — PR #13 merged.
- `fix/post-pr13-review-fixes` — PR #14 merged.
- `codex/debug-map-contract-hooks` — PR #9 merged.
- `chore/adopt-kraddr-doc-structure` — PR #15 merged, 로컬·리모트 모두 삭제됨.
- `chore/post-T-015-status-update` — PR #16 merged, 로컬·리모트 모두 삭제됨.
- `chore/remove-github-actions` — PR #17 merged, 로컬·리모트 모두 삭제됨.
- `chore/post-T-016-status-update` — PR #18 merged, 로컬·리모트 모두 삭제됨.
- `chore/all-docs-in-korean` — PR #19 merged, 로컬·리모트 모두 삭제됨.
- `feat/enhance-routes-and-stability` — PR #20 merged.
- `feat/popup-z-index` — PR #21 merged.
- `feat/price-marker-array` — PR #22 merged.
- `docs/adr-11` — PR #23 merged.

### 후속 백로그

- T-019: VWorld `getCapabilities` 응답을 활용한 layer/tile matrix 자동 검증 — 현재 `getVWorldMaxZoom`은 하드코딩 표.
- T-026: `<VWorldMap>` lazy loading 지원.
- T-027: 마커 클릭/지도 클릭 구분 context 지원.
- T-028: 지원되지 않는 타일 대체 이미지/동작 구현.
- T-029: CI/CD 활성화 재검토 — ADR-10과 충돌하므로 새 ADR 선행.
- (그 외 신규 항목은 발견 시 `docs/tasks.md`에 T-030부터 등록.)

## 에이전트 worktree + CodeGraph

ChatGPT Codex는 `F:\dev\vw-codex`, Claude Code는 `F:\dev\vw-claude`, Google Antigravity 2.0은 `F:\dev\vw-antigravity`를 고정 worktree로 사용한다. 새 작업은 해당 worktree에서 `git fetch` 후 `git switch -c agent/<topic> main`으로 브랜치만 새로 딴다. CodeGraph는 worktree마다 1회 `codegraph init -i`로 초기화하고 이후에는 `codegraph sync`만 실행한다. `.codegraph/`는 gitignore 대상이며, MCP 설정은 프로젝트 루트 `.codex/config.toml`에 있다.

## 로컬 개발 환경

```
F:\dev\maplibre-vworld-js\
├── src/              # 소스 — declaration 생성 대상
│   ├── components/   # React 컴포넌트 (모두 'use client')
│   ├── store/        # MapStore + useSyncExternalStore hooks
│   ├── schemas.ts    # zod 스키마 (region-bounded factory 포함)
│   ├── vworld.ts     # VWorld URL/style/redact helper
│   └── index.ts      # public 진입점
├── test/             # vitest + Testing Library
├── dist/             # 빌드 산출물 (git 커밋 대상 — ADR-5)
├── dev/              # 로컬 dev 서버용 (배포 산출물에서 제외)
└── docs/             # 아키텍처, ADR, journal, tasks
```

Node 20 LTS. `npm ci` → `npm test` / `npm run build`.

## VWorld 계약

| 항목 | 값 |
|------|----|
| 타일 URL | `https://api.vworld.kr/req/wmts/1.0.0/{key}/{layer}/{z}/{y}/{x}.{ext}` |
| Satellite / Hybrid max zoom | 18 |
| Base / gray / midnight max zoom | 19 |
| Attribution | `공간정보 오픈플랫폼 브이월드` |

`apiKey`는 양 끝 whitespace를 trim하고 URL-encode한 뒤 사용한다. 빈 키 / 공백뿐인 키는 `fallback` 렌더로 빠지고 MapLibre 인스턴스를 만들지 않는다.

## 빠른 검증 명령

```bash
# 의존성
PUPPETEER_SKIP_DOWNLOAD=1 npm ci

# 품질 게이트 (PR 전 로컬에서 직접 돌린다 — GitHub Actions는 사용하지 않는다)
npm run type-check
npm test
npm run build
git diff --exit-code -- dist/        # dist/ drift 검사
npm run pack:check                    # tarball 산출물 확인
codegraph sync && codegraph status     # CodeGraph 인덱스 최신화/상태 확인

# dev 서버
npm run dev
```

## 주요 결정 사항

- ADR-1: 렌더링 엔진 MapLibre GL JS (Canvas 2D 대비 60fps)
- ADR-2: React.createPortal로 마커 주입 — React 라이프사이클과 동기화
- ADR-3: supercluster + viewport culling — 10만 마커 메모리 안전
- ADR-4: `transformRequest` — CORS/프록시 우회 hook
- ADR-5: `dist/` 커밋 — GitHub dependency 소비자 보호
- ADR-6: zod v4 강제 (v3 미지원, externalize)
- ADR-7: 범용 라이브러리 경계 — 도메인 특화 코드 비포함
- ADR-8: 외부 store + `useSyncExternalStore` + `useEvent` 패턴

상세는 `docs/decisions.md`.

## 작업 후 의무사항

1. `docs/journal.md`에 항목 추가 (날짜·요약·결정·다음 작업, 역시간순)
2. `docs/tasks.md`의 현재 작업 상태 업데이트
3. 결정이 있었다면 `docs/decisions.md`에 ADR 추가
4. 사용자 가시 변경이면 `CHANGELOG.md` 갱신
5. `npm run build` 후 `dist/` 커밋 — `git diff --exit-code -- dist/`가 깨끗해야 PR 머지
