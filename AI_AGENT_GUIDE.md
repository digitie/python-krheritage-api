# AI 에이전트 가이드: maplibre-vworld-js

이 라이브러리를 사용해 코드를 생성하는 AI 코딩 어시스턴트(Cursor, Copilot, ChatGPT, Claude Code 등)를 위한 컨텍스트 문서다.

> **본 저장소를 직접 수정하는 컨트리뷰터/에이전트는 다른 문서를 본다**: [`CLAUDE.md`](./CLAUDE.md)가 진입점, 한글 매뉴얼은 [`SKILL.md`](./SKILL.md), 아키텍처·결정·일지·태스크는 [`docs/`](./docs/)에 있다. 이 문서는 **소비자 앱**(이 라이브러리를 import해서 쓰는 React 앱)을 작성하는 AI 가이드다.

## 이 라이브러리는 무엇인가

- React (18+) 환경에서 MapLibre GL JS v5를 한국 VWorld(공간정보 오픈플랫폼) 베이스맵으로 구성한 바인딩.
- 지도 primitive만 제공한다: 마커, 팝업, 레이어, 클러스터링, 지역-bounded zod 스키마.
- 다음은 라이브러리 책임이 **아니다**: 데이터 fetching, 상태 관리, 감사 로그, 서버 API 호출, 비즈니스 카테고리 enum, 디자인 팔레트. 그런 관심사는 소비자 앱에 둔다.

## 아키텍처 규칙

- 모든 DOM 모듈은 첫 줄에 `'use client'`를 선언한다. Next.js App Router의 React Server Component에서 그대로 import해도 안전 — directive가 작업을 클라이언트 번들로 이동시킨다. `next/dynamic({ ssr: false })`로 감쌀 필요 없음.
- 지도 상태는 외부 store(`MapStore` + `useSyncExternalStore`)로 노출된다. 자식 컴포넌트는 필요한 slice만 구독하므로 카메라 이동이 전체 트리를 re-render하지 않는다.
- 내부적으로 이벤트 핸들러는 `useEvent`를 거친다. 따라서 prop callback이 매 render마다 새 closure여도 MapLibre 인스턴스나 리스너가 재구성되지 않는다.
- `dist/`는 GitHub dependency 소비자를 위해 커밋되어 있다. `tsconfig.build.json`이 declaration emission을 `src/`로 한정해, `dev/`와 `test/` 타입 오류가 배포 산출물에 새지 않는다.
- 본 저장소는 GitHub Actions/CI를 사용하지 않는다(ADR-10). 유지보수자가 머지 전 `npm run type-check && npm test && npm run build && git diff --exit-code -- dist/`를 로컬에서 실행한다.

## 컴포넌트 표면

### `<VWorldMap>`

```ts
interface VWorldMapProps {
  apiKey: string;                       // 필수
  center: [number, number];             // 필수, [lng, lat]
  zoom?: number;                        // 기본 12
  pitch?: number;
  bearing?: number;
  layerType?: 'Base' | 'gray' | 'midnight' | 'Hybrid' | 'Satellite';
  minZoom?: number; maxZoom?: number;
  maxBounds?: maplibregl.LngLatBoundsLike;
  semanticZoomThreshold?: number;
  navigation?: boolean; geolocate?: boolean; scale?: boolean;
  onLoad?: (map) => void;
  onClick?: (MapMouseEvent) => void;
  onContextMenu?: (MapMouseEvent) => void;
  onMoveEnd?: (MapLibreEvent) => void;
  onZoomEnd?: (MapLibreEvent) => void;
  onIdle?: (MapLibreEvent) => void;
  onError?: (ErrorEvent) => void;
  transformRequest?: maplibregl.RequestTransformFunction;
  fallback?: ReactNode | ((info: { reason: 'missing-api-key' | 'map-init-error'; error?: Error }) => ReactNode);
  loadingSkeleton?: ReactNode;
  animateCameraChanges?: boolean;       // 기본 true
  flyToOptions?: Omit<FlyToOptions, 'center' | 'zoom' | 'pitch' | 'bearing'>;
}
```

AI가 지킬 규칙:

- **`center`에 암묵적 기본값 없음**. `center`는 필수다. 앱에 맞는 적절한 값을 직접 지정.
- 이벤트 콜백은 **raw** MapLibre 이벤트를 받는다. `VWorldMap*Info` 같은 envelope wrapper 없음.
- 카메라 prop 변경(`center`, `zoom`, `pitch`, `bearing`)은 `flyTo` (애니메이션) 또는 `jumpTo` (즉시)로 적용된다. 사용자 제스처 중(`map.isMoving()`)에는 silent drop하지 않고 큐잉해서 `moveend` 시 재시도한다.
- `Satellite`/`Hybrid`는 z18에서 clamp, `Base`/`gray`/`midnight`는 z19에서 clamp. 라이브러리가 자동으로 처리하므로 `maxZoom`을 `getVWorldMaxZoom(layerType)`보다 크게 지정하지 말 것.
- CORS / 프록시 요구는 `transformRequest`로 해결. 헤더 주입을 위해 라이브러리를 fork하지 말 것.

### Hooks (`maplibre-vworld`)

```ts
useMap(): MapLibreMap | null         // mount/unmount에서만 re-render, identity 안정
useMapZoom(): number                 // zoomend에서 re-render
useMapLoaded(): boolean
useMapSelector(selector): T          // 임의 slice, referential caching
useEvent(handler): T                 // 항상 최신을 호출하는 stable callback
```

threshold 검사(`zoom < N`)는 `useMapSelector`를 권장. consumer는 boolean이 flip하는 순간에만 re-render하고, 매 zoom 이벤트마다는 re-render하지 않는다.

### 마커

`Marker`, `PinMarker`, `MakiMarker`, `PulsingMarker`, `SimpleMarker`, `PlaceMarker`, `PriceMarker`, `WeatherMarker`, `RoutePointMarker`, `ClusterMarker`.

대부분의 마커가 공통으로 받는 상태 prop: `selected`, `highlighted`, `zIndex`, `ariaLabel`, `className`. DOM에는 `data-selected` / `data-highlighted` 속성이 노출된다.

`MakiMarker`는 단일 `icon: string` prop만 받는다 (예: `'restaurant'`, `'park'`). `iconName`/`fallbackIcon` 같은 alias 없음.

### 레이어

- `RouteLine` — 폴리라인. `coordinates: [number, number][]`, `color`, `width`, `dashArray`. `coordinates` 배열은 반드시 memoize.
- `PolygonArea` — Polygon/MultiPolygon GeoJSON 채우기 + 외곽선.
- `ClusterLayer` — `supercluster` 기반 클라이언트 사이드 클러스터링.
- `ServerClusterLayer` — 서버에서 그룹화된 클러스터. `cluster.bounds`가 있으면 `fitBounds`, 없으면 `flyTo`.

### 팝업

```tsx
<Popup lngLat={[lng, lat]} onClose={…}>{children}</Popup>
```

### 스키마

```ts
LngLatSchema, BoundsSchema, PointSchema, RouteCoordinatesSchema
makeBoundedLngLatSchema(lngRange, latRange)
makeBoundedBoundsSchema(lngRange, latRange)
extendPointSchema({ … })
formatLngLat(lngLat, precision)
serializeBounds(bounds, precision)
parseBoundsParam(string)
```

라이브러리 core에 한국 전용 상수는 없다. 한국 preset이 필요하면 소비자 앱 안에서 직접 만든다:

```ts
const KoreaLngLat = makeBoundedLngLatSchema([124, 132], [33, 43]);
```

### VWorld 유틸리티

```ts
getVWorldTileUrl(apiKey, layerType)   // {z}/{y}/{x}를 가진 WMTS URL template
getVWorldStyle(apiKey, layerType)     // MapLibre StyleSpecification
getVWorldMaxZoom(layerType)           // 18 (Sat/Hybrid) 또는 19
redactVWorldUrl(url)                  // 로그용으로 API key 세그먼트를 마스킹
isVWorldTileError(errorEvent)         // tile vs style 오류 분류
```

## 피해야 할 것

- hook을 `./components/VWorldMap`에서 직접 import하지 말 것. 패키지 root나 `./store/hooks`를 사용한다.
- diff가 발생하는 prop(`coordinates`, GeoJSON `data`, `flyToOptions`)에 인라인 객체를 넘기지 말 것. memoize하거나 ref에 보관.
- 도메인 특화 코드(TripMate, kraddr 등)를 본 저장소에 추가하지 말 것. 라이브러리는 범용으로 유지.
- VWorld에 `map.setTerrain()`을 호출하지 말 것 — VWorld는 Terrain-RGB를 제공하지 않는다.
- `next/dynamic({ ssr: false })`로 본 라이브러리를 감싸지 말 것. 이미 SSR 안전하다. 소비자가 특수한 이유가 있는 경우에만 사용.

## 문서화된 후속 요구사항

TripMate와 tour-map에서 필요한 lazy loading, 마커/지도 클릭 context, 지원되지 않는 타일 fallback, CI/CD 활성화 검토는 [`docs/consumer-requirements.md`](./docs/consumer-requirements.md)에 있다. 이 문서의 "예정 API" 코드는 2026-05-27 기준 구현 전 예시이므로, 소비자 앱 코드를 생성할 때 현재 README의 실제 API와 혼동하지 말 것.

## 머지 정책

브랜치 + PR만 허용. `main`은 보호됨 — 직접 push 금지, `--no-verify` 금지.

## 더 읽을거리

- [`README.md`](./README.md) — 사용자 대상 소개와 API 레퍼런스
- [`CLAUDE.md`](./CLAUDE.md) — 현재 상태 (Claude Code가 세션 시작 시 자동 로드)
- [`AGENTS.md`](./AGENTS.md) — 언어 정책, 식별자 매트릭스, DO NOT 규칙
- [`SKILL.md`](./SKILL.md) — 본 저장소 컨트리뷰터/에이전트 매뉴얼
- [`docs/architecture.md`](./docs/architecture.md) — `MapStore` + `useSyncExternalStore` 심층 분석
- [`docs/decisions.md`](./docs/decisions.md) — ADR-1 ~ ADR-12
- [`docs/consumer-requirements.md`](./docs/consumer-requirements.md) — TripMate/tour-map 요구사항과 예정 API 예제
- [`docs/journal.md`](./docs/journal.md) — 작업 일지 (역시간순)
- [`docs/tasks.md`](./docs/tasks.md) — T-NNN 백로그
- [`docs/dev-environment.md`](./docs/dev-environment.md) — 로컬 셋업
