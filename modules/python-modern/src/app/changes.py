"""B4: the change stream, on the stdlib HTTP server.

No language lesson is claimed here. Server-sent events on this stack are HTTP plumbing — a
header, a held socket, a flushed line — and `io` belongs to the framework modules, so
claiming it as a Python fundamental would blur the split this module sits on. The stack
serves the endpoint for contract parity and says nothing more.

ThreadingHTTPServer gives each request its own thread, so a held stream is a parked thread.
That is the honest cost of this shape here, and it is the same tradeoff the Java module
makes cheaper with virtual threads.
"""
from __future__ import annotations

import json
import threading

_LOCK = threading.Lock()
_SUBSCRIBERS: list = []


def subscribe(handler) -> None:
    """Hold the connection open until the client drops it."""
    handler.send_response(200)
    handler.send_header("Content-Type", "text/event-stream")
    handler.send_header("Cache-Control", "no-cache")
    handler.send_header("Connection", "keep-alive")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()

    stream = handler.wfile
    with _LOCK:
        _SUBSCRIBERS.append(stream)
    try:
        stream.write(b": open\n\n")
        stream.flush()
        stop = threading.Event()
        while not stop.wait(15):
            stream.write(b": keep-alive\n\n")
            stream.flush()
    except (BrokenPipeError, ConnectionResetError, ValueError):
        pass
    finally:
        with _LOCK:
            if stream in _SUBSCRIBERS:
                _SUBSCRIBERS.remove(stream)


def emit(kind: str, item_id: str) -> None:
    """Announce a change. A dead subscriber is dropped rather than retried."""
    frame = f"event: change\ndata: {json.dumps({'kind': kind, 'id': item_id})}\n\n".encode()
    with _LOCK:
        for stream in list(_SUBSCRIBERS):
            try:
                stream.write(frame)
                stream.flush()
            except (BrokenPipeError, ConnectionResetError, ValueError):
                _SUBSCRIBERS.remove(stream)
