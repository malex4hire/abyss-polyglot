"""B1 Query: filter, tag containment, multi-field sort."""

from __future__ import annotations

from typing import Callable, Iterable, Protocol, TypeVar

from app.status import Status
from app.work_item import WorkItem


def matching(items: list[WorkItem], status: Status | None, tag: str | None) -> list[WorkItem]:
    """Filter by status and tag, either of which may be absent.

    The annotations are the documentation and they are checkable: `Status | None` says
    absent is expected here, so a reader knows the None branch is intentional rather than
    an oversight. Python does not enforce them at runtime. They describe intent to
    readers and to a type checker, which is exactly where the value is.
    """
    return [
        item
        for item in items
        if (status is None or item.status is status)
        # Substring across the tags rather than membership: `any(... in ...)` reads as
        # "any tag containing this", which is what a filter box means.
        and (not tag or any(tag.lower() in candidate.lower() for candidate in item.tags))
    ]


def titles_by_assignee(items: Iterable[WorkItem]) -> dict[str, list[str]]:
    """Group titles under their assignee.

    A dict comprehension over a set comprehension: the shape of the result is visible in
    the expression itself, rather than assembled by a loop whose purpose you infer from
    what it appends. Comprehensions say what the collection *is*; loops say how it is
    built.
    """
    assignees = {item.assignee for item in items}
    return {
        assignee: sorted(item.title for item in items if item.assignee == assignee)
        for assignee in sorted(assignees)
    }


class Ordered(Protocol):
    def __lt__(self, other) -> bool: ...


T = TypeVar("T", bound=Ordered)


def first_in_order(values: list[T], limit: int) -> list[T]:
    """The first `limit` values in natural order.

    The TypeVar is bound to a protocol requiring __lt__, which is what makes sorted()
    legal here and keeps the return type tied to the input's: pass a list of str and you
    get list[str] back, not list[Any]. The bound is structural, so anything comparable
    satisfies it without inheriting from anything.
    """
    return sorted(values)[: max(0, limit)]


def summarise(*items: WorkItem, **options: object) -> str:
    """Summarise any number of items, with keyword options.

    *items collects positional arguments into a tuple and **options collects keyword
    arguments into a dict, so one signature serves one item, six, or none without the
    caller building a list first. Keyword-only options are self-documenting at the call
    site, which is what stops a bare True appearing in an argument list.
    """
    separator = str(options.get("separator", ", "))
    field: Callable[[WorkItem], str] = lambda item: item.title
    if options.get("by") == "assignee":
        field = lambda item: item.assignee
    return separator.join(field(item) for item in items)
