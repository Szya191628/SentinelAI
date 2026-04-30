"""App management routes — forum engine start/stop and status."""

from datetime import datetime

from fastapi import APIRouter, HTTPException

from services.system_service import (
    _forum_status,
    read_log_from_file, write_log_to_file,
)
from services.forum_service import start_forum_engine, stop_forum_engine

router = APIRouter(tags=["apps"])


@router.get("/api/status")
def get_status():
    return {"forum": {"status": _forum_status.get("status", "stopped"), "port": None}}


@router.get("/api/start/{app_name}")
def start_app(app_name: str):
    if app_name == "forum":
        try:
            start_forum_engine()
            _forum_status["status"] = "running"
            return {"success": True, "message": "ForumEngine已启动"}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))
    raise HTTPException(status_code=400, detail=f"未知应用: {app_name} (支持: forum)")


@router.get("/api/stop/{app_name}")
def stop_app(app_name: str):
    if app_name == "forum":
        try:
            stop_forum_engine()
            _forum_status["status"] = "stopped"
            return {"success": True, "message": "ForumEngine已停止"}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))
    raise HTTPException(status_code=400, detail=f"未知应用: {app_name} (支持: forum)")


@router.get("/api/output/{app_name}")
def get_output(app_name: str):
    if app_name == "forum":
        forum_log = read_log_from_file("forum")
        return {"success": True, "output": forum_log, "total_lines": len(forum_log)}
    raise HTTPException(status_code=400, detail=f"未知应用: {app_name}")
