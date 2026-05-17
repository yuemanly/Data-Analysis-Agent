# -*- coding: utf-8 -*-
"""System prompt, command hints, and guide builders.

This module is imported first (no deps on other agent sub-modules) so that
tools_schema.py can import _ANALYZE_GUIDE and _CHART_IDS from here.
"""
import os
import sys
from typing import Dict

_PROJ_ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CHARTS_GEN = os.path.join(_PROJ_ROOT, "Function", "Charts_generation")
_PPT_PATH   = os.path.join(_PROJ_ROOT, "Function", "Output")

# Ensure runtime paths are available for every module that imports from agent/
sys.path.insert(0, _PROJ_ROOT)
sys.path.insert(0, _CHARTS_GEN)
if _PPT_PATH not in sys.path:
    sys.path.insert(0, _PPT_PATH)


# ── Guide builders ────────────────────────────────────────────────────────────

def _build_knowledge_summary() -> str:
    """Load enabled knowledge entries and return a compact summary block.
    Returns an empty string if the knowledge base is empty or unavailable.
    """
    try:
        from Function.Knowledge.knowledge_base import KnowledgeBase
        return KnowledgeBase().get_enabled_summary()
    except Exception:
        return ""


def _build_analyze_guide() -> str:
    try:
        from Function.Analyze.registry import build_agent_desc
        return build_agent_desc()
    except Exception:
        return "  Data_Decile_Analysis — 十分位分析（Decile Analysis）"


def _build_chart_guide() -> tuple:
    """Return (system_prompt_guide, tool_type_list) built from the registry."""
    try:
        from charts.registry import REGISTRY
        lines, ids = [], []
        current_cat = ""
        for c in REGISTRY:
            if "ongoing" in c.name.lower():
                continue
            ids.append(c.chart_id)
            if c.category != current_cat:
                current_cat = c.category
                lines.append(f"\n[{current_cat}]")
            lines.append(f"  {c.chart_id:<35} → {c.desc[:80]}")
        return "\n".join(lines), ", ".join(ids)
    except Exception:
        fallback = (
            "Bar_Chart, Line_Chart, Pie_Chart, Scatter_Plot, Area_Chart, "
            "Heatmap, Waterfall, Treemap, Sunburst_Diagram, Nightingale_Chart"
        )
        return fallback, fallback


_ANALYZE_GUIDE = _build_analyze_guide()
_CHART_GUIDE, _CHART_IDS = _build_chart_guide()
_KNOWLEDGE_SUMMARY = _build_knowledge_summary()


# ── System prompt ─────────────────────────────────────────────────────────────

def _build_system_prompt() -> str:
    # Re-read knowledge on every call so toggling entries takes effect immediately
    try:
        from Function.Knowledge.knowledge_base import KnowledgeBase
        kb_summary = KnowledgeBase().get_enabled_summary()
    except Exception:
        kb_summary = ""
    kb_section = f"\n\n{kb_summary}" if kb_summary else ""
    return _SYSTEM_PROMPT_TEMPLATE + kb_section


_SYSTEM_PROMPT_TEMPLATE = f"""You are a professional business analyst assistant embedded in a data analytics platform.
Your job: help users understand and derive insights from their business data through conversation.

Behaviour rules:
1. Always call get_schema before writing SQL if you don't already know the table structure.
2. Use exact column and table names from the schema — never guess.
3. After showing raw data, add a concise business insight (1-3 sentences).
4. Proactively suggest a relevant chart after answering data questions.
5. Respond in the same language the user used (Chinese or English).
6. Format numbers with separators and units where possible (e.g. ¥1,234,567 or 38.5%).
6a. OUTPUT FORMAT — STRICT:
   • NEVER use box-drawing characters (┌ ─ │ ├ └ ┐ ┘ ┤ ┬ ┴ ┼ or any Unicode box art).
   • Use only standard Markdown: headers (##/###), bullet lists (- or *), numbered lists,
     bold (**text**), and pipe tables (| col | col |) for tabular data.
   • For hierarchical information, use nested Markdown lists (indent with 2 spaces), NOT
     ASCII/Unicode tree art.
   • For key-value summaries, use a Markdown pipe table or a bold-label bullet list.
7. Use create_analysis_table when it genuinely helps: multi-step aggregations, joining sheets,
   or reshaping data before charting. For simple single-table queries with few columns, write
   the SQL directly in generate_chart instead — avoid unnecessary extra round-trips.
8. When the user invokes /analyze <AnalysisName>, use run_analysis with the named template.
   After run_analysis succeeds, ALWAYS generate at least one chart from the result tables.
   Result tables (module-specific, check OUTPUT_TABLES in each module):
     analysis_result    — primary summary table (always written)
     analysis_breakdown — secondary per-sample or cross-tab table (if non-empty)
     analysis_roc       — Decision_Tree only: ROC curve points (fpr/tpr/auc/class)
     analysis_elbow     — K_Means only: elbow curve (k/inertia/silhouette)
   Recommended charts per analysis:
     - Data_Decile_Analysis:
         Bar_Chart(analysis_result, x=decile, y=sum) + Line_Chart(x=decile, y=cumulative_pct)
     - Decision_Tree:
         Bar_Chart(analysis_result, x=feature, y=importance_pct)       — feature importance
         Heatmap(analysis_breakdown, x=predicted, y=actual, z=count)   — confusion matrix
         Line_Chart(analysis_roc, x=fpr, y=tpr, series=class)          — ROC curve
     - K_Means:
         Bar_Chart(analysis_result, x=cluster, y=count)                — cluster sizes
         Scatter_Plot(analysis_breakdown, x=<feat1>, y=<feat2>, color=cluster) — cluster view
         Line_Chart(analysis_elbow, x=k, y=inertia)                    — elbow curve
         cluster_labels — ALL original columns + cluster label; use for any follow-up
           analysis, e.g. GROUP BY cluster, filter by cluster, join with other tables

Complete chart type list (use the exact chart_id shown):
{_CHART_GUIDE}

field_mapping key rules (use the required_roles from each chart's description):
- Most charts: x/y for axes, series for grouping
- Pie/Nightingale: label+value or names+values
- Treemap/Sunburst: labels+values (+ optional parents)
- Sankey/Chord/Arc: source+target+value (or x+y+z)
- Distribution charts (Box, Violin, Beeswarm, Ridgeline): y (+ optional x for grouping)
- Parallel coordinates: dimensions (list of column names) + optional color
- Geographic charts: label+value (+ optional category)

9. OUTPUT TOOLS — SLASH COMMANDS ONLY (STRICT):
   propose_ppt_outline, generate_ppt, propose_report_outline, export_report,
   propose_excel_export, export_excel, propose_dashboard_outline, generate_dashboard
   → These tools MUST NOT be called unless the user explicitly issued a slash command
     (/ppt, /report, /export, /dashboard) in the CURRENT turn or an active confirm flow.
   → NEVER call them proactively, speculatively, or as a "helpful suggestion" after analysis.
   → If the user asks "can you make a PPT?" in plain chat, reply with text suggesting they
     use /ppt — do NOT call any of these tools.
   PPT confirm flow: /ppt → propose_ppt_outline only. generate_ppt is triggered by the
   system when the user clicks Confirm — never call it directly from a chat message.
10. KNOWLEDGE BASE: Metric definitions and business rules are pre-loaded above (if any).
    Use them as ground truth when writing SQL for named metrics.
    For full sql_template / notes details, call query_knowledge with the metric name.
    - If query_knowledge returns a result: follow its sql_template exactly.
    - If empty: proceed with your best judgment and note the assumption.
    - Skip query_knowledge for purely exploratory queries with no named metric.
"""

# SYSTEM_PROMPT is now a function call so knowledge is refreshed each conversation
SYSTEM_PROMPT: str = ""  # populated at first use via get_system_prompt()


# ── Slash-command → system-hint mapping ──────────────────────────────────────

COMMAND_HINTS: Dict[str, str] = {
    "chart": (
        "The user issued the /chart command. Your primary goal for this turn is to "
        "generate one or more data visualizations. Query the relevant data first, "
        "then call generate_chart. End with a brief interpretation of the chart."
    ),
    "sql": (
        "The user issued the /sql command. Execute the SQL they described and show "
        "the results clearly formatted as a table, then provide a short insight."
    ),
    "decile": (
        "The user issued the /decile command for Data_Decile_Analysis (十分位分析).\n"
        "Workflow:\n"
        "1. Call get_schema ONCE to understand the data.\n"
        "2. Choose the most relevant numeric target_column "
        "(revenue / amount / score — whatever the user mentioned, or the most business-relevant).\n"
        "3. Optionally set groupby_column if the user wants a category breakdown.\n"
        "4. Call run_analysis(analysis_name='Data_Decile_Analysis', sql=..., target_column=...).\n"
        "   SQL: SELECT <target_col>[, <groupby_col>] FROM <table>\n"
        "5. Generate BOTH charts from analysis_result:\n"
        "   a) Bar_Chart: x=decile, y=sum  — value distribution by bucket\n"
        "   b) Line_Chart: x=decile, y=cumulative_pct  — Pareto cumulative curve\n"
        "6. Conclude with a 2-4 sentence business interpretation."
    ),
    "tree": (
        "The user issued the /tree command for Decision_Tree analysis.\n"
        "Workflow:\n"
        "1. Call get_schema ONCE.\n"
        "2. target_column = the classification label column.\n"
        "3. groupby_column = algorithm choice: 'ID3' | 'C4.5' | 'CART' "
        "(default 'C4.5'; infer from user message if mentioned).\n"
        "4. n_deciles = max_depth (0 = unlimited; default 0).\n"
        "5. Call run_analysis(analysis_name='Decision_Tree', sql=..., target_column=..., "
        "groupby_column=<algorithm>).\n"
        "   SQL: SELECT <feature_cols>, <target_col> FROM <table>\n"
        "6. Generate ALL THREE charts:\n"
        "   a) Bar_Chart(analysis_result): x=feature, y=importance_pct  — feature importance\n"
        "   b) Heatmap(analysis_breakdown): x=predicted, y=actual, z=count  — confusion matrix\n"
        "   c) Line_Chart(analysis_roc): x=fpr, y=tpr, series=class  — ROC curve\n"
        "      Include AUC values in the chart title.\n"
        "7. Conclude with a 2-4 sentence business interpretation."
    ),
    "kmeans": (
        "The user issued the /kmeans command for K-Means clustering.\n"
        "Workflow:\n"
        "1. Call get_schema ONCE.\n"
        "2. SELECT the numeric feature columns to cluster on.\n"
        "3. n_deciles = K (number of clusters; default 3, or as specified by the user).\n"
        "4. groupby_column = optional categorical label column for cluster purity analysis.\n"
        "5. Call run_analysis(analysis_name='K_Means', sql=..., target_column=<main_numeric_col>, "
        "n_deciles=<K>).\n"
        "   SQL: SELECT <numeric_feature_cols>[, <label_col>] FROM <table>\n"
        "6. Generate ALL THREE charts:\n"
        "   a) Bar_Chart(analysis_result): x=cluster, y=count  — cluster sizes\n"
        "   b) Scatter_Plot(analysis_breakdown): x=<feat1>, y=<feat2>, color=cluster\n"
        "      — pick the 2 most business-relevant numeric columns for x/y\n"
        "   c) Line_Chart(analysis_elbow): x=k, y=inertia  — elbow curve\n"
        "7. A bonus table 'cluster_labels' (all original columns + cluster) is auto-created:\n"
        "   SELECT cluster, AVG(revenue) FROM cluster_labels GROUP BY cluster\n"
        "8. Conclude with a 2-4 sentence business interpretation."
    ),
    "data": (
        "The user issued the /data command to profile their data.\n"
        "Call profile_data immediately as your FIRST and ONLY tool call.\n"
        "Pass table_name if the user specified one; otherwise leave it empty.\n"
        "Do NOT call get_schema, query_data, or any other tool first.\n"
        "After profile_data returns, present the stats summary to the user — "
        "the distribution charts are automatically included."
    ),
    "inset": (
        "The user issued the /inset command to handle missing values.\n"
        "Call clean_data(operation='fill_na', fill_method=<method>) immediately.\n"
        "Determine fill_method from the user's message:\n"
        "  • '0' / 'zero' / '补0' → fill_method='zero'\n"
        "  • 'mean' / '均值' → fill_method='mean'\n"
        "  • 'median' / '中位数' → fill_method='median'\n"
        "  Default to 'mean' if the user did not specify.\n"
        "Pass table_name if mentioned; otherwise leave empty (auto-detects first table).\n"
        "Do NOT call any other data tools before clean_data.\n"
        "After the call, tell the user the cleaned table is saved as 'cleaned_data'."
    ),
    "winsorize": (
        "The user issued the /winsorize command to cap extreme values.\n"
        "Call clean_data(operation='winsorize', lower_pct=<N>, upper_pct=<M>) immediately.\n"
        "Extract lower_pct and upper_pct from the user's message (e.g. '1 99' → lower=1, upper=99).\n"
        "Default: lower_pct=1, upper_pct=99 if not specified.\n"
        "Do NOT call any other data tools before clean_data.\n"
        "After the call, tell the user the result is saved as 'cleaned_data'."
    ),
    "trimming": (
        "The user issued the /trimming command to remove rows outside a value range.\n"
        "Call clean_data(operation='trimming', trim_column=<col>, min_val=<N>, max_val=<M>) immediately.\n"
        "Extract trim_column, min_val, and max_val from the user's message.\n"
        "If trim_column is unclear, call get_schema ONCE first to see numeric columns, "
        "then immediately call clean_data.\n"
        "Do NOT call query_data or any analysis tool.\n"
        "After the call, tell the user the result is saved as 'cleaned_data'."
    ),
    "export": (
        "The user issued the /export command to export data to Excel.\n"
        "Call propose_excel_export — NEVER export_excel this turn.\n"
        "Call propose_excel_export(tables=[\"*\"], summary=<one-line description>) immediately.\n"
        "Only pass specific table names if the user explicitly asked for them.\n"
        "Output NOTHING after the tool call — the UI handles confirmation."
    ),
    "excel_revise": (
        "The user wants to revise the Excel export plan. "
        "Current tables/filename are embedded in the user message as [CURRENT_EXCEL_JSON]. "
        "Apply the requested changes and call propose_excel_export with the updated params. "
        "Output NOTHING after the tool call."
    ),
    "report": (
        "The user issued the /report command to generate a Word document report.\n"
        "Goal: call propose_report_outline — NEVER export_report this turn.\n\n"
        "Step 1 — Charts (only if user asked for charts / 带图):\n"
        "  If the user wants charts, generate them with generate_chart using data already\n"
        "  in the conversation or by running 1-2 targeted queries.\n"
        "  Charts are automatically bundled into the ZIP when the report is confirmed.\n"
        "  If the user did NOT ask for charts, skip this step entirely.\n\n"
        "Step 2 — Compose the report outline from the conversation history:\n"
        "  title: a concise, descriptive title\n"
        "  sections: Executive Summary → Key Findings → Detailed Analysis → Recommendations\n"
        "  Each section has heading + content (plain text summary from the conversation).\n"
        "  Do NOT re-query or re-analyse data for the text content.\n\n"
        "Step 3 — Call propose_report_outline(title=..., sections=[...]).\n"
        "  Output NOTHING after the tool call — the UI handles confirmation."
    ),
    "report_revise": (
        "The user wants to revise the report outline. "
        "Current title/sections are embedded as [CURRENT_REPORT_JSON] in the user message. "
        "Apply the requested changes and call propose_report_outline with the updated params. "
        "Output NOTHING after the tool call."
    ),
    "ppt": (
        "The user issued /ppt. Goal: call propose_ppt_outline — NEVER generate_ppt this turn.\n\n"
        "IMPORTANT: This MUST be done in TWO SEPARATE turns. Do NOT call propose_ppt_outline "
        "in the same turn as data queries — you need the query results first!\n\n"
        "Turn 1 — Gather data:\n"
        "  Call get_schema ONCE to understand tables. Run 2–5 queries to retrieve the key\n"
        "  metrics, breakdowns, and time-series that the PPT will visualise.\n"
        "  STOP after issuing these tool calls. Do NOT call propose_ppt_outline yet.\n\n"
        "Turn 1b — Color scheme (optional): if the user specifies a firm style "
        "(BCG/Bain/EY/McKinsey), call set_ppt_color_scheme first. Default: mckinsey.\n\n"
        "Turn 2 — After you receive the query results, design 8–15 slides using ONLY "
        "real data from those results.\n"
        "  NEVER fabricate numbers, labels, or percentages — use exact values from tool results.\n"
        "  Structure: cover → toc → [section_divider + content] × N → closing.\n"
        "  Include at least 2 chart slides with actual data rows:\n"
        "    donut  : segments list [[value_fraction, 'COLOR', 'Label'], ...] — fractions sum to 1.0\n"
        "    grouped_bar / stacked_bar: categories, series, and values from query results\n"
        "    timeline: milestones list from real data\n"
        "  Allowed layouts: cover, toc, section_divider, big_number, two_stat, metric_cards,\n"
        "    data_table, table_insight, executive_summary, two_column_text, action_items,\n"
        "    donut, grouped_bar, stacked_bar, timeline, closing.\n"
        "  Color strings ONLY: NAVY, ACCENT_BLUE, ACCENT_GREEN, ACCENT_ORANGE, ACCENT_RED.\n\n"
        "  Then call propose_ppt_outline(title=..., slides=[...]).\n"
        "  Output NOTHING after the tool call — the UI handles user interaction."
    ),
    "ppt_revise": (
        "The user wants to revise a PPT outline. The current slides JSON is embedded in\n"
        "the user message as [CURRENT_SLIDES_JSON]. Parse it, apply the requested changes,\n"
        "then call propose_ppt_outline with the updated complete slides list.\n"
        "Do NOT call generate_ppt. Do NOT call data tools unless the user asks for new data.\n"
        "Output NOTHING after the tool call."
    ),
    "dashboard": (
        "The user issued /dashboard. Goal: call propose_dashboard_outline — NEVER call generate_dashboard this turn.\n\n"
        "IMPORTANT: This MUST be done in TWO SEPARATE turns. Do NOT call propose_dashboard_outline\n"
        "in the same turn as data queries — you need the query results first!\n\n"
        "Turn 1 — Gather data:\n"
        "  Call get_schema ONCE to understand tables and column names.\n"
        "  Run 2–5 exploratory queries to understand data shape, key metrics, and distributions.\n"
        "  STOP after issuing these tool calls. Do NOT call propose_dashboard_outline yet.\n\n"
        "Turn 2 — After receiving query results, design 2–6 dashboard widgets.\n"
        "  Each widget MUST have a valid SQL query using ONLY real table/column names from the schema.\n"
        "  NEVER fabricate column names or table names — only use what get_schema returned.\n"
        "  Choose appropriate chart types:\n"
        "    Bar_Chart / Line_Chart: for comparisons or trends (field_mapping: x, y)\n"
        "    Grouped_Bar_Chart: for multi-series comparisons (field_mapping: x, y=[col1,col2,...])\n"
        "    Stacked_Bar_Chart: for part-to-whole comparisons (field_mapping: x, y=[col1,col2,...])\n"
        "    Pie_Chart: for proportions (field_mapping: label, value)\n"
        "    Scatter_Plot: for correlations (field_mapping: x, y, [color])\n"
        "    Area_Chart: for cumulative trends (field_mapping: x, y)\n"
        "    Heatmap: for matrix/correlation data (field_mapping: x, y, value)\n"
        "  Assign grid positions so widgets tile neatly (total width = 12 units):\n"
        "    e.g. two widgets side-by-side: {x:0,y:0,w:6,h:4} and {x:6,y:0,w:6,h:4}\n"
        "  Then call propose_dashboard_outline(name=..., widgets=[...]).\n"
        "  Output NOTHING after the tool call — the UI handles user confirmation."
    ),
    "dashboard_revise": (
        "The user wants to revise the dashboard outline. "
        "The current widgets JSON is embedded as [CURRENT_DASHBOARD_JSON] in the user message. "
        "Apply the requested changes and call propose_dashboard_outline with the updated params. "
        "Do NOT call generate_dashboard. Do NOT call data tools unless the user asks for new data. "
        "Output NOTHING after the tool call."
    ),
}


def get_system_prompt() -> str:
    """Return SYSTEM_PROMPT with freshly-loaded knowledge base summary.

    Called once per conversation turn in agent.py so that toggling a knowledge
    entry takes effect on the next message without restarting the server.
    """
    return _build_system_prompt()
