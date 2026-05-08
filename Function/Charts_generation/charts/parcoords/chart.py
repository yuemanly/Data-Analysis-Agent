"""
平行坐标图 Parallel Coordinates - 多维图表
图表分类: 多维 Multi-dimensional | 书章节: Ch5
感知排名: ★★★☆☆

统一接口:
    generate(df, mapping, options) -> ChartResult
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

import pandas as pd
import plotly.express as px
import plotly.io as pio

_PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from charts.base import ChartResult

__all__ = ["generate"]

_DATA_FMT = "多列数值（每列一个维度）"
_DESC = "用平行轴表示多维数据，每条线代表一个样本，适合对比多维实体。"


def _build_html(title: str, chart_name: str, library: str,
                data_fmt: str, desc: str, embed: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<title>{title}</title>
<style>
body{{font-family:"Heiti SC","Microsoft YaHei",sans-serif;margin:40px;background:#fafafa}}
.chart-wrap{{background:white;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,.08);padding:24px;margin-bottom:32px}}
h1{{color:#222;font-size:22px;margin-bottom:6px}}
.subtitle{{color:#888;font-size:13px;margin-bottom:24px}}
.desc{{color:#555;font-size:14px;line-height:1.7;margin-top:20px}}
</style></head>
<body><div class="chart-wrap">
<h1>{title}</h1><div class="subtitle">{chart_name} | {library}</div>
{embed}
</div><div class="desc">
<strong>数据格式：</strong>{data_fmt}<br>
<strong>说明：</strong>{desc}
</div></body></html>"""


def generate(
    df: pd.DataFrame = None,
    mapping: Dict[str, str] = None,
    options: Dict[str, Any] = None,
    # ── 向后兼容旧接口 ──────────────────────────────
    excel_path: str = None,
    dims: List[str] = None,
    color: str = None,
    title: str = "平行坐标图",
    **kwargs
) -> ChartResult:
    warnings: list = []
    options = options or {}
    mapping = mapping or {}

    if df is None:
        if excel_path:
            try:
                df = pd.read_excel(excel_path)
            except Exception as e:
                return ChartResult(warnings=[f"读取Excel失败: {e}"])
        else:
            return ChartResult(warnings=["请提供 df 或 excel_path"])

    color_col = mapping.get("color") or color
    title = options.get("title", title)

    # dims: list of column names, or None = all numeric
    if dims is None:
        dims = list(df.select_dtypes(include="number").columns)
    if isinstance(dims, str):
        dims = [d.strip() for d in dims.split(",")]

    _color = _auto_col_helper(df, color_col, "color", "类别", "group") if color_col else None
    if _color and _color not in df.columns:
        _color = None

    if not dims:
        warnings.append("没有找到数值列用于维度")
        return ChartResult(warnings=warnings)

    fig = px.parallel_coordinates(
        df, dimensions=dims, color=_color, title=title, **kwargs)
    fig.update_layout(font_family="Heiti SC, Microsoft YaHei, sans-serif",
                      margin=dict(l=40, r=40, t=60, b=40))

    chart_html = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")
    html = _build_html(title, "parcoords", "plotly", _DATA_FMT, _DESC, chart_html)


    meta = {
        "chart_id": "parcoords",
        "n_rows": len(df),
        "dims": dims,
        "color_col": _color,
    }

    return ChartResult(html=html, spec={}, warnings=warnings, meta=meta)


def _auto_col_helper(df: pd.DataFrame, *hints: str) -> Optional[str]:
    """根据提示自动查找匹配的列名"""
    strs = [c for c in df.columns if df[c].dtype == object]
    nums = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    col_lower = {c.lower(): c for c in df.columns}
    for h in hints:
        h_lower = h.lower()
        if h_lower in col_lower:
            return col_lower[h_lower]
        for col, cl in col_lower.items():
            if h_lower in cl or cl in h_lower:
                return col
    if hints:
        t = hints[0]
        if t in ("str", "x", "label", "category", "group", "color") and strs:
            return strs[0]
        if t in ("num", "y", "value", "amount", "num") and nums:
            return nums[0]
    return hints[0] if hints else None
