"""Executable proof that awaiting hands control back to the event loop rather than
blocking. Measured, because the returned values look the same either way."""

from __future__ import annotations

import pytest

import asyncio
import time

from app.workload import score_for


@pytest.mark.async_await
def test_awaiting_yields_control_rather_than_blocking(sample):
    """Two 50ms waits overlap, so the pair costs about one of them."""
    async def both():
        return await asyncio.gather(score_for("a", sample), score_for("b", sample))

    started = time.perf_counter()
    scores = asyncio.run(both())
    elapsed = time.perf_counter() - started

    assert scores == [16, 16]
    assert elapsed < 0.09, f"two 50ms waits overlapped: {elapsed:.3f}s"


@pytest.mark.async_await
def test_awaiting_hands_control_back_so_coroutines_overlap(sample):
    """Two coroutines together cost about what one costs; blocking would cost both.

    A coroutine with a blocking sleep in place of the await returns the same score after
    the same delay, so every assertion about the value passes, which is how a counter
    passed. The only thing await does is hand control back to the event loop, and that is
    observable exactly once: when two of them run together.
    """
    import asyncio
    import time

    async def one():
        return await score_for("avery", sample)

    async def both():
        return await asyncio.gather(
            score_for("avery", sample),
            score_for("briar", sample),
        )

    # Measured, not assumed. The first version pinned a millisecond figure guessed from
    # the source and failed against correct code, the same defect as a check asserting a
    # jar count it wrote down. One call establishes the unit; two concurrent calls have to
    # cost close to one, and blocking instead of awaiting costs two.
    started = time.perf_counter()
    asyncio.run(one())
    single = time.perf_counter() - started

    started = time.perf_counter()
    asyncio.run(both())
    together = time.perf_counter() - started

    assert together < single * 1.6, (
        f"one coroutine took {single:.3f}s and two took {together:.3f}s; overlapping "
        "costs about one, blocking costs both while returning identical scores"
    )
