"""Blueprint: conversation (SSE streaming) and chart serving."""
import json
import uuid

from flask import Blueprint, request, Response, jsonify

from .state import session_manager, config_manager, chart_store
from agent.agent import BusinessAgent

bp = Blueprint("chat", __name__)


def _build_agent(sess) -> BusinessAgent:
    provider = sess.model_provider or config_manager.get_default_provider()
    if not provider:
        raise ValueError("未配置任何 LLM 模型，请先在「模型设置」中添加模型。")
    from LLM.llm_config_manager import get_llm_client
    client = get_llm_client(provider)
    cfg = config_manager.get_config(provider)
    return BusinessAgent(
        client=client, model=cfg.model, data_source=sess.data_source,
        enable_thinking=cfg.enable_thinking,
    )


# ── Session lifecycle ──────────────────────────────────────────────────────

@bp.post("/api/session/new")
def new_session():
    sess = session_manager.create()
    return jsonify({"session_id": sess.session_id})


@bp.post("/api/session/<sid>/clear")
def clear_history(sid: str):
    session_manager.get_or_create(sid).clear_history()
    return jsonify({"ok": True})


# ── Chart serving ──────────────────────────────────────────────────────────

@bp.get("/api/chart/<chart_id>")
def serve_chart(chart_id: str):
    html = chart_store.get(chart_id)
    if not html:
        return "Chart not found", 404
    return Response(html, mimetype="text/html")


# ── Chat SSE ───────────────────────────────────────────────────────────────

@bp.post("/api/session/<sid>/chat")
def chat_stream(sid: str):
    d = request.json or {}
    message = (d.get("message") or "").strip()
    command = (d.get("command") or "").strip()
    if not message:
        return jsonify({"error": "消息不能为空"}), 400

    sess = session_manager.get_or_create(sid)

    def generate():
        collected: list[str] = []

        try:
            agent = _build_agent(sess)
        except ValueError as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return

        for event in agent.run(message, list(sess.history), command=command):
            etype = event.get("type")

            if etype == "chart_html":
                cid = uuid.uuid4().hex
                chart_store[cid] = event["html"]
                yield f"data: {json.dumps({'type': 'chart_ref', 'chart_id': cid})}\n\n"
            elif etype == "chart_placeholder":
                pass   # internal signal, not forwarded
            elif etype == "usage":
                # Record in session and enrich with context_window before forwarding
                sess.record_usage(
                    event.get("prompt_tokens", 0),
                    event.get("completion_tokens", 0),
                )
                cfg = config_manager.get_config(sess.model_provider)
                enriched = {
                    **event,
                    "context_window": cfg.context_window if cfg else None,
                    "max_output_tokens": cfg.max_output_tokens if cfg else None,
                    "session_total_input": sess.total_input_tokens,
                    "session_total_output": sess.total_output_tokens,
                }
                yield f"data: {json.dumps(enriched)}\n\n"
            else:
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            if etype == "text":
                collected.append(event.get("content", ""))

        sess.add_user(message)
        sess.add_assistant("".join(collected))

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )
