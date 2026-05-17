/* knowledge_panel.js — Business Knowledge Base UI
 *
 * Depends on:  openOverlay / closeOverlay / showToast  (agent_chat.js)
 * API routes:  /api/knowledge/*  (api/knowledge.py)
 */

// ── State ─────────────────────────────────────────────────────────────────────

const _kb = {
  tab:         "metrics",
  editType:    null,
  editId:      null,
  previewRecs: [],
};

// ── Tab switching ─────────────────────────────────────────────────────────────

function kbSwitchTab(tab, btn) {
  _kb.tab = tab;
  document.querySelectorAll(".kb-tab").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  ["metrics", "rules", "notes", "import"].forEach(t => {
    const el = document.getElementById(`kb-panel-${t}`);
    if (el) el.style.display = t === tab ? "flex" : "none";
  });
  if      (tab === "metrics") kbLoadMetrics();
  else if (tab === "rules")   kbLoadRules();
  else if (tab === "notes")   kbLoadNotes();
  else if (tab === "import")  { kbResetImport(); kbLoadFiles(); }
}

// ── Load lists ────────────────────────────────────────────────────────────────

async function kbLoadMetrics() {
  const list = document.getElementById("kb-list-metrics");
  list.innerHTML = '<div class="kb-empty">加载中…</div>';
  try {
    const data = await fetch("/api/knowledge/metrics").then(r => r.json());
    const enabled = data.filter(r => r.enabled).length;
    document.getElementById("kb-metrics-count").textContent =
      `共 ${data.length} 条 · ${enabled} 条已启用`;
    list.innerHTML = data.length
      ? data.map(r => kbMetricCard(r)).join("")
      : '<div class="kb-empty">暂无指标定义</div>';
  } catch (e) {
    list.innerHTML = `<div class="kb-empty" style="color:#ef4444">加载失败: ${e.message}</div>`;
  }
}

async function kbLoadRules() {
  const list = document.getElementById("kb-list-rules");
  list.innerHTML = '<div class="kb-empty">加载中…</div>';
  try {
    const data = await fetch("/api/knowledge/rules").then(r => r.json());
    const enabled = data.filter(r => r.enabled).length;
    document.getElementById("kb-rules-count").textContent =
      `共 ${data.length} 条 · ${enabled} 条已启用`;
    list.innerHTML = data.length
      ? data.map(r => kbRuleCard(r)).join("")
      : '<div class="kb-empty">暂无业务规则</div>';
  } catch (e) {
    list.innerHTML = `<div class="kb-empty" style="color:#ef4444">加载失败: ${e.message}</div>`;
  }
}

async function kbLoadNotes() {
  const list = document.getElementById("kb-list-notes");
  list.innerHTML = '<div class="kb-empty">加载中…</div>';
  try {
    const data = await fetch("/api/knowledge/notes").then(r => r.json());
    const enabled = data.filter(r => r.enabled).length;
    document.getElementById("kb-notes-count").textContent =
      `共 ${data.length} 条 · ${enabled} 条已启用`;
    list.innerHTML = data.length
      ? data.map(r => kbNoteCard(r)).join("")
      : '<div class="kb-empty">暂无背景知识</div>';
  } catch (e) {
    list.innerHTML = `<div class="kb-empty" style="color:#ef4444">加载失败: ${e.message}</div>`;
  }
}

// ── Card renderers ────────────────────────────────────────────────────────────

function esc(s) {
  return String(s || "")
    .replace(/&/g,"&amp;").replace(/</g,"&lt;")
    .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

function kbToggleSwitch(enabled) {
  return `<div class="kb-toggle ${enabled ? 'on' : ''}" title="${enabled ? '已启用，点击禁用' : '已禁用，点击启用'}">
    <div class="kb-toggle-knob"></div>
  </div>`;
}

function kbMetricCard(r) {
  const dimmed = r.enabled ? "" : "opacity:.45;";
  return `
  <div class="kb-card" id="kbc-metrics-${r.id}" style="${dimmed}">
    <div class="kb-card-head">
      <div class="kb-card-name">
        <span class="kb-badge kb-badge-metric">指标</span>
        ${esc(r.name)}
        ${r.alias ? `<span style="font-size:12px;color:#94a3b8;font-weight:400">· ${esc(r.alias)}</span>` : ""}
      </div>
      <div class="kb-card-actions">
        <div onclick="kbToggle('metrics',${r.id})">${kbToggleSwitch(r.enabled)}</div>
        <button class="kb-act-btn" onclick="kbOpenForm('metrics',${r.id})">编辑</button>
        <button class="kb-act-btn danger" onclick="kbDelete('metrics',${r.id})">删除</button>
      </div>
    </div>
    ${r.definition  ? `<div class="kb-card-meta">${esc(r.definition)}</div>` : ""}
    ${r.sql_template? `<div class="kb-card-sql">${esc(r.sql_template)}</div>` : ""}
    ${r.notes       ? `<div class="kb-card-meta" style="color:#94a3b8;font-size:11px">备注：${esc(r.notes)}</div>` : ""}
  </div>`;
}

function kbRuleCard(r) {
  const badgeCls = r.severity === "error" ? "kb-badge-rule-error" : "kb-badge-rule-warning";
  const dimmed   = r.enabled ? "" : "opacity:.45;";
  return `
  <div class="kb-card" id="kbc-rules-${r.id}" style="${dimmed}">
    <div class="kb-card-head">
      <div class="kb-card-name">
        <span class="kb-badge ${badgeCls}">${esc(r.severity)}</span>
        ${esc(r.rule_id)}
      </div>
      <div class="kb-card-actions">
        <div onclick="kbToggle('rules',${r.id})">${kbToggleSwitch(r.enabled)}</div>
        <button class="kb-act-btn" onclick="kbOpenForm('rules',${r.id})">编辑</button>
        <button class="kb-act-btn danger" onclick="kbDelete('rules',${r.id})">删除</button>
      </div>
    </div>
    ${r.description ? `<div class="kb-card-meta">${esc(r.description)}</div>` : ""}
    ${r.condition   ? `<div class="kb-card-sql">${esc(r.condition)}</div>` : ""}
  </div>`;
}

function kbNoteCard(r) {
  const dimmed = r.enabled ? "" : "opacity:.45;";
  return `
  <div class="kb-card" id="kbc-notes-${r.id}" style="${dimmed}">
    <div class="kb-card-head">
      <div class="kb-card-name">
        <span class="kb-badge kb-badge-note">背景</span>
        ${esc(r.topic)}
        ${r.tags ? `<span style="font-size:11px;color:#94a3b8;font-weight:400">${esc(r.tags)}</span>` : ""}
      </div>
      <div class="kb-card-actions">
        <div onclick="kbToggle('notes',${r.id})">${kbToggleSwitch(r.enabled)}</div>
        <button class="kb-act-btn" onclick="kbOpenForm('notes',${r.id})">编辑</button>
        <button class="kb-act-btn danger" onclick="kbDelete('notes',${r.id})">删除</button>
      </div>
    </div>
    ${r.content ? `<div class="kb-card-meta">${esc(r.content)}</div>` : ""}
  </div>`;
}

// ── Toggle enabled ────────────────────────────────────────────────────────────

async function kbToggle(type, id) {
  try {
    const res  = await fetch(`/api/knowledge/${type}/${id}/toggle`, { method: "POST" });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "切换失败");

    // Update the card in-place without full reload
    const card = document.getElementById(`kbc-${type}-${id}`);
    if (card) {
      card.style.opacity = data.enabled ? "1" : "0.45";
      const toggleEl = card.querySelector(".kb-toggle");
      if (toggleEl) {
        toggleEl.classList.toggle("on", !!data.enabled);
        toggleEl.title = data.enabled ? "已启用，点击禁用" : "已禁用，点击启用";
      }
    }
    // Refresh the count badge
    if      (type === "metrics") kbLoadMetrics();
    else if (type === "rules")   kbLoadRules();
    else if (type === "notes")   kbLoadNotes();
  } catch (e) {
    showToast(`切换失败: ${e.message}`);
  }
}

// ── Form: open ────────────────────────────────────────────────────────────────

async function kbOpenForm(type, id = null) {
  _kb.editType = type;
  _kb.editId   = id;

  ["metrics", "rules", "notes"].forEach(t => {
    document.getElementById(`kb-fields-${t}`).style.display = t === type ? "block" : "none";
  });

  const titles = { metrics: "指标定义", rules: "业务规则", notes: "背景知识" };
  document.getElementById("kb-form-title").textContent =
    (id ? "编辑" : "新增") + titles[type];
  document.getElementById("kb-form-err").textContent = "";
  kbFormClear();

  if (id !== null) {
    try {
      const list = await fetch(`/api/knowledge/${type}`).then(r => r.json());
      const rec  = list.find(r => r.id === id);
      if (rec) kbFormFill(type, rec);
    } catch (_) {}
  }

  openOverlay("ov-kb-form");
}

function kbFormClear() {
  ["kbf-name","kbf-alias","kbf-definition","kbf-sql","kbf-notes",
   "kbf-rule-id","kbf-rule-desc","kbf-rule-cond",
   "kbf-topic","kbf-content","kbf-tags"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = "";
  });
  const sev = document.getElementById("kbf-rule-sev");
  if (sev) sev.value = "warning";
}

function kbFormFill(type, rec) {
  if (type === "metrics") {
    document.getElementById("kbf-name").value       = rec.name         || "";
    document.getElementById("kbf-alias").value      = rec.alias        || "";
    document.getElementById("kbf-definition").value = rec.definition   || "";
    document.getElementById("kbf-sql").value        = rec.sql_template || "";
    document.getElementById("kbf-notes").value      = rec.notes        || "";
  } else if (type === "rules") {
    document.getElementById("kbf-rule-id").value   = rec.rule_id      || "";
    document.getElementById("kbf-rule-desc").value = rec.description  || "";
    document.getElementById("kbf-rule-cond").value = rec.condition    || "";
    document.getElementById("kbf-rule-sev").value  = rec.severity     || "warning";
  } else if (type === "notes") {
    document.getElementById("kbf-topic").value   = rec.topic   || "";
    document.getElementById("kbf-content").value = rec.content || "";
    document.getElementById("kbf-tags").value    = rec.tags    || "";
  }
}

// ── Form: submit ──────────────────────────────────────────────────────────────

async function kbSubmitForm() {
  const type  = _kb.editType;
  const id    = _kb.editId;
  const errEl = document.getElementById("kb-form-err");
  errEl.textContent = "";

  let body = {};
  if (type === "metrics") {
    const name = document.getElementById("kbf-name").value.trim();
    if (!name) { errEl.textContent = "指标名称不能为空"; return; }
    body = {
      name,
      alias:        document.getElementById("kbf-alias").value.trim(),
      definition:   document.getElementById("kbf-definition").value.trim(),
      sql_template: document.getElementById("kbf-sql").value.trim(),
      notes:        document.getElementById("kbf-notes").value.trim(),
    };
  } else if (type === "rules") {
    const rule_id = document.getElementById("kbf-rule-id").value.trim();
    if (!rule_id) { errEl.textContent = "规则 ID 不能为空"; return; }
    body = {
      rule_id,
      description: document.getElementById("kbf-rule-desc").value.trim(),
      condition:   document.getElementById("kbf-rule-cond").value.trim(),
      severity:    document.getElementById("kbf-rule-sev").value,
    };
  } else if (type === "notes") {
    const topic = document.getElementById("kbf-topic").value.trim();
    if (!topic) { errEl.textContent = "主题不能为空"; return; }
    body = {
      topic,
      content: document.getElementById("kbf-content").value.trim(),
      tags:    document.getElementById("kbf-tags").value.trim(),
    };
  }

  const method = id ? "PUT" : "POST";
  const url    = id ? `/api/knowledge/${type}/${id}` : `/api/knowledge/${type}`;

  try {
    const res  = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) { errEl.textContent = data.error || "保存失败"; return; }

    closeOverlay("ov-kb-form");
    showToast(id ? "已更新 ✓" : "已添加 ✓");

    if      (type === "metrics") kbLoadMetrics();
    else if (type === "rules")   kbLoadRules();
    else if (type === "notes")   kbLoadNotes();
  } catch (e) {
    errEl.textContent = `请求失败: ${e.message}`;
  }
}

// ── Delete ────────────────────────────────────────────────────────────────────

async function kbDelete(type, id) {
  if (!confirm("确认删除这条记录？")) return;
  try {
    await fetch(`/api/knowledge/${type}/${id}`, { method: "DELETE" });
    showToast("已删除");
    if      (type === "metrics") kbLoadMetrics();
    else if (type === "rules")   kbLoadRules();
    else if (type === "notes")   kbLoadNotes();
  } catch (e) {
    showToast(`删除失败: ${e.message}`);
  }
}

// ── Historical source files ───────────────────────────────────────────────────

async function kbLoadFiles() {
  const list = document.getElementById("kb-files-list");
  if (!list) return;
  list.innerHTML = '<div class="kb-empty" style="padding:8px 0;font-size:12px">加载中…</div>';
  try {
    const files = await fetch("/api/knowledge/files").then(r => r.json());
    if (!files.length) {
      list.innerHTML = '<div class="kb-empty" style="padding:8px 0;font-size:12px">暂无上传记录</div>';
      return;
    }
    list.innerHTML = files.map(f => {
      const date = new Date(f.mtime * 1000).toLocaleDateString("zh-CN",
        { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
      const kb  = f.size > 1024 * 1024
        ? (f.size / 1024 / 1024).toFixed(1) + " MB"
        : Math.round(f.size / 1024) + " KB";
      return `
      <div class="kb-file-row">
        <span class="kb-file-icon">${f.filename.endsWith(".docx") ? "📝" : "📊"}</span>
        <span class="kb-file-name" title="${esc(f.filename)}">${esc(f.filename)}</span>
        <span class="kb-file-meta">${kb} · ${date}</span>
        <button class="kb-act-btn danger" style="padding:2px 7px;font-size:11px"
                onclick="kbDeleteFile('${esc(f.filename)}')">删除</button>
      </div>`;
    }).join("");
  } catch (e) {
    list.innerHTML = `<div class="kb-empty" style="color:#ef4444;font-size:12px">加载失败: ${e.message}</div>`;
  }
}

async function kbDeleteFile(filename) {
  if (!confirm(`删除文件 ${filename}？`)) return;
  try {
    await fetch(`/api/knowledge/files/${encodeURIComponent(filename)}`, { method: "DELETE" });
    showToast("文件已删除");
    kbLoadFiles();
  } catch (e) {
    showToast(`删除失败: ${e.message}`);
  }
}

// ── Import: file selection & drag-drop ────────────────────────────────────────

function kbResetImport() {
  document.getElementById("kb-parsing").style.display      = "none";
  document.getElementById("kb-preview-area").style.display = "none";
  document.getElementById("kb-import-err").textContent     = "";
  document.getElementById("kb-import-ok").textContent      = "";
  document.getElementById("kb-file-input").value           = "";
  document.getElementById("kb-drop-zone").style.display    = "flex";
  _kb.previewRecs = [];
}

function kbOnDrop(e) {
  e.preventDefault();
  document.getElementById("kb-drop-zone").classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  if (file) kbParseFile(file);
}

function kbOnFileSelect(e) {
  const file = e.target.files[0];
  if (file) kbParseFile(file);
}

document.addEventListener("DOMContentLoaded", () => {
  const zone = document.getElementById("kb-drop-zone");
  if (!zone) return;
  zone.addEventListener("dragover",  () => zone.classList.add("drag-over"));
  zone.addEventListener("dragleave", () => zone.classList.remove("drag-over"));
});

async function kbParseFile(file) {
  const ext = file.name.split(".").pop().toLowerCase();
  if (!["xlsx","xls","docx"].includes(ext)) {
    document.getElementById("kb-import-err").textContent =
      "不支持的格式，请上传 .xlsx / .xls / .docx";
    return;
  }

  document.getElementById("kb-drop-zone").style.display  = "none";
  document.getElementById("kb-parsing").style.display    = "flex";
  document.getElementById("kb-import-err").textContent   = "";
  document.getElementById("kb-import-ok").textContent    = "";

  const formData = new FormData();
  formData.append("file", file);
  const sid = (typeof SID !== "undefined" ? SID : "")
            || sessionStorage.getItem("baa_session_id") || "";
  formData.append("session_id", sid);
  // Also pass the currently selected provider so the backend uses the exact model
  const provider = document.getElementById("model-sel")?.value || "";
  if (provider) formData.append("provider", provider);

  try {
    const res  = await fetch("/api/knowledge/parse", { method: "POST", body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "解析失败");

    _kb.previewRecs = data.preview || [];
    kbRenderPreview(data);
    kbLoadFiles();   // refresh file list after upload
  } catch (e) {
    document.getElementById("kb-parsing").style.display   = "none";
    document.getElementById("kb-drop-zone").style.display = "flex";
    document.getElementById("kb-import-err").textContent  = `解析失败：${e.message}`;
  }
}

// ── Import: preview rendering ─────────────────────────────────────────────────

const _KB_TABLE_LABELS = {
  metrics:        "📐 指标",
  business_rules: "🛡 规则",
  context_notes:  "📝 背景",
};

const _KB_FIELDS_META = {
  metrics: [
    { key: "name",         label: "指标名称",  required: true  },
    { key: "alias",        label: "别名",       required: false },
    { key: "definition",   label: "定义",       required: false },
    { key: "sql_template", label: "SQL 模板",   required: false, multiline: true },
    { key: "notes",        label: "备注",       required: false },
  ],
  business_rules: [
    { key: "rule_id",     label: "规则 ID",  required: true  },
    { key: "description", label: "描述",      required: false },
    { key: "condition",   label: "违反条件",  required: false, multiline: true },
    { key: "severity",    label: "严重程度",  required: false },
  ],
  context_notes: [
    { key: "topic",   label: "主题",  required: true  },
    { key: "content", label: "内容",  required: false, multiline: true },
    { key: "tags",    label: "标签",  required: false },
  ],
};

function kbRenderPreview(data) {
  document.getElementById("kb-parsing").style.display = "none";
  const recs = _kb.previewRecs;
  const fmtLabel = data.format === "structured" ? "模板格式（直接映射）"
                 : data.format === "mixed"       ? "混合格式（部分模板 + LLM 提取）"
                 :                                 "自由文本（LLM 提取）";

  document.getElementById("kb-preview-title").textContent =
    `解析结果预览（${recs.length} 条）`;
  document.getElementById("kb-preview-sub").textContent =
    `格式：${fmtLabel}  ·  请核对后点击「全部入库」`;

  const listEl = document.getElementById("kb-preview-list");
  listEl.innerHTML = recs.length
    ? recs.map((rec, idx) => kbPreviewCard(rec, idx)).join("")
    : '<div class="kb-empty">未提取到任何知识条目</div>';

  document.getElementById("kb-preview-area").style.display = "block";
}

function kbPreviewCard(rec, idx) {
  const table  = rec.table || "metrics";
  const label  = _KB_TABLE_LABELS[table] || table;
  const fields = _KB_FIELDS_META[table]  || [];

  const fieldsHtml = fields.map(f => {
    const val = rec[f.key] || "";
    const inputEl = f.multiline
      ? `<textarea class="kb-prev-input" rows="2"
           data-idx="${idx}" data-key="${f.key}"
           oninput="kbPreviewUpdate(this)">${esc(val)}</textarea>`
      : `<input class="kb-prev-input" type="text" value="${esc(val)}"
           data-idx="${idx}" data-key="${f.key}"
           oninput="kbPreviewUpdate(this)">`;
    return `
      <div class="kb-prev-field">
        <div class="kb-prev-label">${f.label}${f.required ? " *" : ""}</div>
        ${inputEl}
      </div>`;
  }).join("");

  return `
  <div class="kb-prev-card" id="kb-prev-card-${idx}">
    <div class="kb-prev-card-head">
      <span class="kb-prev-card-type">${label}</span>
      <button class="kb-prev-delete" title="移除此条" onclick="kbPreviewRemove(${idx})">×</button>
    </div>
    <div class="kb-prev-fields">${fieldsHtml}</div>
  </div>`;
}

function kbPreviewUpdate(el) {
  const idx = parseInt(el.dataset.idx, 10);
  _kb.previewRecs[idx][el.dataset.key] = el.value;
}

function kbPreviewRemove(idx) {
  _kb.previewRecs[idx] = null;
  const card = document.getElementById(`kb-prev-card-${idx}`);
  if (card) card.style.display = "none";
  const remaining = _kb.previewRecs.filter(r => r !== null).length;
  document.getElementById("kb-preview-title").textContent =
    `解析结果预览（${remaining} 条）`;
}

function kbCancelImport() { kbResetImport(); }

// ── Import: confirm ───────────────────────────────────────────────────────────

async function kbConfirmImport() {
  const records = _kb.previewRecs.filter(r => r !== null);
  if (!records.length) {
    document.getElementById("kb-import-err").textContent = "没有可入库的记录";
    return;
  }
  const okEl  = document.getElementById("kb-import-ok");
  const errEl = document.getElementById("kb-import-err");
  okEl.textContent  = "";
  errEl.textContent = "";

  try {
    const res  = await fetch("/api/knowledge/confirm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ records }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "入库失败");

    const { inserted } = data;
    okEl.textContent =
      `✓ 入库成功：指标 ${inserted.metrics} 条，规则 ${inserted.rules} 条，背景知识 ${inserted.notes} 条`;
    _kb.previewRecs = [];
    setTimeout(() => kbResetImport(), 1800);
  } catch (e) {
    errEl.textContent = `入库失败：${e.message}`;
  }
}

// ── Init: refresh data when modal opens ──────────────────────────────────────

const _origOpenOverlay = window.openOverlay;
window.openOverlay = function(id, ...rest) {
  if (id === "ov-knowledge") {
    if      (_kb.tab === "metrics") kbLoadMetrics();
    else if (_kb.tab === "rules")   kbLoadRules();
    else if (_kb.tab === "notes")   kbLoadNotes();
    else if (_kb.tab === "import")  { kbResetImport(); kbLoadFiles(); }
  }
  if (_origOpenOverlay) _origOpenOverlay(id, ...rest);
};
