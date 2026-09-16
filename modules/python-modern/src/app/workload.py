"""B3 Aggregate: per-assignee rollup over deliberately slow work."""

from __future__ import annotations

import asyncio
import functools
import time
from typing import Callable

from app.work_item import WorkItem

AUDIT: list[str] = []


def audited(label: str) -> Callable:
    """Record that a computation ran, without the computation knowing.

    A decorator is a function returning a replacement function, so the behaviour wraps
    the call rather than being written inside it — the scorer below has no logging code
    and gains an audit trail anyway. functools.wraps carries the original's name and
    docstring across, which is what stops every decorated function in a traceback being
    called "wrapper".

    It is applied at the call site rather than with @ on the definition. Decorator syntax
    runs at import time, so a failure inside one breaks the module's import and every
    test in the package with it, instead of the one test that exercises the decorator.
    """
    def decorate(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            started = time.perf_counter()
            try:
                return await fn(*args, **kwargs)
            finally:
                AUDIT.append(f"{label}:{fn.__name__}:{time.perf_counter() - started:.3f}")
        return wrapper
    return decorate


async def score_for(assignee: str, items: list[WorkItem]) -> int:
    """One assignee's score, with a deliberately slow step.

    await hands control back to the event loop while this waits, so other coroutines run
    during the pause rather than the whole program stopping. It is cooperative: nothing
    is pre-empted, and a synchronous time.sleep here would block every other coroutine —
    which is the mistake this shape exists to make visible.
    """
    await asyncio.sleep(0.05)
    return sum(item.priority for item in items)


def group_by_assignee(items: list[WorkItem]) -> dict[str, list[WorkItem]]:
    grouped: dict[str, list[WorkItem]] = {}
    for item in items:
        grouped.setdefault(item.assignee, []).append(item)
    return grouped


async def rollup(
    grouped: dict[str, list[WorkItem]],
    scorer: Callable = score_for,
) -> dict[str, int]:
    """Score every assignee concurrently.

    gather schedules all the coroutines on one event loop and waits for the set, so the
    elapsed time is the slowest rather than the sum. Results come back in the order the
    coroutines were passed, not the order they finished, which is what makes zipping them
    back to their keys safe.

    This is the Python side of the pair: one thread, cooperative scheduling. The Java
    module reaches the same shape with virtual threads and ordinary blocking calls.

    The scorer is a parameter defaulting to the real one, so a caller can supply its own.
    Production passes the default; a test of gather itself passes a trivial coroutine and
    stays independent of whatever the real scorer is doing.
    """
    names = list(grouped)
    scores = await asyncio.gather(*(scorer(name, grouped[name]) for name in names))
    return dict(zip(names, scores))
