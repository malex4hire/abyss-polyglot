"""Domain errors."""

from __future__ import annotations


class TransitionRefused(Exception):
    """Raised when the state machine refuses a move."""

    def __init__(self, frm, to) -> None:
        """Carry the data that explains the failure, not just a message.

        A named exception subclass lets a caller catch this specific failure without
        catching everything else that might go wrong — `except TransitionRefused` says
        something a bare `except ValueError` cannot.

        Attaching the states as attributes is the other half: a caller reads `frm` and
        `to` instead of parsing the message, which is what makes the failure programmable
        rather than only printable. The message is for humans and may be reworded; the
        attributes are the contract.
        """
        super().__init__(f"{frm.value} cannot move to {to.value}")
        self.frm = frm
        self.to = to
