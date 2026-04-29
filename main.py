"""FastAPI main application — primary backend (Phase 3)."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from loguru import logger

from services.forum_service import init_forum_log, start_forum_log_monitor
from utils.knowledge_logger import init_knowledge_log

from routers import system, config, apps, forum, search, graph, events, report


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    init_forum_log()
    init_knowledge_log()
    start_forum_log_monitor()
    logger.info("FastAPI 服务器已启动，共享服务已初始化")
    yield


app = FastAPI(
    title="尚舆分析平台 API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(system.router)
app.include_router(config.router)
app.include_router(apps.router)
app.include_router(forum.router)
app.include_router(search.router)
app.include_router(graph.router)
app.include_router(events.router)
app.include_router(report.router)

# ── SPA & static files ──────────────────────────────────────────────────

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_STATIC_DIR = Path(__file__).resolve().parent / "static"
_INDEX_HTML = _TEMPLATE_DIR / "index.html"


@app.get("/", response_class=HTMLResponse)
async def serve_spa():
    """Serve the SPA entry point."""
    if _INDEX_HTML.exists():
        return HTMLResponse(content=_INDEX_HTML.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>尚舆分析平台</h1>", status_code=200)


@app.get("/graph-viewer")
@app.get("/graph-viewer/")
@app.get("/graph-viewer/{report_id}")
async def serve_graph_viewer(report_id: str = None):
    """Serve graph viewer page."""
    graph_html = _TEMPLATE_DIR / "graph_viewer.html"
    if graph_html.exists():
        return HTMLResponse(content=graph_html.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Graph Viewer</h1>", status_code=200)


if __name__ == "__main__":
    import uvicorn
    from config import settings

    host = settings.HOST
    port = settings.PORT

    logger.info(f"FastAPI 主服务器启动: http://{host}:{port}")

    if settings.FLASK_ENABLED:
        import threading
        from app import app as flask_app

        def _run_flask():
            flask_app.run(host=host, port=5001, debug=False, use_reloader=False)

        t = threading.Thread(target=_run_flask, daemon=True)
        t.start()
        logger.info(f"Flask 辅助服务器启动: http://{host}:5001")

    uvicorn.run(app, host=host, port=port, log_level="info")
