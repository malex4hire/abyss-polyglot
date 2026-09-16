"""Executable proof that gather returns results in call order and that scheduling the
coroutines together costs the slowest rather than the sum."""

from __future__ import annotations

import asyncio

import pytest

from app.workload import group_by_assignee, rollup


@pytest.mark.async_gather
def test_results_come_back_in_call_order(sample):
    """Results zip back to their keys by position, and the waits overlap.

    A trivial scorer is supplied rather than the module's real one, so this exercises
    gather's ordering guarantee and stays independent of the coroutine being scheduled.
    """
    grouped = group_by_assignee(sample)

    async def scorer(name: str, items) -> int:
        await asyncio.sleep(0.01)
        return sum(item.priority for item in items)

    scores = asyncio.run(rollup(grouped, scorer))

    assert scores == {"avery": 5, "briar": 9, "casey": 2}
    assert list(scores) == list(grouped), "zipped back to keys by position, safely"

    # Ordering and values are identical when the same coroutines are awaited one at a
    # time, which is how a sequential counter passed. The difference gather makes is
    # elapsed time: scheduled together, the wait is the slowest rather than the sum.
    import time

    started = time.perf_counter()
    asyncio.run(rollup(grouped, scorer))
    elapsed = time.perf_counter() - started

    assert elapsed < 0.01 * len(grouped), (
        f"{len(grouped)} scorers sleeping 10ms each finished in {elapsed:.3f}s; "
        "awaited one at a time this would be their sum"
    )
