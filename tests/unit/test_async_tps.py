"""공개 서비스의 공통 과금·HTTP 오류·스트림 정리 계약을 검증한다."""

import asyncio

import httpx
import pytest
from tenacity import wait_none

from krheritage import AsyncTokenBucket, HeritageClient, HeritageConfig
from krheritage.debug import debug_error
from krheritage.exceptions import ApiErrorResponse, TransportError
from krheritage.transport import AsyncHttpxTransport

LIST = b"""<result><totalCnt>1</totalCnt><pageIndex>1</pageIndex><pageUnit>1</pageUnit>
<item><ccbaKdcd>11</ccbaKdcd><ccbaAsno>0000010000000</ccbaAsno><ccbaCtcd>11</ccbaCtcd>
<ccbaMnm1>Sungnyemun</ccbaMnm1></item></result>"""
EVENT = b"""<result><item><sn>EVT-1</sn><title>Festival</title>
<startDate>20260901</startDate><endDate>20260930</endDate></item></result>"""
GIS = b"""<result><item><gid>AREA-1</gid><longitude>127</longitude>
<latitude>37</latitude></item></result>"""


class CountingBucket(AsyncTokenBucket):
    def __init__(self):
        super().__init__(10000)
        self.calls = 0

    async def acquire(self):
        await super().acquire()
        self.calls += 1


async def test_public_services_pages_debug_and_two_clients_share_budget():
    bucket = CountingBucket()
    seen = []

    async def handler(request):
        seen.append(request)
        if "Event" in request.url.path:
            content = EVENT
        elif "spca" in request.url.path:
            content = GIS
        else:
            content = LIST
        return httpx.Response(200, content=content)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as session:
        async with (
            HeritageClient(session=session, rate_limiter=bucket, max_rps=-1) as first,
            HeritageClient(session=session, rate_limiter=bucket) as second,
        ):
            rows = [row async for row in first.heritage.iter_all_details(page_size=1)]
            assert rows[0].name_ko == "Sungnyemun"
            months = [
                row async for row in first.event.iter_months(search_year=2026, search_month=9)
            ]
            assert months[0].display_title == "Festival"
            assert (await second.gis.spca()).features
            run = await second.debug_fetch("khs-search-list")
            assert run.error is None
        assert not session.is_closed
        with pytest.raises(RuntimeError, match="closed"):
            await first.search.list()
    assert bucket.calls == len(seen) == 5


async def test_retry_redirect_and_final_http_status_each_charge_once(monkeypatch):
    monkeypatch.setattr(
        AsyncHttpxTransport, "get", AsyncHttpxTransport.get.retry_with(wait=wait_none())
    )
    bucket = CountingBucket()
    seen = []

    async def handler(request):
        seen.append(request)
        if len(seen) == 1:
            return httpx.Response(503)
        if len(seen) == 2:
            return httpx.Response(302, headers={"location": "/final"})
        return httpx.Response(403)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), follow_redirects=True
    ) as session:
        transport = AsyncHttpxTransport(
            HeritageConfig.from_env(api_key="fake-secret"), session=session, rate_limiter=bucket
        )
        with pytest.raises(TransportError) as caught:
            await transport.get("https://apis.data.go.kr/fake")
        assert caught.value.status_code == 403
        assert "fake-secret" not in str(caught.value)
        await transport.aclose()
        assert not session.is_closed
    assert len(seen) == bucket.calls == 3


class BlockingStream(httpx.AsyncByteStream):
    def __init__(self):
        self.entered = asyncio.Event()
        self.closed = False

    async def __aiter__(self):
        self.entered.set()
        await asyncio.Event().wait()
        yield b"unused"

    async def aclose(self):
        self.closed = True


async def test_body_cancellation_closes_stream_and_preserves_injected_session():
    stream = BlockingStream()
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, stream=stream))
    ) as session:
        async with HeritageClient(session=session) as client:
            task = asyncio.create_task(client.search.list())
            await stream.entered.wait()
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert stream.closed
        assert not session.is_closed


async def test_oversize_stream_fails_once_and_closes_response(monkeypatch):
    monkeypatch.setattr("krheritage.transport.client._MAX_RESPONSE_BYTES", 3)
    count = 0
    responses = []

    async def handler(request):
        nonlocal count
        count += 1
        response = httpx.Response(200, content=b"too large")
        responses.append(response)
        return response

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as session:
        async with HeritageClient(session=session) as client:
            with pytest.raises(TransportError, match="byte limit"):
                await client.search.list()
    assert count == 1
    assert all(response.is_closed for response in responses)


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf"), True])
def test_invalid_rate_rejected_before_creating_client(value):
    with pytest.raises(ValueError):
        HeritageClient(max_rps=value)


async def test_debug_does_not_attach_key_to_unrelated_custom_host():
    requests = []

    async def handler(request):
        requests.append(request)
        return httpx.Response(200, content=LIST)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as session:
        async with HeritageClient(api_key="fake-secret", session=session) as client:
            await client.debug_fetch(
                "data-go-kr-custom", custom_path="https://apis.data.go.kr.attacker.invalid/probe"
            )
            await client.debug_fetch("data-go-kr-custom", custom_path="/safe-service")
    assert "serviceKey" not in requests[0].url.params
    assert requests[1].url.params["serviceKey"] == "fake-secret"


async def test_provider_key_echo_is_redacted_after_error_classification():
    key = "fake-secret"

    async def handler(request):
        return httpx.Response(200, json={"result": {"message": {"code": "403", "text": key}}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as session:
        async with HeritageClient(api_key=key, session=session) as client:
            with pytest.raises(ApiErrorResponse) as caught:
                await client.search.list()
            assert caught.value.code == "403"
            assert key not in str(caught.value)
            assert key not in str(caught.value.payload)
            run = await client.debug_fetch("khs-search-list")
            assert run.error["result_code"] == "403"
            assert key not in str(run.error)
            assert key not in str(run.response)


def test_debug_respects_explicit_transport_status_and_retryability():
    retry = debug_error(TransportError("throttled", status_code=429))
    assert retry["status_code"] == 429
    assert retry["retryable"] is True
    assert debug_error(TransportError("large", retryable=False))["retryable"] is False
    assert debug_error(TransportError("blocked", status_code=403))["retryable"] is False


async def test_redirect_stream_is_discarded_without_reading_body():
    class UnboundedStream(httpx.AsyncByteStream):
        closed = False

        async def __aiter__(self):
            raise AssertionError("redirect body must not be read")
            yield b"unused"

        async def aclose(self):
            self.closed = True

    stream = UnboundedStream()

    async def handler(request):
        if request.url.path.endswith("SearchKindOpenapiList.do"):
            return httpx.Response(302, headers={"location": "/final"}, stream=stream)
        return httpx.Response(200, content=LIST)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), follow_redirects=True
    ) as session:
        async with HeritageClient(session=session) as client:
            assert (await client.search.list()).items
    assert stream.closed


async def test_debug_validates_original_coordinates_before_redacting_output():
    content = LIST.replace(b"</item>", b"<longitude>127</longitude><latitude>37</latitude></item>")
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, content=content))
    ) as session:
        async with HeritageClient(api_key="127", session=session) as client:
            assert (await client.search.list()).items
            run = await client.debug_fetch("khs-search-list")
    assert not run.validation_errors
    assert len(run.parsed) == 1


async def test_debug_url_input_request_and_trace_mask_inline_credentials():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, content=LIST))
    ) as session:
        async with HeritageClient(api_key="reviewer-fake-key", session=session) as client:
            run = await client.debug_fetch(
                "data-go-kr-custom",
                custom_path="https://apis.data.go.kr/probe?serviceKey=reviewer-fake-key",
            )
    for value in (run.input, run.request, run.trace):
        assert "reviewer-fake-key" not in str(value)
    assert "other-inline-key" not in str(
        debug_error(TransportError("https://apis.data.go.kr/probe?serviceKey=other-inline-key"))
    )
