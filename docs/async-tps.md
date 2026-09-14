# 비동기 호출과 공통 속도 제어

## 비동기 호출과 TPS

HeritageClient의 네트워크 메서드는 await, 페이지·상세·월별 반복은 async for,
종료는 async with 또는 await client.aclose()를 사용한다. 동기 HTTP와
AsyncHeritageClient 자리표시자·aio 팩터리는 제거했다. 코드표·파싱·메타데이터는
일반 함수로 유지한다. 기존 서비스 인자와 반환 모델은 동일하다.

max_rps는 기본 5이며 KHERITAGE_MAX_RPS 환경변수로 설정할 수 있다.
AsyncTokenBucket을 rate_limiter에 주입하면 클라이언트 여러 개의 요청 예산을
합산하고 max_rps보다 우선한다. 버킷의 기본 capacity는 max(1, max_rps)이며
초기에 가득 차 있으므로 burst를 허용한다. 일정한 송신 간격이 필요하면 capacity=1을
사용한다. 모든 서비스·debug·페이지, 각 재시도와 리다이렉트마다 토큰을 소비한다.
대기 취소는 토큰을 쓰지 않는다. 버킷은 한 이벤트 루프에서만 사용한다.

내부 생성 HTTPX 세션은 문맥 종료 시 닫는다. session으로 주입한 AsyncClient는
호출자가 닫는다. 본문 스트리밍 중 취소·50MB 상한 오류에도 응답을 닫는다.
HTTP 429와 5xx 및 전송 오류는 재시도하며 나머지 HTTP 4xx는 즉시 반환한다.
사용자 정의 인증·transport 내부의 추가 요청은 라이브러리 밖의 동작이다.
files.write_bytes의 파일 쓰기는 작업 스레드에서 실행한다. 취소는 이미 시작한
디스크 쓰기를 되돌리지 않는다.

```python
import asyncio
from krheritage import AsyncTokenBucket, HeritageClient


async def main() -> None:
    bucket = AsyncTokenBucket(2, capacity=1)
    async with HeritageClient(rate_limiter=bucket) as client:
        page = await client.search.list(page_size=1)
        print(page.items)
        async for detail in client.heritage.iter_all_details(page_size=1, max_pages=1):
            print(detail.name_ko)


asyncio.run(main())
```
