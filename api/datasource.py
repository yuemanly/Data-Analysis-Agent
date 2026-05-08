"""Blueprint: data source management — upload Excel/CSV, connect SQL DB."""
import uuid
from pathlib import Path

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

from .state import session_manager
from data.connector import ExcelDataSource, CSVDataSource, SQLDataSource
import os
from pathlib import Path

bp = Blueprint("datasource", __name__)

# 自动识别环境，Vercel 用 /tmp，本地用项目目录
if os.environ.get("VERCEL"):
    UPLOAD_DIR = Path("/tmp/uploads")
else:
    UPLOAD_DIR = Path(__file__).parent.parent / "uploads"

UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_EXTS = {".xlsx", ".xls", ".csv"}


def _allowed(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTS


@bp.post("/api/session/<sid>/upload")
def upload_file(sid: str):
    if "file" not in request.files:
        return jsonify({"error": "未选择文件"}), 400
    f = request.files["file"]
    if not f.filename or not _allowed(f.filename):
        return jsonify({"error": "仅支持 .xlsx / .xls / .csv 文件"}), 400

    display_name = f.filename  # keep original (may contain CJK/unicode)
    ext = Path(f.filename).suffix.lower()
    safe_stem = secure_filename(f.filename)
    safe_name = (safe_stem if safe_stem else f"upload_{uuid.uuid4().hex[:8]}{ext}")
    save_path = UPLOAD_DIR / f"{sid[:8]}_{uuid.uuid4().hex[:6]}_{safe_name}"
    f.save(str(save_path))

    try:
        if ext == ".csv":
            source = CSVDataSource(str(save_path), display_name)
        else:
            source = ExcelDataSource(str(save_path), display_name)

        sess = session_manager.get_or_create(sid)
        sess.data_source = source
        return jsonify({"ok": True, "source_name": display_name,
                        "schema_preview": source.get_schema()})
    except Exception as exc:
        return jsonify({"error": f"文件解析失败: {exc}"}), 400


@bp.post("/api/session/<sid>/connect-db")
def connect_db(sid: str):
    d = request.json or {}
    conn_str     = (d.get("connection_string") or "").strip()
    display_name = (d.get("name") or "").strip()
    if not conn_str:
        return jsonify({"error": "连接字符串不能为空"}), 400
    try:
        source = SQLDataSource(conn_str, display_name)
        sess = session_manager.get_or_create(sid)
        sess.data_source = source
        return jsonify({"ok": True, "source_name": source.name,
                        "schema_preview": source.get_schema()})
    except Exception as exc:
        return jsonify({"error": f"数据库连接失败: {exc}"}), 400


@bp.delete("/api/session/<sid>/datasource")
def disconnect_source(sid: str):
    sess = session_manager.get_or_create(sid)
    sess.data_source = None
    return jsonify({"ok": True})
