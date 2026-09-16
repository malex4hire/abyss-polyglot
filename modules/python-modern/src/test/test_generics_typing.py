"""Executable proof that a bounded type variable ties the return type to the input
and states, once, the capability the values must have."""

from __future__ import annotations

import pytest

from app.queries import first_in_order


@pytest.mark.generics_typing
def test_the_bound_is_what_makes_ordering_legal():
    """One function orders any comparable sequence, which is what the bound buys."""
    assert first_in_order(["gamma", "beta", "alpha"], 2) == ["alpha", "beta"]
    assert first_in_order([3, 1, 2], 5) == [1, 2, 3], "one function, any comparable"
    assert first_in_order(["a"], 0) == []


@pytest.mark.generics_typing
def test_the_return_type_is_tied_to_the_input_and_the_bound_is_stated():
    """The type variable and its bound survive to runtime, so both claims are readable.

    Filed Tier 3 with type-hints and wrong for the same reason: nothing enforces a TypeVar
    at runtime, and the program can still read it. The parameter stays on the annotation
    and its bound stays on the TypeVar, which is how a checker knows the value must be
    orderable and that what comes back matches what went in.

    The counter is this function typed with a bare list. It sorts identically, and its
    signature has stopped making either claim.
    """
    import typing

    hints = typing.get_type_hints(first_in_order)
    returned = typing.get_args(hints["return"])
    supplied = typing.get_args(hints["values"])

    assert returned and supplied, (
        f"the list is parameterised, not bare: {hints['return']}"
    )
    assert returned[0] is supplied[0], (
        "the same variable on both sides, which is what ties the return to the input"
    )
    assert returned[0].__bound__ is not None, (
        "and the variable is bounded, so the capability is proven once: "
        f"{returned[0]}"
    )
