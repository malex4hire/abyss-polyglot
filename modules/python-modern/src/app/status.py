"""Lifecycle states, and the rule that governs moving between them."""

from __future__ import annotations

from enum import Enum


class Status(Enum):
    """The work item lifecycle.

    Python enum members are instances of the class, so behaviour is ordinary method
    definition rather than anything special — which is what makes the rule below able to
    live with the data.
    """

    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    DONE = "DONE"
    CANCELLED = "CANCELLED"

    def can_transition_to(self, nxt: "Status") -> bool:
        """Whether this state may move to another.

        The rule belongs to the constant rather than to a table somewhere else, so adding
        a state cannot leave a transition map elsewhere quietly out of date. Members are
        instances, so this is an ordinary method and `self` is the constant.

        Identity comparison would work here too — enum members are singletons, which is
        why `is` is the idiomatic test for them and why a member survives a round trip
        through a name lookup unchanged.
        """
        allowed = {
            "OPEN": {"IN_PROGRESS", "CANCELLED"},
            "IN_PROGRESS": {"BLOCKED", "DONE", "CANCELLED"},
            "BLOCKED": {"IN_PROGRESS", "CANCELLED"},
            "DONE": set(),
            "CANCELLED": set(),
        }
        return nxt.value in allowed[self.value]
