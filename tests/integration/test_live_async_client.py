"""공개 native async 클라이언트에서 실제 목록·상세·디버그를 검증한다."""

import os

import pytest

from krheritage import HeritageClient

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(os.getenv("KHERITAGE_RUN_LIVE") != "1", reason="live opt-in required"),
]


async def test_live_public_async_client_list_detail_and_debug():
    async with HeritageClient(max_rps=2) as client:
        page = await client.search.list(page_size=1)
        assert page.total > 1000
        assert page.items
        summary = page.items[0]
        detail = await client.heritage.details(
            summary.key.ccba_kdcd, summary.key.ccba_asno, summary.key.ccba_ctcd
        )
        assert detail.key == summary.key
        assert detail.name_ko == summary.name_ko
        run = await client.debug_fetch("khs-search-list", {"pageUnit": "1", "pageIndex": "1"})
        assert run.error is None
        assert run.processed
