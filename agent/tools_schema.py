# -*- coding: utf-8 -*-
"""LLM tool JSON schemas (the ``tools`` list passed to the API).

Depends on module-level globals from prompts.py — import order matters:
  prompts.py  →  tools_schema.py  →  agent.py
"""
from .prompts import _ANALYZE_GUIDE, _CHART_IDS

AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_knowledge",
            "description": (
                "Search the business knowledge base for canonical metric definitions, "
                "business rules, and context notes. Call this before writing SQL for "
                "any named business metric (DAU, LTV, retention, ARPU, etc.) to check "
                "if a canonical definition or SQL template already exists. "
                "If a result is returned, follow its definition and sql_template exactly. "
                "Skip this call for ad-hoc exploratory queries with no named metric."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": (
                            "The metric name or business concept to look up, "
                            "e.g. 'DAU', '次日留存', 'LTV', '付费渗透率'."
                        ),
                    }
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_schema",
            "description": (
                "Get the full schema of the connected data source — tables, columns, "
                "types, and row counts. Always call this first when the user asks "
                "about data you haven't seen yet."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_analysis_table",
            "description": (
                "Extract specific fields from the raw data and materialise the result "
                "as a new queryable table. Use this to: (1) select only the columns "
                "needed for the current analysis, (2) pre-aggregate or filter large "
                "datasets before charting, (3) join / reshape data into the exact "
                "shape a chart requires. The resulting table is immediately available "
                "to query_data and generate_chart by its table_name."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": (
                            "SQL SELECT that defines the analysis table — "
                            "select the exact columns needed, apply WHERE filters, "
                            "GROUP BY aggregations, JOINs, etc."
                        ),
                    },
                    "table_name": {
                        "type": "string",
                        "description": (
                            "Name for the new temp table (default: 'analysis_data'). "
                            "Use a descriptive name when creating multiple tables."
                        ),
                    },
                },
                "required": ["sql"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_data",
            "description": "Execute a SQL SELECT query and return the results as a table.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "A valid SQL SELECT statement using actual column/table names from the schema.",
                    }
                },
                "required": ["sql"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_analysis",
            "description": (
                "Run a built-in statistical analysis template on the data.\n"
                "Steps: (1) call get_schema to know the tables/columns, "
                "(2) call run_analysis with the appropriate parameters, "
                "(3) the result is stored as queryable tables — call generate_chart on them.\n\n"
                "Available analyses:\n"
                f"{_ANALYZE_GUIDE}"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "analysis_name": {
                        "type": "string",
                        "description": "Analysis ID, e.g. 'Data_Decile_Analysis'.",
                    },
                    "sql": {
                        "type": "string",
                        "description": (
                            "SQL SELECT to fetch the raw data for analysis. "
                            "Include the target column and any optional groupby column. "
                            "Example: SELECT revenue, region FROM sales_data"
                        ),
                    },
                    "target_column": {
                        "type": "string",
                        "description": "The numeric column to analyse (must exist in the SQL result).",
                    },
                    "groupby_column": {
                        "type": "string",
                        "description": "(Optional) A categorical column for additional breakdown.",
                    },
                    "n_deciles": {
                        "type": "integer",
                        "description": "Number of buckets (default 10). Use 5 for quintiles, 4 for quartiles.",
                    },
                },
                "required": ["analysis_name", "sql", "target_column"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_chart",
            "description": (
                "Create a data visualization chart displayed to the user. "
                "Use after querying to confirm the data shape. "
                "See the system prompt for the complete chart type list and their field_mapping requirements."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "chart_type": {
                        "type": "string",
                        "description": (
                            f"Exact chart_id from the registry. Available: {_CHART_IDS}"
                        ),
                    },
                    "sql": {
                        "type": "string",
                        "description": "SQL query to retrieve data for the chart.",
                    },
                    "field_mapping": {
                        "type": "object",
                        "description": (
                            "Maps chart field roles to column names per the chart's data_format. "
                            'E.g. {"x": "month", "y": "revenue"} or '
                            '{"label": "product", "value": "sales"}.'
                        ),
                    },
                    "title": {
                        "type": "string",
                        "description": "Chart title shown above the visualization.",
                    },
                },
                "required": ["chart_type", "sql", "field_mapping"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "profile_data",
            "description": (
                "Profile a data table: per-column missing value %, dtype, "
                "and for numeric columns: mean/std/min/max/quartiles. "
                "Also generates distribution histogram charts automatically. "
                "Call this for the /data command."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Table to profile. Leave empty to use the first available table.",
                    },
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of columns to limit profiling to.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "clean_data",
            "description": (
                "Clean data in-place and store result as 'cleaned_data' table. "
                "Supports three operations:\n"
                "  fill_na   — fill NaN with zero / mean / median\n"
                "  winsorize — cap values at lower/upper percentiles\n"
                "  trimming  — remove rows outside [min_val, max_val] on one column"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "One of: fill_na | winsorize | trimming",
                    },
                    "table_name": {
                        "type": "string",
                        "description": "Source table name. Leave empty to use the first available raw table.",
                    },
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Columns to process (fill_na / winsorize). None = all numeric columns.",
                    },
                    "fill_method": {
                        "type": "string",
                        "description": "For fill_na: 'zero' | 'mean' | 'median'",
                    },
                    "lower_pct": {
                        "type": "number",
                        "description": "For winsorize: lower percentile, 0–100 (e.g. 1 for 1st percentile)",
                    },
                    "upper_pct": {
                        "type": "number",
                        "description": "For winsorize: upper percentile, 0–100 (e.g. 99 for 99th percentile)",
                    },
                    "trim_column": {
                        "type": "string",
                        "description": "For trimming: the column to filter on",
                    },
                    "min_val": {
                        "type": "number",
                        "description": "For trimming: minimum value to keep (inclusive)",
                    },
                    "max_val": {
                        "type": "number",
                        "description": "For trimming: maximum value to keep (inclusive)",
                    },
                    "output_table": {
                        "type": "string",
                        "description": "Name for the result table (default: 'cleaned_data')",
                    },
                },
                "required": ["operation"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "export_excel",
            "description": (
                "Export data tables to an Excel (.xlsx) file. "
                "Call this ONLY when the user explicitly asked to export data. "
                "Each table becomes a separate sheet. "
                "Pass tables=[\"*\"] to export ALL available tables automatically — "
                "this is the default behaviour unless the user asks for specific tables."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tables": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Table names to export. "
                            "Use [\"*\"] to auto-export every table in the data source "
                            "(raw data + analysis results). "
                            "Only specify exact names if the user asked for specific tables."
                        ),
                    },
                    "filename": {
                        "type": "string",
                        "description": "Base filename without extension (optional, auto-generated if omitted).",
                    },
                },
                "required": ["tables"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "export_report",
            "description": (
                "Generate a Word document (.docx) analysis report. "
                "Call this ONLY when the user explicitly asked to export a report. "
                "Query the data first, then compose sections."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Report title.",
                    },
                    "sections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "heading": {"type": "string"},
                                "content": {
                                    "type": "string",
                                    "description": "Section body text (plain text or markdown-style).",
                                },
                            },
                            "required": ["heading", "content"],
                        },
                        "description": (
                            "Ordered list of report sections. Typical structure: "
                            "Executive Summary → Key Findings → Data Analysis → Recommendations."
                        ),
                    },
                },
                "required": ["title", "sections"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "propose_excel_export",
            "description": (
                "Show the user a preview of which tables will be exported BEFORE generating the Excel file.\n"
                "ONLY call this when the /export slash command is active. NEVER call proactively.\n"
                "The frontend renders a confirmation card with Confirm / Edit / Cancel buttons."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tables": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Table names to export. Use [\"*\"] to export all available tables.",
                    },
                    "filename": {
                        "type": "string",
                        "description": "Base filename without extension (optional).",
                    },
                    "summary": {
                        "type": "string",
                        "description": "One-sentence description of what will be exported.",
                    },
                },
                "required": ["tables"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "propose_report_outline",
            "description": (
                "Show the user a report outline for review BEFORE generating the Word file.\n"
                "ONLY call this when the /report slash command is active. NEVER call proactively.\n"
                "The frontend renders a confirmation card with Confirm / Edit / Cancel buttons."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Report title.",
                    },
                    "sections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "heading": {"type": "string"},
                                "content": {"type": "string"},
                            },
                            "required": ["heading", "content"],
                        },
                        "description": "Ordered list of report sections.",
                    },
                },
                "required": ["title", "sections"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "propose_ppt_outline",
            "description": (
                "Show the user a slide-by-slide PPT outline for review BEFORE generating the file.\n"
                "ONLY call this when the /ppt slash command is active. NEVER call proactively.\n"
                "The frontend will render an editable card with Confirm / Edit / Cancel buttons.\n"
                "Use exactly the same parameters as generate_ppt."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Overall deck title.",
                    },
                    "slides": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "layout": {"type": "string"},
                                "params": {"type": "object"},
                            },
                            "required": ["layout", "params"],
                        },
                        "description": "Ordered list of slides, each {layout, params}.",
                    },
                },
                "required": ["title", "slides"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_ppt",
            "description": (
                "Generate a professional McKinsey-style PowerPoint (.pptx) presentation.\n"
                "ONLY called automatically by the system after user confirms a propose_ppt_outline. NEVER call directly.\n\n"
                "SLIDE LAYOUTS and their params:\n"
                "  cover            title, subtitle?(str), author?(str), date?(str)\n"
                "  toc              title?='目录', items(list of [num_str, title, desc])\n"
                "  section_divider  section_label(str), title(str), subtitle?(str)\n"
                "  big_number       title, number(str), unit?(str), description?(str),\n"
                "                   detail_items?(list[str])\n"
                "  two_stat         title, stats(list of [number_str, label, is_navy_bool])\n"
                "  metric_cards     title, cards(list of [letter, card_title, desc])\n"
                "  data_table       title, headers(list[str]), rows(list[list[str]])\n"
                "  table_insight    title, headers(list[str]), rows(list[list[str]]),\n"
                "                   insights(list[str])\n"
                "  executive_summary title, headline(str),\n"
                "                   items(list of [num_str, item_title, desc])\n"
                "  two_column_text  title, columns(list of [letter, col_title,\n"
                "                   points(list[str])])\n"
                "  action_items     title, actions(list of [action_title, timeline, desc, owner])\n"
                "  donut            title, segments(list of [pct_float, color_str, label]),\n"
                "                   center_label?(str), center_sub?(str)\n"
                "  grouped_bar      title, categories(list[str]),\n"
                "                   series(list of [name, color_str]),\n"
                "                   data(list[list[num]]), max_val?(num)\n"
                "  stacked_bar      title, periods(list[str]),\n"
                "                   series(list of [name, color_str]),\n"
                "                   data(list[list[num]] — percentages 0-100)\n"
                "  timeline         title, milestones(list of [label, description])\n"
                "  closing          title, message?(str)\n\n"
                "Color string constants for color params:\n"
                "  NAVY (primary dark), ACCENT_BLUE, ACCENT_GREEN, ACCENT_ORANGE, ACCENT_RED,\n"
                "  BG_GRAY, LIGHT_BLUE, LIGHT_GREEN, LIGHT_ORANGE, LIGHT_RED, MED_GRAY"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Overall deck title (used for the filename).",
                    },
                    "slides": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "layout": {
                                    "type": "string",
                                    "description": "Slide layout name, e.g. 'cover', 'donut', 'timeline'.",
                                },
                                "params": {
                                    "type": "object",
                                    "description": "Parameters matching the chosen layout's signature.",
                                },
                            },
                            "required": ["layout", "params"],
                        },
                        "description": "Ordered list of slides. Each item: {layout, params}.",
                    },
                    "filename": {
                        "type": "string",
                        "description": "Optional base filename without extension.",
                    },
                },
                "required": ["title", "slides"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_ppt_color_scheme",
            "description": (
                "Set the color scheme for ALL visuals in this session — both Plotly charts "
                "and PPT slides. Default is 'mckinsey'. "
                "Available schemes: mckinsey, bcg, bain, ey. "
                "Call this IMMEDIATELY whenever the user mentions a color preference, firm style, "
                "or brand (e.g. 'BCG green', 'Bain style', 'EY yellow', '麦肯锡蓝'). "
                "If the user never specifies, do NOT call this tool — mckinsey is already active."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "scheme": {
                        "type": "string",
                        "enum": ["mckinsey", "bcg", "bain", "ey"],
                        "description": "Color scheme name.",
                    },
                },
                "required": ["scheme"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "propose_dashboard_outline",
            "description": (
                "Show the user a dashboard outline for review BEFORE generating the dashboard.\n"
                "ONLY call this when the /dashboard slash command is active. NEVER call proactively.\n"
                "The frontend renders a confirmation card with Confirm / Edit / Cancel buttons.\n"
                "Do NOT call generate_dashboard in the same turn."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Dashboard name."},
                    "widgets": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "chart_type": {
                                    "type": "string",
                                    "enum": [
                                        "Bar_Chart", "Line_Chart", "Pie_Chart",
                                        "Scatter_Plot", "Area_Chart", "Grouped_Bar_Chart",
                                        "Heatmap", "Stacked_Bar_Chart",
                                    ],
                                },
                                "sql": {"type": "string", "description": "Valid SQL against real tables."},
                                "field_mapping": {
                                    "type": "object",
                                    "description": "Maps chart axes/roles to column names.",
                                },
                                "options": {"type": "object"},
                                "grid": {
                                    "type": "object",
                                    "description": "{x, y, w, h} grid position (w/h in grid units).",
                                },
                            },
                            "required": ["title", "chart_type", "sql", "field_mapping"],
                        },
                        "description": "List of widget specs (2–6 widgets recommended).",
                    },
                },
                "required": ["name", "widgets"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_dashboard",
            "description": (
                "Generate and save an interactive dashboard with multiple chart widgets.\n"
                "Only call this after the user confirms a proposed outline via the UI button,\n"
                "or when the dashboard_confirm command is active.\n"
                "Each widget executes SQL against the connected data source and renders a chart."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Dashboard name."},
                    "widgets": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "chart_type": {
                                    "type": "string",
                                    "enum": [
                                        "Bar_Chart", "Line_Chart", "Pie_Chart",
                                        "Scatter_Plot", "Area_Chart", "Grouped_Bar_Chart",
                                        "Heatmap", "Stacked_Bar_Chart",
                                    ],
                                },
                                "sql": {"type": "string"},
                                "field_mapping": {"type": "object"},
                                "options": {"type": "object"},
                                "grid": {
                                    "type": "object",
                                    "description": "{x, y, w, h} grid position.",
                                },
                            },
                            "required": ["title", "chart_type", "sql", "field_mapping"],
                        },
                    },
                    "color_scheme": {
                        "type": "string",
                        "enum": ["mckinsey", "bcg", "bain", "ey"],
                        "description": "Color scheme (defaults to current session scheme).",
                    },
                },
                "required": ["name", "widgets"],
            },
        },
    },
]


def get_tools_with_mcp(mcp_manager=None) -> list:
    if mcp_manager is None:
        return AGENT_TOOLS
    try:
        mcp_schemas = mcp_manager.get_all_openai_schemas()
    except Exception:
        mcp_schemas = []
    return AGENT_TOOLS + mcp_schemas

