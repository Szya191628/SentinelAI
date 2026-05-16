"""
SSE event stream — replaces Socket.IO for real-time communication.

Publishes: console_output, forum_message, status_update
"""

import asyncio
import json
import time
from queue import Queue, Empty

from fastapi import APIRouter, Request
from starlette.responses import StreamingResponse
from loguru import logger

from app.services.event_bus import subscribe 

router = APIRouter(tags=["events"])
# 不指定队列的最大大小
queue:Queue = Queue()


# Initialize event bus forwarder
def sse_event_handler(event_type: str, data: dict):
    """将消息"""
    # TODO：这里需要做一个判断，前端需要什么类型的事件，现在是所有事件都会处理
    global queue
    payload = json.dumps({"event": event_type, "data": data}, ensure_ascii=False)
    queue.put_nowait(payload)

subscribe(sse_event_handler)


async def _event_generator(request: Request):
    """SSE event generator with keepalive."""

    logger.debug("SSE client connected")

    try:
        # Send initial connection event
        yield f"event: connected\ndata: {json.dumps({'status': 'connected'})}\n\n"

        last_event_time = time.time()
        while True:
            if await request.is_disconnected():
                break
            try:
                payload = queue.get(timeout=1)
                yield f"data: {payload}\n\n"
                last_event_time = time.time()
            except Empty:
                # Send keepalive every 15s
                if time.time() - last_event_time > 15:
                    yield f": keepalive\n\n"
                    last_event_time = time.time()
    finally:
        
        logger.debug("SSE client disconnected")


@router.get("/api/events/stream")
async def event_stream(request: Request):
    return StreamingResponse(
        _event_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
