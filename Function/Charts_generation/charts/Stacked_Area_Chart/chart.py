"""
堆叠面积图 Stacked Area Chart - 趋势图表
图表分类: 趋势 Trend | 书章节: Ch6
感知排名: ★★★★☆

统一接口:
    generate(df, mapping, options) -> ChartResult

使用示例:
    from charts.Stacked_Area_Chart.chart import generate
    from charts import ChartResult

    result = generate(
        df=df,
        mapping={"x": "月份", "y": ["销售额", "成本"]},
        options={"title": "累积趋势"}
    )
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

_PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from charts.base import ChartResult
from charts.color_schemes import get_color_scheme

__all__ = ["generate"]

_DATA_FMT = "x列(时间/类别) + y列(数值，支持多列) + 可选series列(分组)"
_DESC = "堆叠面积图通过填充区域展示多个数值序列的累积贡献，适合展示部分与整体的关系。支持多列堆叠和麦肯锡配色。"

# 麦肯锡配色方案
MCKINSEY_COLORS = [
    "#003D7A",  # 深蓝
    "#0084D1",  # 中蓝
    "#00A4EF",  # 浅蓝
    "#7FBA00",  # 绿色
    "#FFB81C",  # 金色
    "#F7630C",  # 橙色
    "#DA3B01",  # 红色
    "#A4373A",  # 深红
    "#6B2C91",  # 紫色
    "#00B4EF",  # 青色
]


def _get_colors_for_scheme(color_scheme_name: str, count: int = 10) -> List[str]:
    """获取指定配色方案的颜色列表"""
    scheme = get_color_scheme(color_scheme_name)
    colors = scheme.get("colors", MCKINSEY_COLORS)
    result = []
    for i in range(count):
        result.append(colors[i % len(colors)])
    return result


def _auto_col(df: pd.DataFrame, role: str, exclude: set = None) -> Optional[str]:
    """根据角色自动查找匹配的列名。
    
    参数：
        role: 'x' (时间/类别) 或 'y' (数值)
        exclude: 已使用的列名集合，避免重复
    
    策略：
    1. 精确匹配常见列名
    2. 类型推断（x优先字符串，y优先数值）
    3. 回退到第一个合适的列
    """
    exclude = exclude or set()
    strs = [c for c in df.columns if df[c].dtype == object and c not in exclude]
    nums = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c not in exclude]
    col_lower = {c.lower(): c for c in df.columns if c not in exclude}
    
    if role == "x":
        # x 优先查找时间/类别列
        time_hints = ["date", "time", "month", "year", "week", "day", "period", "时间", "日期", "月份", "年份"]
        for hint in time_hints:
            if hint.lower() in col_lower:
                return col_lower[hint.lower()]
        # 回退到第一个字符串列
        if strs:
            return strs[0]
        # 最后回退到第一个数值列
        if nums:
            return nums[0]
    
    elif role == "y":
        # y 优先查找数值列
        value_hints = ["value", "amount", "sales", "count", "frequency", "数值", "销售额", "销量", "金额","线上","线下"]
        for hint in value_hints:
            if hint.lower() in col_lower:
                return col_lower[hint.lower()]
        # 回退到第一个数值列
        if nums:
            return nums[0]
        # 最后回退到第一个字符串列
        if strs:
            return strs[0]
    
    return None


def _get_numeric_cols(df: pd.DataFrame, exclude: set = None) -> List[str]:
    """获取所有数值列"""
    exclude = exclude or set()
    return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c not in exclude]


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
    mapping: Dict[str, Union[str, List[str]]] = None,
    options: Dict[str, Any] = None,
    excel_path: str = None,
    x: str = "x",
    y: Union[str, List[str]] = "y",
    title: str = "堆叠面积图",
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

    x_col = mapping.get("x") or x
    y_cols = mapping.get("y") or y
    title = options.get("title", title)
    color_scheme_name = options.get("color_scheme", "mckinsey")
    series_col = mapping.get("series") or options.get("series")

    if y_cols == "y" or y_cols is None:
        y_cols = []
    elif isinstance(y_cols, str):
        y_cols = [y_cols]
    elif not isinstance(y_cols, list):
        y_cols = [str(y_cols)]

    if x_col and x_col != "x":
        _x = x_col if x_col in df.columns else _auto_col(df, "x")
    else:
        _x = _auto_col(df, "x")

    if _x is None or _x not in df.columns:
        return ChartResult(warnings=warnings + ["找不到有效x列"])

    _y_cols = []
    exclude_for_y = {_x}
    for y_col in y_cols:
        if y_col and y_col != "y":
            if y_col in df.columns:
                _y_cols.append(y_col)
                exclude_for_y.add(y_col)
            else:
                warnings.append(f"y列 '{y_col}' 不存在")
        else:
            auto_y = _auto_col(df, "y", exclude_for_y)
            if auto_y:
                _y_cols.append(auto_y)
                exclude_for_y.add(auto_y)

    if not _y_cols:
        _y_cols = _get_numeric_cols(df, exclude_for_y)

    if not _y_cols:
        return ChartResult(warnings=warnings + ["找不到任何数值列"])

    if len(_y_cols) > 5:
        warnings.append(f"数值列过多({len(_y_cols)}个)，只显示前5列")
        _y_cols = _y_cols[:5]

    try:
        df_plot = df[[_x] + _y_cols + ([series_col] if series_col in df.columns else [])].copy()

        for col in _y_cols:
            df_plot[col] = pd.to_numeric(df_plot[col], errors="coerce")

        df_plot = df_plot.dropna(subset=[_x] + _y_cols)
        if df_plot.empty:
            return ChartResult(warnings=warnings + ["无有效数据"])

        fig = go.Figure()
        colors = _get_colors_for_scheme(color_scheme_name, max(len(_y_cols), 10))

        if series_col and series_col in df_plot.columns:
            # 分组后分别画堆叠面积：每个 series 内部再堆叠 y_cols
            groups = list(df_plot[series_col].dropna().unique())
            if len(groups) > 3:
                warnings.append(f"分组数过多({len(groups)}个)，建议 ≤3")

            for gi, g in enumerate(groups):
                dfg = df_plot[df_plot[series_col] == g]
                first = True
                for yi, col in enumerate(_y_cols):
                    fig.add_trace(go.Scatter(
                        x=dfg[_x],
                        y=dfg[col],
                        mode="lines",
                        name=f"{g}-{col}",
                        line=dict(color=colors[(gi + yi) % len(colors)], width=0.8),
                        stackgroup=str(g),
                        groupnorm=None,
                        fillcolor=colors[(gi + yi) % len(colors)],
                    ))
        else:
            # 标准堆叠面积图
            for i, col in enumerate(_y_cols):
                fig.add_trace(go.Scatter(
                    x=df_plot[_x],
                    y=df_plot[col],
                    mode="lines",
                    name=col,
                    line=dict(color=colors[i % len(colors)], width=0.8),
                    stackgroup="one",
                    fillcolor=colors[i % len(colors)],
                ))

        fig.update_layout(
            title=title,
            font_family="Heiti SC, Microsoft YaHei, sans-serif",
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=50, r=50, t=70, b=50),
            hovermode="x unified",
            xaxis_title=str(_x),
            yaxis_title="数值",
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )

        chart_html = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")
    except Exception as e:
        return ChartResult(warnings=warnings + [f"图表生成失败: {e}"])

    html = _build_html(title, "stacked_area_chart", "plotly", _DATA_FMT, _DESC, chart_html)

    meta = {
        "chart_id": "stacked_area_chart",
        "n_rows": len(df),
        "x_col": _x,
        "y_cols": _y_cols,
        "n_y_cols": len(_y_cols),
    }

    return ChartResult(html=html, spec={}, warnings=warnings, meta=meta)
