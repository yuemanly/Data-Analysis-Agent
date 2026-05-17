# -*- coding: utf-8 -*-
"""Blueprint: business knowledge base — parse, preview, confirm, CRUD, toggle."""
import logging
import uuid
from pathlib import Path

from flask import Blueprint, request, jsonify, send_from_directory

from .state import session_manager, config_manager

log = logging.getLogger(__name__)
bp = Blueprint("knowledge", __name__)

# ── Directory: uploads/knowledge/  (relative to project root) ────────────────
# This file lives at <root>/api/knowledge.py → parent = api/ → parent = root
_PROJECT_ROOT = Path(__file__).parent.parent
_KB_DIR = _PROJECT_ROOT / "uploads" / "knowledge"
_ALLOWED_EXTS = {".xlsx", ".xls", ".docx"}


def _ensure_dir() -> None:
    _KB_DIR.mkdir(parents=True, exist_ok=True)


def _kb():
    from Function.Knowledge.knowledge_base import KnowledgeBase
    return KnowledgeBase()


def _get_client(sid: str, provider: str = ""):
    """Return (client, model_name) for the given session.

    Priority:
      1. explicit provider passed from the request (frontend model-sel value)
      2. provider stored on the session (set via POST /api/session/<sid>/model)
      3. global default provider from config
    """
    if not provider:
        sess = session_manager.get_or_create(sid)
        provider = getattr(sess, "model_provider", None) or ""
    if not provider:
        provider = config_manager.get_default_provider() or ""
    if not provider:
        raise ValueError("未配置任何 LLM 模型，请先在「模型设置」中添加模型。")
    from LLM.llm_config_manager import get_llm_client
    client = get_llm_client(provider)
    cfg = config_manager.get_config(provider)
    log.info("[knowledge] using provider=%s model=%s for LLM extraction", provider, cfg.model)
    return client, cfg.model


# ── File parse → preview ──────────────────────────────────────────────────────

@bp.post("/api/knowledge/parse")
def parse_file():
    """Upload docx/xlsx, keep the file in uploads/knowledge/, return preview."""
    _ensure_dir()

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    f = request.files["file"]
    sid = request.form.get("session_id", "")
    provider = request.form.get("provider", "")
    original_name = f.filename or "upload"
    ext = Path(original_name).suffix.lower()

    if ext not in _ALLOWED_EXTS:
        return jsonify({"error": f"不支持的文件格式 {ext}，请上传 .xlsx / .xls / .docx"}), 400

    # Keep original filename; prepend uuid prefix to avoid collisions
    safe_stem = "".join(c if c.isalnum() or c in "-_." else "_"
                        for c in Path(original_name).stem)[:60]
    filename = f"{uuid.uuid4().hex[:8]}_{safe_stem}{ext}"
    save_path = _KB_DIR / filename
    f.save(str(save_path))

    try:
        client, model = _get_client(sid, provider=provider)
        from Function.Knowledge.file_parser import parse_file as _parse
        result = _parse(str(save_path), client, model)
        result["filename"] = filename          # let frontend reference the file
        return jsonify(result)
    except Exception as e:
        log.exception("Knowledge parse failed")
        msg = str(e)
        if "JSONDecodeError" in type(e).__name__ or (msg.startswith(('"', "'")) and len(msg) < 80):
            msg = "LLM 返回格式异常，无法解析。请检查模型是否正常，或尝试重新上传。"
        return jsonify({"error": msg}), 500


# ── List uploaded source files ────────────────────────────────────────────────

@bp.get("/api/knowledge/files")
def list_files():
    """Return metadata of all uploaded source files in uploads/knowledge/."""
    _ensure_dir()
    files = []
    for p in sorted(_KB_DIR.iterdir(), key=lambda f: f.stat().st_mtime, reverse=True):
        if p.suffix.lower() in _ALLOWED_EXTS:
            files.append({
                "filename": p.name,
                "size":     p.stat().st_size,
                "mtime":    p.stat().st_mtime,
            })
    return jsonify(files)


@bp.delete("/api/knowledge/files/<filename>")
def delete_file(filename: str):
    """Delete a source file from uploads/knowledge/."""
    # Security: strip any path separators
    filename = Path(filename).name
    target = _KB_DIR / filename
    if not target.exists():
        return jsonify({"error": "File not found"}), 404
    target.unlink()
    return jsonify({"ok": True})


# ── Confirm → bulk insert ─────────────────────────────────────────────────────

@bp.post("/api/knowledge/confirm")
def confirm_records():
    body = request.get_json(silent=True) or {}
    records = body.get("records", [])
    if not records:
        return jsonify({"error": "No records provided"}), 400
    try:
        counts = _kb().bulk_insert(records)
        return jsonify({"ok": True, "inserted": counts})
    except Exception as e:
        log.exception("Knowledge confirm failed")
        return jsonify({"error": str(e)}), 500


# ── Toggle enabled ────────────────────────────────────────────────────────────

@bp.post("/api/knowledge/metrics/<int:mid>/toggle")
def toggle_metric(mid: int):
    rec = _kb().get_metric_by_id(mid)
    if not rec:
        return jsonify({"error": "Not found"}), 404
    updated = _kb().update_metric(mid, enabled=0 if rec["enabled"] else 1)
    return jsonify(updated)


@bp.post("/api/knowledge/rules/<int:rid>/toggle")
def toggle_rule(rid: int):
    rec = _kb().get_rule_by_id(rid)
    if not rec:
        return jsonify({"error": "Not found"}), 404
    updated = _kb().update_rule(rid, enabled=0 if rec["enabled"] else 1)
    return jsonify(updated)


@bp.post("/api/knowledge/notes/<int:nid>/toggle")
def toggle_note(nid: int):
    rec = _kb().get_note_by_id(nid)
    if not rec:
        return jsonify({"error": "Not found"}), 404
    updated = _kb().update_note(nid, enabled=0 if rec["enabled"] else 1)
    return jsonify(updated)


# ── Metrics CRUD ──────────────────────────────────────────────────────────────

@bp.get("/api/knowledge/metrics")
def list_metrics():
    return jsonify(_kb().list_metrics())


@bp.post("/api/knowledge/metrics")
def add_metric():
    body = request.get_json(silent=True) or {}
    try:
        record = _kb().add_metric(
            name=body.get("name", ""),
            alias=body.get("alias", ""),
            definition=body.get("definition", ""),
            sql_template=body.get("sql_template", ""),
            notes=body.get("notes", ""),
        )
        return jsonify(record), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.put("/api/knowledge/metrics/<int:mid>")
def update_metric(mid: int):
    body = request.get_json(silent=True) or {}
    record = _kb().update_metric(mid, **body)
    if record is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify(record)


@bp.delete("/api/knowledge/metrics/<int:mid>")
def delete_metric(mid: int):
    _kb().delete_metric(mid)
    return jsonify({"ok": True})


# ── Business rules CRUD ───────────────────────────────────────────────────────

@bp.get("/api/knowledge/rules")
def list_rules():
    return jsonify(_kb().list_rules())


@bp.post("/api/knowledge/rules")
def add_rule():
    body = request.get_json(silent=True) or {}
    try:
        record = _kb().add_rule(
            rule_id=body.get("rule_id", ""),
            description=body.get("description", ""),
            condition=body.get("condition", ""),
            severity=body.get("severity", "warning"),
        )
        return jsonify(record), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.put("/api/knowledge/rules/<int:rid>")
def update_rule(rid: int):
    body = request.get_json(silent=True) or {}
    record = _kb().update_rule(rid, **body)
    if record is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify(record)


@bp.delete("/api/knowledge/rules/<int:rid>")
def delete_rule(rid: int):
    _kb().delete_rule(rid)
    return jsonify({"ok": True})


# ── Context notes CRUD ────────────────────────────────────────────────────────

@bp.get("/api/knowledge/notes")
def list_notes():
    return jsonify(_kb().list_notes())


@bp.post("/api/knowledge/notes")
def add_note():
    body = request.get_json(silent=True) or {}
    try:
        record = _kb().add_note(
            topic=body.get("topic", ""),
            content=body.get("content", ""),
            tags=body.get("tags", ""),
        )
        return jsonify(record), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.put("/api/knowledge/notes/<int:nid>")
def update_note(nid: int):
    body = request.get_json(silent=True) or {}
    record = _kb().update_note(nid, **body)
    if record is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify(record)


@bp.delete("/api/knowledge/notes/<int:nid>")
def delete_note(nid: int):
    _kb().delete_note(nid)
    return jsonify({"ok": True})


# ── Search ────────────────────────────────────────────────────────────────────

@bp.get("/api/knowledge/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"metrics": [], "rules": [], "notes": []})
    return jsonify(_kb().search(q))
