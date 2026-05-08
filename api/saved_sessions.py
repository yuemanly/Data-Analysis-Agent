"""Blueprint: save / load / delete persistent sessions."""
import json
import os
import re
from datetime import datetime
from pathlib import Path

from flask import Blueprint, request, jsonify

from .state import session_manager, config_manager
from data.connector import ExcelDataSource, CSVDataSource

bp = Blueprint("saved_sessions", __name__)

if os.environ.get("VERCEL"):
    SAVE_DIR = Path("/tmp/outputs/Session")
else:
    SAVE_DIR = Path(__file__).parent.parent / "outputs" / "Session"

SAVE_DIR.mkdir(parents=True, exist_ok=True)


# ── helpers ────────────────────────────────────────────────────────────────

def _safe_stem(name: str) -> str:
    """Turn an arbitrary name into a filesystem-safe stem (keep CJK)."""
    name = re.sub(r'[\\/:*?"<>|]', "_", name).strip()
    return name or "session"


def _ds_info(sess) -> dict | None:
    """Serialize data source metadata for JSON storage."""
    ds = sess.data_source
    if ds is None:
        return None
    info: dict = {"display_name": ds.name, "ds_type": type(ds).__name__}
    if isinstance(ds, (ExcelDataSource, CSVDataSource)):
        info["file_path"] = ds.file_path
    return info


def _restore_ds(info: dict):
    """Re-instantiate a data source from saved metadata. Returns None on failure."""
    if not info:
        return None
    fp = info.get("file_path", "")
    if not fp or not Path(fp).exists():
        return None
    display = info.get("display_name", Path(fp).name)
    ext = Path(fp).suffix.lower()
    try:
        if info.get("ds_type") == "CSVDataSource" or ext == ".csv":
            return CSVDataSource(fp, display)
        else:
            return ExcelDataSource(fp, display)
    except Exception:
        return None


def _list_files() -> list[dict]:
    files = sorted(SAVE_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    result = []
    for f in files:
        try:
            meta = json.loads(f.read_text(encoding="utf-8"))
            result.append({
                "filename": f.name,
                "name":     meta.get("name", f.stem),
                "saved_at": meta.get("saved_at", ""),
                "msg_count": len(meta.get("history", [])),
                "ds_name":  (meta.get("data_source") or {}).get("display_name", ""),
            })
        except Exception:
            continue
    return result


# ── API endpoints ──────────────────────────────────────────────────────────

@bp.get("/api/saved-sessions")
def list_sessions():
    return jsonify(_list_files())


@bp.post("/api/session/<sid>/save")
def save_session(sid: str):
    sess = session_manager.get(sid)
    if not sess:
        return jsonify({"error": "会话不存在"}), 404
    if not sess.history:
        return jsonify({"error": "对话为空，无需保存"}), 400

    name = (request.json or {}).get("name", "").strip()
    if not name:
        name = datetime.now().strftime("对话_%Y%m%d_%H%M%S")

    payload = {
        "name":               name,
        "saved_at":           datetime.now().isoformat(timespec="seconds"),
        "model_provider":     sess.model_provider,
        "history":            sess.history,
        "total_input_tokens": sess.total_input_tokens,
        "total_output_tokens":sess.total_output_tokens,
        "data_source":        _ds_info(sess),
    }

    stem = _safe_stem(name)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = SAVE_DIR / f"{stem}_{ts}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return jsonify({"ok": True, "filename": path.name, "name": name})


@bp.post("/api/session/<sid>/load")
def load_session(sid: str):
    filename = (request.json or {}).get("filename", "").strip()
    if not filename:
        return jsonify({"error": "未指定文件名"}), 400

    path = SAVE_DIR / filename
    if not path.exists() or path.suffix != ".json":
        return jsonify({"error": "文件不存在"}), 404

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return jsonify({"error": f"读取失败: {exc}"}), 500

    sess = session_manager.get_or_create(sid)
    sess.history              = data.get("history", [])
    sess.model_provider       = data.get("model_provider", "")
    sess.total_input_tokens   = data.get("total_input_tokens", 0)
    sess.total_output_tokens  = data.get("total_output_tokens", 0)
    sess.last_prompt_tokens   = 0

    ds_info  = data.get("data_source")
    ds       = _restore_ds(ds_info)
    sess.data_source = ds

    return jsonify({
        "ok":              True,
        "name":            data.get("name", ""),
        "history":         sess.history,
        "model_provider":  sess.model_provider,
        "total_input":     sess.total_input_tokens,
        "total_output":    sess.total_output_tokens,
        "ds_connected":    ds is not None,
        "ds_name":         ds.name if ds else (ds_info or {}).get("display_name", ""),
        "ds_lost":         ds is None and ds_info is not None,
    })


@bp.delete("/api/saved-sessions/<filename>")
def delete_session(filename: str):
    path = SAVE_DIR / filename
    if not path.exists() or path.suffix != ".json":
        return jsonify({"error": "文件不存在"}), 404
    path.unlink()
    return jsonify({"ok": True})
