"""The domain value."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone

from app.status import Status


@dataclass(frozen=True, slots=True)
class WorkItem:
    """The domain record.

    frozen makes instances immutable, so a state change derives a new value instead of
    mutating a shared one — the same decision the Java module makes with a record, taken
    for the same reason. slots drops the per-instance __dict__, which costs the ability to
    add attributes at runtime and buys memory and attribute-access speed.

    The generated __init__, __repr__ and __eq__ are the point: equality is componentwise
    and nothing here is written by hand.
    """

    id: str
    title: str
    status: Status
    priority: int
    assignee: str
    created_at: datetime
    updated_at: datetime
    tags: tuple[str, ...] = field(default_factory=tuple)
    archived_at: datetime | None = None


def describe(item: WorkItem) -> str:
    """Render an item through the protocol methods rather than by poking at fields.

    format() dispatches to __format__, str() to __str__, len() to __len__ — the dunder
    methods are how a type joins the language's own vocabulary instead of requiring
    callers to learn a bespoke one. Here the tuple's __len__ and the enum's __str__ do
    the work, which is why this reads as ordinary Python rather than as an API.
    """
    return "{0.id}: {0.title} [{1}] p{0.priority} ({2} tags)".format(
        item, item.status.value, len(item.tags)
    )


def now() -> datetime:
    return datetime.now(tz=timezone.utc)


def evolve(item: WorkItem, **changes) -> WorkItem:
    """Derive a new item with some fields changed.

    dataclasses.replace calls the generated __init__ with the current field values and
    the overrides, which is the only way to "change" a frozen instance — and the reason
    frozen is worth having: nothing shares a mutable item, so no caller can be surprised.

    replace validates the field names against the generated signature, so a typo is a
    TypeError here rather than an attribute silently appearing on the copy.

    The dataclass lesson is demonstrated through this helper rather than through the
    class declaration: break a dataclass body and every fixture in the module fails to
    construct, which is a loud failure that says nothing about what actually broke.
    """
    return replace(item, **changes)


def with_status(item: WorkItem, nxt: Status, at: datetime) -> WorkItem:
    return evolve(item, status=nxt, updated_at=at)


def archived(item: WorkItem, at: datetime) -> WorkItem:
    return replace(item, archived_at=at, updated_at=at)
