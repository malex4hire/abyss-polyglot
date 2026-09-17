"""The HTTP surface: http.server from the standard library, no framework."""

from __future__ import annotations

import asyncio
import json
import os
import platform
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from app import packaging, queries, workload
from app.errors import TransitionRefused
from app.repository import Repository, load_seed
from app import changes
from app.status import Status
from app.work_item import WorkItem, archived, describe
from app.workflow import Applied, Rejected, apply, status_code_for

REPO = Repository()


def _json_default(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Status):
        return value.value
    if isinstance(value, tuple):
        return list(value)
    raise TypeError(type(value))


def _as_dict(item: WorkItem) -> dict:
    return {
        "id": item.id, "title": item.title, "status": item.status.value,
        "priority": item.priority, "assignee": item.assignee,
        "createdAt": item.created_at, "updatedAt": item.updated_at,
        "tags": list(item.tags), "archivedAt": item.archived_at,
    }


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args) -> None:  # quieter container logs
        pass

    def _send(self, code: int, payload) -> None:
        body = json.dumps(payload, default=_json_default).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if not _method_guard(self, "GET"):
            return
        url = urlparse(self.path)
        params = {k: v[0] for k, v in parse_qs(url.query).items()}
        try:
            if url.path == "/health":
                self._send(200, {
                    "status": "UP",
                    "items": REPO.size(),
                    "modules": packaging.own_modules(),
                    "sample": describe(REPO.live()[0]) if REPO.live() else "",
                })
            elif url.path == "/__instrumentation/identity":
                self._send(200, {
                    "runtime_version": ".".join(map(str, sys.version_info[:3])),
                    # The build string, which names the compiler and the build date
                    # as well as the version. The tuple above stays the field the
                    # floor is compared against, because it is the parseable one.
                    "runtime_version_exact": sys.version.split("\n")[0].strip(),
                    "runtime_vendor": platform.python_implementation(),
                    "http_server_class": f"{ThreadingHTTPServer.__module__}.{ThreadingHTTPServer.__name__}",
                    # Name and version, not name alone: java-modern's classpath entries
                    # carry their version in the jar filename by construction, and an
                    # artifact list that cannot say which release resolved gives the
                    # runtime-identity check nothing to compare across backends.
                    "artifacts": sorted(
                        f"{d.metadata['Name']}=={d.version}"
                        for d in __import__("importlib.metadata", fromlist=["x"]).distributions()
                        if d.metadata.get("Name")
                    ),
                })
            elif url.path == "/events":
                # B4. Held open on this request's thread; nothing below this line runs
                # until the client goes away.
                changes.subscribe(self)
            elif url.path == "/work-items":
                status = Status(params["status"]) if params.get("status") else None
                found = queries.matching(REPO.live(), status, params.get("tag"))
                found.sort(key=lambda item: (-item.priority, item.title))
                self._send(200, {"items": [_as_dict(i) for i in found]})
            elif url.path == "/workload":
                grouped = workload.group_by_assignee(REPO.live())
                # The audit wrapper is applied here, on the request path, rather than with
                # @ on the definition: decorator syntax runs at import.
                traced = workload.audited("workload")(workload.score_for)
                self._send(200, {"byAssignee": asyncio.run(workload.rollup(grouped, traced))})
            elif url.path.startswith("/work-items/") and url.path.count("/") == 2:
                item = REPO.get(url.path.rsplit("/", 1)[1])
                if item is None:
                    self._send(404, {"error": "no such work item",
                                     "id": url.path.rsplit("/", 1)[1]})
                else:
                    # Archived items resolve. Archive is a soft delete, so the list is the
                    # active view and this addresses the record.
                    self._send(200, {"item": _as_dict(item)})
            else:
                self._send(404, {"error": "no such path", "path": url.path})
        except (KeyError, ValueError) as exc:
            self._send(400, {"error": "bad request", "detail": str(exc)})

    def do_POST(self) -> None:
        if not _method_guard(self, "POST"):
            return
        url = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw or b"{}")
            if url.path == "/work-items":
                at = datetime.now(tz=timezone.utc)
                # B5. The key is the row's identity, so it is checked before anything is
                # built. An absent or blank key is a row nobody can address.
                key = payload.get("id")
                if not isinstance(key, str) or not key.strip():
                    self._send(400, {"error": "id is required", "field": "id"})
                    return
                item = WorkItem(
                    id=key, title=payload["title"],
                    status=Status(payload["status"]), priority=int(payload["priority"]),
                    assignee=payload["assignee"], created_at=at, updated_at=at,
                    tags=tuple(payload.get("tags", ())), archived_at=None)
                # The outcome comes from the write, not from a lookup before it.
                existing = REPO.put_if_absent(item)
                if existing is not None:
                    # Nothing written, so nothing announced and nothing claiming 201.
                    self._send(200, {"item": _as_dict(existing)})
                    return
                changes.emit("created", item.id)
                self._send(201, {"item": _as_dict(item)})
                return

            parts = url.path.strip("/").split("/")
            if len(parts) == 3 and parts[0] == "work-items":
                item = REPO.get(parts[1])
                if item is None:
                    self._send(404, {"error": "no such work item", "id": parts[1]})
                    return
                if parts[2] == "archive":
                    REPO.put(archived(item, datetime.now(tz=timezone.utc)))
                    changes.emit("archived", item.id)
                    self._send(200, {"archived": item.id})
                    return
                if parts[2] == "transition":
                    nxt = Status(payload["status"])
                    # B5. Already there is not an illegal move, it is a move that has
                    # happened, which is what a retry of a dropped response is asking.
                    # Only the self-edge changes; every genuine refusal still refuses.
                    if item.status is nxt:
                        self._send(200, {"item": _as_dict(item)})
                        return
                    result = apply(item, nxt, datetime.now(tz=timezone.utc))
                    code = status_code_for(result)
                    match result:
                        case Applied(item=moved):
                            # Compare and set against the status the decision was made on.
                            stored = REPO.replace_if_status_is(item.id, item.status, moved)
                            if stored is None:
                                now = REPO.get(item.id) or moved
                                self._send(200, {"item": _as_dict(now)})
                                return
                            changes.emit("transitioned", moved.id)
                            self._send(code, {"item": _as_dict(moved)})
                        case Rejected(frm=frm, to=to, reason=reason):
                            refused = TransitionRefused(frm, to)
                            self._send(code, {"rejected": {
                                "id": item.id, "to": to.value, "reason": str(refused)}})
                    return
            self._send(404, {"error": "no such path", "path": url.path})
        except (KeyError, ValueError, TypeError) as exc:
            self._send(400, {"error": "bad request", "detail": str(exc)})


def _unsupported(method: str):
    """One handler per verb this server does not implement, so the answer is about the
    path rather than about the server. Absent these, the base class replies 501."""
    def handler(self) -> None:
        _method_guard(self, method)
    return handler


for _verb in ("DELETE", "PUT", "PATCH", "HEAD"):
    setattr(Handler, f"do_{_verb}", _unsupported(_verb))


def serve() -> None:
    for item in load_seed(datetime.now(tz=timezone.utc)):
        REPO.put(item)
    port = int(os.environ.get("PORT", "8080"))
    ThreadingHTTPServer(("", port), Handler).serve_forever()


def _allowed_for(path: str) -> set[str]:
    """The methods each shape answers to, stated once.

    Without this, an unsupported method falls through to BaseHTTPRequestHandler's default
    501 (a claim about the whole server rather than about this path), and carries no Allow
    header, so a client is told "no" and not "what instead".
    """
    parts = path.split("/")
    if path in ("/health", "/workload", "/events") or path.startswith("/__instrumentation"):
        return {"GET"}
    if path == "/work-items":
        return {"GET", "POST"}
    if len(parts) == 3 and parts[1] == "work-items" and parts[2]:
        return {"GET"}
    if len(parts) == 4 and parts[1] == "work-items" and parts[3] in ("archive", "transition"):
        return {"POST"}
    return set()


def _method_guard(handler, method: str) -> bool:
    """True when the request may proceed; otherwise the response has been sent."""
    path = urlparse(handler.path).path
    allowed = _allowed_for(path)
    if not allowed:
        handler._send(404, {"error": "no such path", "path": path})
        return False
    if method not in allowed:
        handler.send_response(405)
        handler.send_header("Allow", ", ".join(sorted(allowed)))
        handler.send_header("Content-Type", "application/json")
        body = json.dumps({"error": "method not allowed", "path": path,
                           "method": method, "allowed": sorted(allowed)}).encode()
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)
        return False
    return True
