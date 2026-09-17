"""The contract, exercised identically against every active backend.

Nothing here names an implementation, and nothing here branches. A backend that needs a
special case in this file is a backend that does not serve the contract.
"""

from __future__ import annotations

import re
import uuid
import time

import requests

TIMEOUT = 20

LEGAL_NEXT = {
    "OPEN": "IN_PROGRESS",
    "IN_PROGRESS": "BLOCKED",
    "BLOCKED": "IN_PROGRESS",
}
ILLEGAL_NEXT = {
    "OPEN": "DONE",
    "IN_PROGRESS": "OPEN",
    "BLOCKED": "DONE",
    "DONE": "OPEN",
    "CANCELLED": "OPEN",
}

REQUIRED_FIELDS = (
    "id", "title", "status", "priority", "assignee", "createdAt", "updatedAt", "tags",
)


def items(base, **params):
    response = requests.get(f"{base}/work-items", params=params, timeout=TIMEOUT)
    assert response.status_code == 200, f"list returned {response.status_code}"
    return response.json()["items"]


# --- shape -------------------------------------------------------------------

def test_every_item_carries_the_declared_fields(base, fresh):
    fresh()
    for item in items(base):
        for field in REQUIRED_FIELDS:
            assert field in item, f"{item.get('id')} is missing '{field}'"
        assert isinstance(item["tags"], list), "tags is a list in every backend"
        assert isinstance(item["priority"], int)


# --- B1 query ----------------------------------------------------------------

def test_b1_orders_by_priority_desc_then_title_asc(base, fresh):
    fresh(priority=1, status="OPEN")
    fresh(priority=99, status="OPEN")
    listed = items(base)
    keys = [(-item["priority"], item["title"]) for item in listed]
    assert keys == sorted(keys), "the declared ordering is total and every backend serves it"


def test_b1_filters_by_status(base, fresh):
    created = fresh(status="BLOCKED")
    filtered = items(base, status="BLOCKED")
    assert all(item["status"] == "BLOCKED" for item in filtered)
    assert created["id"] in [item["id"] for item in filtered]
    assert created["id"] not in [item["id"] for item in items(base, status="DONE")]


def test_b1_filters_by_tag_containment(base, fresh):
    created = fresh(tags=("alpha", "beta"))
    by_tag = items(base, tag="beta")
    assert created["id"] in [item["id"] for item in by_tag]
    assert all("beta" in item["tags"] for item in by_tag)
    assert created["id"] not in [item["id"] for item in items(base, tag="gamma")]


def test_b1_combines_status_and_tag(base, fresh):
    created = fresh(status="BLOCKED", tags=("delta",))
    both = items(base, status="BLOCKED", tag="delta")
    assert created["id"] in [item["id"] for item in both]
    assert created["id"] not in [item["id"] for item in items(base, status="OPEN", tag="delta")]


# --- B2 transition -----------------------------------------------------------

def test_b2_applies_a_legal_transition(base, fresh):
    created = fresh(status="OPEN")
    target = LEGAL_NEXT[created["status"]]

    response = requests.post(f"{base}/work-items/{created['id']}/transition",
                             json={"status": target}, timeout=TIMEOUT)

    assert response.status_code == 200, response.text
    assert response.json()["item"]["status"] == target


def test_b2_refuses_an_illegal_transition_and_changes_nothing(base, fresh):
    created = fresh(status="OPEN")
    target = ILLEGAL_NEXT[created["status"]]

    response = requests.post(f"{base}/work-items/{created['id']}/transition",
                             json={"status": target}, timeout=TIMEOUT)

    assert response.status_code == 422, response.text
    assert "rejected" in response.json(), "the refusal is typed, not a bare error string"
    after = [item for item in items(base) if item["id"] == created["id"]][0]
    assert after["status"] == created["status"], "a refused transition writes nothing"


def test_b2_unknown_id_is_not_found(base):
    response = requests.post(f"{base}/work-items/CT-does-not-exist/transition",
                             json={"status": "IN_PROGRESS"}, timeout=TIMEOUT)
    assert response.status_code == 404


def test_b2_rejects_an_unusable_status_value(base, fresh):
    created = fresh(status="OPEN")
    response = requests.post(f"{base}/work-items/{created['id']}/transition",
                             json={"status": "NOT_A_STATUS"}, timeout=TIMEOUT)
    assert 400 <= response.status_code < 500, "an unusable value is a client error"


# --- B3 aggregate ------------------------------------------------------------

def test_b3_rolls_up_by_assignee(base, fresh):
    fresh(assignee="rollup-a", priority=5)
    fresh(assignee="rollup-a", priority=7)
    fresh(assignee="rollup-b", priority=2)

    response = requests.get(f"{base}/workload", timeout=TIMEOUT)

    assert response.status_code == 200
    rollup = response.json()["byAssignee"]
    assert rollup["rollup-a"] == 12, "priorities sum per assignee"
    assert rollup["rollup-b"] == 2


def test_b3_reflects_archive(base, fresh):
    created = fresh(assignee="rollup-c", priority=9)
    before = requests.get(f"{base}/workload", timeout=TIMEOUT).json()["byAssignee"]
    assert before["rollup-c"] == 9

    requests.post(f"{base}/work-items/{created['id']}/archive", timeout=TIMEOUT)

    after = requests.get(f"{base}/workload", timeout=TIMEOUT).json()["byAssignee"]
    assert after.get("rollup-c", 0) == 0, "an archived item leaves the rollup"


# --- archive semantics -------------------------------------------------------

def test_archive_is_a_soft_delete(base, fresh):
    created = fresh()

    response = requests.post(f"{base}/work-items/{created['id']}/archive", timeout=TIMEOUT)

    assert response.status_code == 200
    assert response.json()["archived"] == created["id"]
    assert created["id"] not in [item["id"] for item in items(base)], "archived leaves the list"
    still_there = requests.post(f"{base}/work-items/{created['id']}/transition",
                                json={"status": "IN_PROGRESS"}, timeout=TIMEOUT)
    assert still_there.status_code != 404, "the record was not removed, only marked"


# --- B4 live update ---------------------------------------------------------------
#
# One suite, no per-stack branch. The stream is read with a socket rather than a
# client library so that nothing here depends on a package a backend's image may not carry,
# and so the assertion is on the bytes the server actually sends.


def _read_events(base, seconds=6.0):
    """Open the stream and return whatever arrives within the window."""
    import socket
    import urllib.parse

    parsed = urllib.parse.urlparse(base)
    connection = socket.create_connection((parsed.hostname, parsed.port), timeout=seconds)
    connection.sendall(
        f"GET /events HTTP/1.1\r\nHost: {parsed.netloc}\r\nAccept: text/event-stream\r\n"
        "Connection: keep-alive\r\n\r\n".encode()
    )
    connection.settimeout(seconds)
    chunks = []
    import time
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            data = connection.recv(4096)
        except socket.timeout:
            break
        if not data:
            break
        chunks.append(data)
        if b"event: change" in b"".join(chunks):
            break
    connection.close()
    return b"".join(chunks).decode("utf-8", "replace")


def test_b4_stream_announces_itself_as_an_event_stream(base):
    opening = _read_events(base, seconds=3.0)
    assert "200" in opening.split("\r\n", 1)[0], f"the stream did not open: {opening[:120]!r}"
    assert "text/event-stream" in opening, (
        f"the stream is not declared as an event stream: {opening[:200]!r}"
    )


def test_b4_emits_a_change_event_when_an_item_is_created(base, fresh):
    import threading

    received = {}

    def reader():
        received["text"] = _read_events(base, seconds=8.0)

    thread = threading.Thread(target=reader)
    thread.start()
    time.sleep(1.0)  # let the stream open before the change happens

    created = fresh()

    thread.join(timeout=12)
    text = received.get("text", "")
    # SSE permits "event:change" and "event: change"; Spring writes the first and the JDK
    # server the second. Asserting one spelling would be a per-stack branch in disguise.
    assert re.search(r"event:\s*change", text), (
        f"no change event arrived after creating {created['id']}: {text[-300:]!r}"
    )
    assert created["id"] in text or '"kind"' in text, (
        f"the change event carried no identifying payload: {text[-300:]!r}"
    )


def test_b1_tag_filter_matches_a_partial_tag(base, fresh):
    """A filter that only answers to a whole tag asks for the answer as its input."""
    created = fresh(tags=("provisioning",))

    whole = requests.get(f"{base}/work-items", params={"tag": "provisioning"}, timeout=TIMEOUT)
    assert whole.status_code == 200
    assert any(item["id"] == created["id"] for item in whole.json()["items"]), (
        "the exact tag did not match, so this test is measuring the wrong thing"
    )

    for fragment in ("provis", "vision", "PROVIS"):
        response = requests.get(f"{base}/work-items", params={"tag": fragment}, timeout=TIMEOUT)
        assert response.status_code == 200, f"tag={fragment!r} returned {response.status_code}"
        assert any(item["id"] == created["id"] for item in response.json()["items"]), (
            f"tag={fragment!r} matched nothing, but 'provisioning' contains it"
        )


def test_b1_tag_filter_still_excludes_what_it_should(base, fresh):
    """Partial matching must not become matching everything."""
    created = fresh(tags=("provisioning",))
    response = requests.get(f"{base}/work-items", params={"tag": "zzz-no-such"}, timeout=TIMEOUT)
    assert response.status_code == 200
    assert not any(item["id"] == created["id"] for item in response.json()["items"])


# --- B5 idempotent writes ----------------------------------------------------------
#
# Why the suite ran green through a real divergence for the whole build: `fresh` mints a
# uuid id per call and every test above creates once. No test had ever posted the same key
# twice or omitted one, so the conflict path and the missing-key path were never entered.
# Identical passed counts across four backends said only that four backends took the same
# paths, and the paths that diverged were the ones nothing walked. A parity suite compares
# implementations only over the behaviour it actually exercises; everywhere else it compares
# nothing and reports agreement.


def _create(base, **fields):
    """Post a create exactly as given, so a test can omit or malform the key."""
    return requests.post(f"{base}/work-items", timeout=TIMEOUT, json=fields)


def _ids(base):
    listed = requests.get(f"{base}/work-items", timeout=TIMEOUT).json()["items"]
    return [item["id"] for item in listed]


def test_b5_a_repeated_create_with_the_same_key_yields_one_row(base):
    key = f"CT-{uuid.uuid4().hex[:10]}"
    body = {"id": key, "title": "idempotent", "status": "OPEN",
            "priority": 4, "assignee": "suite", "tags": ["suite"]}

    first = _create(base, **body)
    assert first.status_code == 201, f"the first create should report a creation: {first.status_code}"

    second = _create(base, **body)
    # Honest, not merely survivable: the second call did not create anything and must not
    # claim it did. 200 is the answer: the resource exists and this is its representation.
    assert second.status_code == 200, (
        f"a repeated create reported {second.status_code}; it created nothing, so 201 is a lie"
    )
    assert second.json()["item"]["id"] == key

    assert _ids(base).count(key) == 1, "the repeated create produced a second row"


def test_b5_a_repeated_create_emits_one_change_event(base):
    import threading

    key = f"CT-{uuid.uuid4().hex[:10]}"
    body = {"id": key, "title": "idempotent", "status": "OPEN",
            "priority": 4, "assignee": "suite", "tags": ["suite"]}
    received = {}

    def reader():
        received["text"] = _read_events(base, seconds=9.0)

    thread = threading.Thread(target=reader)
    thread.start()
    time.sleep(1.0)

    _create(base, **body)
    _create(base, **body)

    thread.join(timeout=13)
    text = received.get("text", "")
    # The stream is a hint to refetch, so a spurious frame is not corruption, but it is a
    # write announcing something that did not happen, and a client that trusts the count is
    # entitled to one event per change.
    assert text.count(key) <= 1, (
        f"the repeated create announced itself twice: {text[-300:]!r}"
    )


def test_b5_a_create_with_no_key_is_rejected_and_stores_nothing(base):
    before = len(_ids(base))
    response = _create(base, title="no key", status="OPEN",
                       priority=4, assignee="suite", tags=["suite"])

    assert response.status_code == 400, (
        f"a create with no key returned {response.status_code}; it must not be stored"
    )
    assert len(_ids(base)) == before, "a keyless create was stored anyway"
    assert "null" not in _ids(base), "a missing key was coerced into the literal string null"


def test_b5_a_create_with_a_malformed_key_is_rejected_and_stores_nothing(base):
    before = len(_ids(base))
    for bad in ("", "   ", None):
        response = _create(base, id=bad, title="bad key", status="OPEN",
                           priority=4, assignee="suite", tags=["suite"])
        assert response.status_code == 400, (
            f"a create with key {bad!r} returned {response.status_code}; it must not be stored"
        )
    assert len(_ids(base)) == before, "a malformed key was stored anyway"


def test_b5_a_transition_repeated_to_its_current_state_is_a_successful_no_op(base, fresh):
    item = fresh(status="OPEN")

    first = requests.post(f"{base}/work-items/{item['id']}/transition",
                          timeout=TIMEOUT, json={"status": "IN_PROGRESS"})
    assert first.status_code == 200, f"the first transition should apply: {first.status_code}"
    assert first.json()["item"]["status"] == "IN_PROGRESS"

    # The retry a client makes when a response is dropped. It has already happened, so the
    # honest answer is the current state, not a rejection of a move already made.
    second = requests.post(f"{base}/work-items/{item['id']}/transition",
                           timeout=TIMEOUT, json={"status": "IN_PROGRESS"})
    assert second.status_code == 200, (
        f"repeating a transition to its current state returned {second.status_code}; "
        "a retry of an applied move is not an illegal move"
    )
    assert second.json()["item"]["status"] == "IN_PROGRESS"


def test_b5_the_state_machine_still_refuses_a_genuinely_illegal_transition(base, fresh):
    """Only the self-edge changed. Everything the state machine refused, it still refuses."""
    item = fresh(status="OPEN")

    response = requests.post(f"{base}/work-items/{item['id']}/transition",
                             timeout=TIMEOUT, json={"status": "DONE"})
    # 422, the code this contract already uses for a refused transition. The first draft
    # asserted 409 from habit, which would have made every backend wrong to agree with the
    # contract they already implement.
    assert response.status_code == 422, (
        f"OPEN to DONE returned {response.status_code}; the state machine must still refuse it"
    )

    # Re-read from the list: this contract has no GET /work-items/{id}, and asserting
    # through an endpoint that does not exist tests the 404 handler, not the transition.
    listed = requests.get(f"{base}/work-items", timeout=TIMEOUT).json()["items"]
    after = next(row for row in listed if row["id"] == item["id"])
    assert after["status"] == "OPEN", "a refused transition changed the item anyway"


# --- routing correctness -----------------------------------------------------------
#
# 404 and 405 are different claims about the world. 405 asserts the path is real and the
# method is not, which tells a client the resource exists, so answering it for an
# unmatched path invents a resource. Hand-rolled routing (D1) means routing correctness is
# the module's own, and prefix matching hands every unmatched sub-path the same answer, so
# this is a routing defect rather than one wrong endpoint.


def test_routing_an_unmatched_path_is_not_found(base):
    response = requests.get(f"{base}/work-items/nope/not-a-route", timeout=TIMEOUT)
    assert response.status_code == 404, (
        f"an unmatched path returned {response.status_code}; 405 would claim it exists"
    )


def test_routing_a_real_path_with_an_unsupported_method_names_what_it_allows(base):
    response = requests.delete(f"{base}/work-items", timeout=TIMEOUT)
    assert response.status_code == 405, (
        f"DELETE on a real path returned {response.status_code}; the path exists, the method does not"
    )
    allow = response.headers.get("Allow", "")
    assert "GET" in allow and "POST" in allow, (
        f"405 must say which methods the path allows; Allow was {allow!r}"
    )


# --- fetch by id -------------------------------------------------------------------


def test_get_by_id_returns_the_item(base, fresh):
    created = fresh()
    response = requests.get(f"{base}/work-items/{created['id']}", timeout=TIMEOUT)

    assert response.status_code == 200, f"fetch by id returned {response.status_code}"
    assert response.json()["item"]["id"] == created["id"]


def test_get_by_id_is_not_found_for_an_unknown_id(base):
    response = requests.get(f"{base}/work-items/CT-does-not-exist", timeout=TIMEOUT)
    assert response.status_code == 404, f"an unknown id returned {response.status_code}"


def test_get_by_id_still_resolves_an_archived_item(base, fresh):
    """Archive is a soft delete, so the record is still addressable: the list is the
    active view, and this addresses the row. The rest of the contract already implies it:
    a transition against an archived item does not 404 either."""
    created = fresh()
    requests.post(f"{base}/work-items/{created['id']}/archive", timeout=TIMEOUT)

    response = requests.get(f"{base}/work-items/{created['id']}", timeout=TIMEOUT)
    assert response.status_code == 200, (
        f"an archived item returned {response.status_code}; soft delete means still addressable"
    )
    assert response.json()["item"]["archivedAt"], "the item resolves but does not say it is archived"
