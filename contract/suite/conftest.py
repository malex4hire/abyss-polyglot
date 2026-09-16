"""Fixtures for the one contract suite.

The suite is identical for every backend. It reads a base URL from the environment and
knows nothing else about what is answering: no name, no port, no capability flag, and no
branch. That is what makes running it four times a comparison of implementations
rather than a comparison of APIs.
"""

from __future__ import annotations

import os
import uuid

import pytest
import requests

TIMEOUT = 20


@pytest.fixture(scope="session")
def base() -> str:
    url = os.environ.get("CONTRACT_BASE_URL")
    if not url:
        pytest.fail("CONTRACT_BASE_URL is not set; the suite has nothing to run against")
    return url.rstrip("/")


@pytest.fixture()
def fresh(base):
    """Create a work item the test owns, so the suite never consumes seed data.

    A suite that mutates its own fixtures passes once and fails on every rerun, which
    makes it useless as a gate.
    """
    created = []

    def make(status="OPEN", priority=4, assignee="suite", tags=("suite",)):
        item_id = f"CT-{uuid.uuid4().hex[:10]}"
        response = requests.post(f"{base}/work-items", timeout=TIMEOUT, json={
            "id": item_id, "title": f"contract {item_id}", "status": status,
            "priority": priority, "assignee": assignee, "tags": list(tags),
        })
        assert response.status_code == 201, f"create returned {response.status_code}"
        created.append(item_id)
        return response.json()["item"]

    yield make

    # Archive is a soft delete; nothing here removes a row.
    for item_id in created:
        requests.post(f"{base}/work-items/{item_id}/archive", timeout=TIMEOUT)
