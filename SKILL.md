# SKILL — maplibre-vworld-js 에이전트 매뉴얼

> 이 파일은 당신(AI 에이전트)이 작업을 시작하기 전 반드시 읽어야 한다.
> 1회만 읽으면 30분 이상의 디버깅을 줄일 수 있다.

## 1. 정체성

이 저장소(GitHub 이름 `maplibre-vworld-js`, npm 패키지 `maplibre-vworld`)는 한국 공간정보 오픈플랫폼 브이월드(VWorld)의 WMTS 타일을 React + MapLibre GL JS 환경에서 사용할 수 있게 묶어 둔 **범용 지도 라이브러리**다. 마커·팝업·레이어·클러스터링 같은 지도 primitive만 제공한다.

도메인 특화 코드(특정 앱의 카테고리 enum, 통화 단위, 색상 팔레트)는 라이브러리에 넣지 않는다(ADR-7). 라이브러리 사용자는 자기 앱의 도메인 로직을 직접 구성한다.

### 식별자 매핑

| 항목 | 값 |
|------|----|
| GitHub 저장소 | `maplibre-vworld-js` |
| npm 패키지 | `maplibre-vworld` |
| import | `from 'maplibre-vworld'` |
| 스타일 import | `'maplibre-vworld/style.css'` |
| peer dependency | `react`, `react-dom`, `maplibre-gl`, `zod@^4.4.3` |

### 개발 환경

- Node.js 20 LTS. 다른 버전은 보장 범위 밖.
- `PUPPETEER_SKIP_DOWNLOAD=1`로 `npm ci` — Puppeteer 브라우저 다운로드는 거의 쓰지 않으므로 회피.
- `dist/`는 커밋 대상(ADR-5). `vite build` 산출물이 깨끗하게 들어 있어야 머지 가능.
- `tsconfig.build.json`이 declaration emission을 `src/`로만 한정 — `dev/`, `test/` 타입 오류가 배포 산출물에 새지 않도록.
- GitHub Actions/CI는 사용하지 않는다(ADR-10). 품질 게이트는 PR을 푸시하기 전 작업자가 직접 로컬에서 실행한다.

## 2. 빠른 시작

```bash
cd F:\dev\maplibre-vworld-js
PUPPETEER_SKIP_DOWNLOAD=1 npm ci
npm run type-check
npm test
npm run build
git diff --exit-code -- dist/   # dist/ drift 검사
npm run pack:check               # tarball 산출물 확인
npm run dev                      # 로컬 dev 서버 (.env.local에 VITE_VWORLD_API_KEY)
```

자세한 환경 셋업은 `docs/dev-environment.md`.

에이전트 작업은 고정 worktree에서 진행한다. ChatGPT Codex는 `F:\dev\vw-codex`, Claude Code는 `F:\dev\vw-claude`, Google Antigravity 2.0은 `F:\dev\vw-antigravity`를 사용한다. worktree마다 한 번만 `codegraph init -i`를 실행하고, 작업 시작마다 `git fetch` 후 새 브랜치를 만들고 `codegraph sync`를 실행한다(ADR-12).

## 3. 디렉토리 지도

```
src/
  components/             — React 컴포넌트 (모두 'use client')
    VWorldMap.tsx         — 최상위 지도, MapStore + flyTo/jumpTo 카메라 큐
    Marker.tsx            — base marker (anchor/offset/className token diff)
    PinMarker.tsx · MakiMarker.tsx · SimpleMarker.tsx · …
    Popup.tsx             — construction-only opt snapshot + setter effects
    RouteLine.tsx · PolygonArea.tsx  — style.load 기반 재등록
    ClusterLayer.tsx · ServerClusterLayer.tsx · ClusterMarker.tsx
  store/
    mapStore.ts           — vanilla MapStore class (snapshot/listeners/setters)
    hooks.ts              — useMap, useMapZoom, useMapLoaded, useMapSelector, useEvent
    index.ts              — store 진입점
  schemas.ts              — zod (LngLat, Bounds, Point, region factory)
  vworld.ts               — getVWorldStyle/TileUrl/MaxZoom, redactVWorldUrl, isVWorldTileError
  index.ts                — public 진입점
test/
  setup.ts                — maplibre-gl mock (Map, Marker, Popup, controls)
  *.test.tsx              — Vitest + @testing-library/react
dist/                     — 빌드 산출물 (git 커밋 대상, drift 검사는 PR 전 로컬에서)
docs/                     — architecture, decisions, journal, tasks, resume, dev-environment
docs/consumer-requirements.md — TripMate/tour-map 소비자 요구사항과 예정 API 예제
```

의존 방향은 **`store` → `vworld`/`schemas` → `components` → `index.ts`** 한 방향. `components`는 서로 import 가능(`Marker` ⇄ `PinMarker` 등 합성).

## 4. 절대 하지 말 것 (DO NOT)

1. **`main` 직접 푸시 금지**: 반드시 feature 브랜치 + PR. `--no-verify`로 hook 우회 금지.
2. **도메인 특화 코드 추가 금지**: 특정 소비자 앱(TripMate, kraddr 등)의 카테고리/통화/색상을 라이브러리에 넣지 않는다(ADR-7). 일반화가 필요하면 factory(`makeBoundedLngLatSchema` 같은)로 노출.
3. **`dist/` 커밋 누락 금지**: `src/` 변경 후 `npm run build` 안 하면 GitHub dependency 소비자가 stale 산출물을 가져간다. PR 전 `git diff --exit-code -- dist/`로 확인.
4. **`'use client'` 누락 금지**: DOM-touching 모듈은 모두 첫 줄에 `'use client'`. Next.js App Router의 RSC에서 import할 수 있어야 한다.
5. **`useMemo` 미적용 prop 가정 깨기 금지**: `RouteLine.coordinates`, `PolygonArea.data`, `flyToOptions` 같은 deep-equal 비싼 prop은 consumer가 memoize한다는 가정 위에 동작한다. 라이브러리 내부에서 `JSON.stringify(...)`로 deps를 만들면 큰 GeoJSON에서 main thread를 막는다.
6. **`map.setTerrain()` 호출 금지**: VWorld는 Terrain-RGB를 제공하지 않는다.
7. **`onError` envelope wrapper 추가 금지**: raw MapLibre `ErrorEvent`를 그대로 노출한다(ADR-7). 카운트/임계치/UI는 소비자 앱 책임.
8. **camera prop 적용 시 `isMoving/isEasing` 가드 누락 금지**: 사용자 제스처 중 강제 `flyTo`는 진동을 만든다. 대신 `pendingCameraRef`로 큐잉하고 `moveend`에서 재시도.
9. **`createContext` value를 매 render마다 새 object로 만들기 금지**: store 단일 source(ADR-8). selector slice 변경 시에만 re-render.
10. **`useMapSelector` cache key에 selector identity 포함 금지**: consumer가 `useCallback`을 잊어도 무한 render가 일어나지 않아야 한다 — selector는 ref, cache key는 snapshot identity, value 비교는 `Object.is`.
11. **`styledata` listener 등록 금지**: 우리 자신의 `setPaintProperty`가 다시 `styledata`를 발화시켜 재진입 가능. layer 보존이 필요하면 `style.load` (setStyle 완료 시 1회).
12. **API 키 평문 커밋 금지**: `dev/` 안의 hardcode도 금지(과거 보안 사고). `.env.local` 권한 600. 로그는 `redactVWorldUrl()`로 마스킹.
13. **zod v3 코드 추가 금지**: peer + dev 모두 v4 고정(ADR-6). `src/schemas.ts`는 v3/v4 공통 표면(`z.tuple`, `z.union`, `z.array().min`, `z.number().min().max`)만 사용.
14. **소비자 앱에 마커 portal teardown 책임 떠넘기기 금지**: `<Marker>` unmount 시 React fiber를 정리하지 않으면 stale handler가 남는다 — portal 해제는 라이브러리 책임.
15. **`.codegraph/` 커밋 금지**: CodeGraph 인덱스는 worktree 로컬 산출물이다. 새 worktree에서만 `codegraph init -i`, 기존 worktree에서는 `codegraph sync`.

## 5. 자주 묻는 작업

| 작업 | 시작 파일 |
|------|-----------|
| 새 마커 컴포넌트 추가 | `src/components/<Name>Marker.tsx` (`<Marker>` 합성, `'use client'` 첫줄) → `src/index.ts` export |
| 새 hook 추가 | `src/store/hooks.ts`에 selector wrapper, `src/index.ts` re-export |
| MapStore에 slice 추가 | `MapStoreSnapshot` 타입 확장 + setter + initial snapshot + `VWorldMap`에서 emit |
| 새 VWorld 헬퍼 추가 | `src/vworld.ts`. URL/style/redact는 한 곳에 모은다 |
| 새 zod 스키마 | `src/schemas.ts`. region-bounded는 `makeBoundedLngLatSchema` factory 사용 |
| MapLibre prop 노출 | `VWorldMap` props 추가 → mount effect에서 옵션 전달 → 변경 effect에서 setter |
| 새 에러 분류기 | `src/vworld.ts`의 `isVWorldTileError` 패턴 따라 — `error?.message` null-safe 처리 |

## 6. 도메인 어휘

| 약어 / 용어 | 의미 |
|------|------|
| VWorld | 공간정보 오픈플랫폼 (`api.vworld.kr`). 한국 정부가 운영하는 WMTS 타일 서비스 |
| WMTS | Web Map Tile Service (OGC 표준). `{z}/{y}/{x}` 타일 URL 패턴 |
| layerType | `Base` / `gray` / `midnight` / `Hybrid` / `Satellite`. Satellite/Hybrid는 z18까지, 나머지는 z19까지 |
| Maki | Mapbox 오픈소스 SVG icon set. `MakiMarker`가 CSS mask로 렌더 |
| supercluster | KDBush 기반 점 데이터 클러스터 알고리즘. 메모리 친화적 |
| `pendingCameraRef` | 사용자 제스처 중 들어온 카메라 prop을 큐잉. `moveend`에서 재시도 |
| `useEvent` | `useLayoutEffect + useRef + useCallback` 합성. stable identity + latest closure |
| `useMapSelector` | snapshot slice를 referential cache로 노출. thresh-crossing만 re-render |
| `'use client'` | Next.js App Router의 RSC ↔ Client 경계 directive |
| portal | `React.createPortal` — React tree를 MapLibre가 만든 DOM 노드로 teleport |

## 7. 작업 후 체크리스트

- [ ] `npm run type-check` 통과
- [ ] `npm test` 통과
- [ ] `npm run build` 통과 (`dist/` 갱신 후 커밋)
- [ ] `git diff --exit-code -- dist/` 통과 (CI 동일 검사)
- [ ] `npm run pack:check` 통과
- [ ] `docs/journal.md`에 작업 항목 추가 (역시간순)
- [ ] `docs/tasks.md`의 T-NNN 상태 갱신
- [ ] 의사결정이 있었다면 `docs/decisions.md`에 ADR 추가
- [ ] 사용자 가시 변경이면 `CHANGELOG.md` 갱신
- [ ] public API 변경이면 `README.md`와 `AI_AGENT_GUIDE.md` 동기화
