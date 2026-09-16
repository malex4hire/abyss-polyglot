"""Executable proof that one signature serves any number of positional arguments
and any set of keyword options, with no arguments as a legal call."""

from __future__ import annotations

import pytest

from app.queries import summarise


@pytest.mark.functions_args_kwargs
def test_one_signature_serves_any_number_of_arguments(sample):
    """*args and **kwargs let one signature cover every arity and every option."""
    assert summarise(*sample) == "title-WI-1, title-WI-2, title-WI-3"
    assert summarise(*sample, separator=" | ").count("|") == 2
    assert summarise(*sample, by="assignee") == "avery, briar, casey"
    assert summarise() == "", "no arguments is a legal call, not a special case"
