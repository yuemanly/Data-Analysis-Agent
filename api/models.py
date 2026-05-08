"""Blueprint: LLM model management — /api/models/*"""
from flask import Blueprint, request, jsonify
from .state import config_manager, session_manager

bp = Blueprint("models", __name__)


@bp.get("/api/models")
def list_models():
    return jsonify(config_manager.list_configs())


@bp.get("/api/models/defaults")
def model_defaults():
    return jsonify({
        k: {
            "base_url": v["base_url"],
            "model": v["model"],
            "context_window": v.get("context_window"),
            "max_output_tokens": v.get("max_output_tokens"),
        }
        for k, v in config_manager.DEFAULT_CONFIGS.items()
    })


@bp.post("/api/models/set-builtin")
def set_builtin():
    d = request.json or {}
    provider = d.get("provider", "").strip()
    api_key  = d.get("api_key", "").strip()
    base_url = d.get("base_url", "").strip() or None
    model    = d.get("model", "").strip() or None
    context_window    = _to_int(d.get("context_window"))
    max_output_tokens = _to_int(d.get("max_output_tokens"))
    enable_thinking   = bool(d.get("enable_thinking", False))
    if not provider or not api_key:
        return jsonify({"error": "provider 和 api_key 不能为空"}), 400
    ok = config_manager.set_config(
        provider, api_key, base_url=base_url, model=model,
        context_window=context_window, max_output_tokens=max_output_tokens,
        enable_thinking=enable_thinking,
    )
    if ok:
        return jsonify({"ok": True})
    return jsonify({"error": f"不支持的内置提供商: {provider}"}), 400


@bp.post("/api/models/clear-builtin")
def clear_builtin():
    d = request.json or {}
    ok, msg = config_manager.clear_builtin_config(d.get("provider", "").strip())
    return jsonify({"ok": ok, "message": msg})


@bp.post("/api/models/add")
def add_model():
    d = request.json or {}
    ok, msg = config_manager.add_custom_model(
        name=d.get("name", ""),
        base_url=d.get("base_url", ""),
        model_name=d.get("model_name", ""),
        api_key=d.get("api_key", ""),
        context_window=_to_int(d.get("context_window")),
        max_output_tokens=_to_int(d.get("max_output_tokens")),
        enable_thinking=bool(d.get("enable_thinking", False)),
    )
    if ok:
        return jsonify({"ok": True, "message": msg})
    return jsonify({"error": msg}), 400


def _to_int(v) -> int | None:
    try:
        return int(v) if v not in (None, "", "0") else None
    except (TypeError, ValueError):
        return None


@bp.post("/api/models/delete")
def delete_model():
    d = request.json or {}
    ok, msg = config_manager.delete_config(d.get("provider", "").strip())
    if ok:
        return jsonify({"ok": True, "message": msg})
    return jsonify({"error": msg}), 400


@bp.post("/api/models/test")
def test_model():
    d = request.json or {}
    return jsonify(config_manager.test_config(d.get("provider", "")))


@bp.post("/api/session/<sid>/model")
def set_session_model(sid: str):
    d = request.json or {}
    provider = d.get("provider", "").strip()
    if not config_manager.get_config(provider):
        return jsonify({"error": f"未知的模型: {provider}"}), 400
    sess = session_manager.get_or_create(sid)
    sess.model_provider = provider
    return jsonify({"ok": True})
