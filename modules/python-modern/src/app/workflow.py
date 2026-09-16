"""B2 Transition: the state machine and its typed outcome."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.status import Status
from app.work_item import WorkItem, with_status


@dataclass(frozen=True, slots=True)
class Applied:
    item: WorkItem


@dataclass(frozen=True, slots=True)
class Rejected:
    frm: Status
    to: Status
    reason: str


TransitionResult = Applied | Rejected


def apply(item: WorkItem, nxt: Status, at: datetime) -> TransitionResult:
    """Orchestration only; the units it chains are demonstrated on their own."""
    if item.status.can_transition_to(nxt):
        return Applied(with_status(item, nxt, at))
    return Rejected(item.status, nxt, f"{item.status.value} cannot move to {nxt.value}")


def status_code_for(result: TransitionResult) -> int:
    """Turn an outcome into an HTTP status.

    Structural pattern matching destructures the value and binds its parts in the same
    breath as it matches, and the guard lets one case split on a condition without a
    nested if. This is matching on shape, not on a tag field someone has to remember to
    set — and the wildcard is the honest admission that Python cannot prove the match is
    exhaustive the way a sealed hierarchy can in Java.
    """
    match result:
        case Applied(item=item) if item.archived_at is not None:
            return 409
        case Applied():
            return 200
        case Rejected():
            return 422
        case _:
            return 500
