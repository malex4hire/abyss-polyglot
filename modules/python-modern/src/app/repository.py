"""Storage. In-memory, seeded at startup, mirroring the other backends."""

from __future__ import annotations

import csv
from collections import OrderedDict
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from app.status import Status
from app.work_item import WorkItem

SEED = Path(__file__).resolve().parent / "seed.csv"


class Repository:
    def __init__(self) -> None:
        self._items: OrderedDict[str, WorkItem] = OrderedDict()

    def put(self, item: WorkItem) -> None:
        self._items[item.id] = item

    def put_if_absent(self, item: WorkItem) -> WorkItem | None:
        """B5. Store only if the key is free; return the incumbent when it is not.

        setdefault decides and writes in one call, so the outcome comes from the write
        rather than from a lookup that a second request could invalidate before the store.
        """
        existing = self._items.setdefault(item.id, item)
        return None if existing is item else existing

    def replace_if_status_is(self, item_id: str, expected, nxt: WorkItem) -> WorkItem | None:
        """B5. Compare and set: the status the decision was made against is the
        precondition of the write, so a concurrent move is not silently overwritten."""
        current = self._items.get(item_id)
        if current is None or current.status is not expected:
            return None
        self._items[item_id] = nxt
        return nxt

    def get(self, item_id: str) -> WorkItem | None:
        return self._items.get(item_id)

    def size(self) -> int:
        return len(self._items)

    def live(self) -> list[WorkItem]:
        """Every unarchived item, in insertion order.

        OrderedDict because iteration order is part of this endpoint's contract. A plain
        dict preserves insertion order in modern Python too, but stating it here says the
        ordering is relied upon rather than incidental — and move_to_end and the
        order-sensitive equality come with it if they are ever needed.

        The returned list is a new list, so a caller cannot reach back through it into
        the store.
        """
        return [item for item in self._items.values() if item.archived_at is None]

    def pages(self, size: int, items: list[WorkItem] | None = None) -> Iterator[list[WorkItem]]:
        """Yield successive pages rather than building every page at once.

        A generator produces values on demand and holds one page in memory instead of
        all of them. The caller can stop early — break out of the loop — and the work for
        the remaining pages is never done. That laziness is the whole difference from
        returning a list of lists.
        """
        page: list[WorkItem] = []
        for item in (self.live() if items is None else items):
            page.append(item)
            if len(page) == size:
                yield page
                page = []
        if page:
            yield page

    @contextmanager
    def batch(self) -> Iterator[list[WorkItem]]:
        """Collect writes and apply them on a clean exit.

        The code before yield is setup, the code after is teardown, and the teardown runs
        whether the block returns or raises — that is what a context manager buys over a
        pair of calls the caller must remember to pair. Here an exception escaping the
        block means the staged writes are dropped rather than half-applied.
        """
        staged: list[WorkItem] = []
        try:
            yield staged
        except Exception:
            staged.clear()
            raise
        else:
            for item in staged:
                self.put(item)


def load_seed(now: datetime) -> list[WorkItem]:
    """Read the seed file. Identical data to every other backend."""
    loaded: list[WorkItem] = []
    with SEED.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            tags = tuple(t.strip() for t in row["tags"].split(";") if t.strip())
            loaded.append(WorkItem(
                id=row["id"], title=row["title"], status=Status(row["status"]),
                priority=int(row["priority"]), assignee=row["assignee"],
                created_at=now, updated_at=now, tags=tags, archived_at=None))
    return loaded
