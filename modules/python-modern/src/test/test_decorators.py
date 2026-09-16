"""Executable proof that a decorator adds behaviour around a call the call knows
nothing about, and that functools.wraps carries the wrapped identity across."""

from __future__ import annotations

import asyncio

import pytest

from app import workload


@pytest.mark.decorators
def test_behaviour_wraps_the_call_without_the_call_knowing():
    """The wrapper records the call, the wrapped function still returns its own value.

    The decorator is applied here to a local coroutine rather than to the module's real
    scorer, so this test exercises the wrapping and nothing else. Reaching through code
    another test covers would mean a break there failed this test too.
    """
    workload.AUDIT.clear()

    @workload.audited("probe")
    async def compute(a: int, b: int) -> int:
        """Add two numbers, slowly enough to be timed."""
        await asyncio.sleep(0.01)
        return a + b

    result = asyncio.run(compute(2, 3))

    assert result == 5, "the wrapped function still returns its own value"
    assert len(workload.AUDIT) == 1, "and the wrapper recorded a call it does not implement"
    assert workload.AUDIT[0].startswith("probe:compute:")
    assert compute.__name__ == "compute", "wraps carried the identity across"
    assert compute.__doc__.startswith("Add two numbers"), "and the docstring with it"
