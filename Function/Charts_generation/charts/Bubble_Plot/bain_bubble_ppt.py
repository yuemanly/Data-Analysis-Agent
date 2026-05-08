# -*- coding: utf-8 -*-
"""
Bain 气泡图 - PPT 专用版本
基于 chart.py 改造，使用 Bain 官方配色方案
"""
import sys
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
from collections import defaultdict
import json as _json

_PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from charts.base import ChartResult

__all__ = ["generate"]

# Bain 官方配色（从 XML 提取）
BAIN_COLORS = {
    "cluster_1": "#E41E26",      # accent1 - 深红
    "cluster_2": "#FF5C5C",      # accent2 - 浅红
    "cluster_3": "#A6192E",      # accent3 - 暗红
    "cluster_4": "#999999",      # 灰色（自定义）
}

BAIN_PRIMARY = "#E41E26"
BAIN_GRAY = "#999999"
BAIN_LIGHT = "#EDEDED"


def _jesc(s: str) -> str:
    return (str(s).replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t"))


def _is_numeric(s: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(s)


def generate(
    df: pd.DataFrame = None,
    mapping: Dict[str, str] = None,
    options: Dict[str, Any] = None,
    excel_path: str = None,
    x: str = None,
    y: str = None,
    size: str = None,
    color: str = None,
    title: str = "Bain 气泡图",
    subtitle: str = "",
    **kwargs
) -> ChartResult:
    """
    Bain 风格气泡图生成器
    
    Parameters
    ----------
    df : pd.DataFrame
        数据框，必须包含：City, Scale, Profitability, MAU, Color 列
    mapping : dict
        列名映射，e.g. {"x": "Scale", "y": "Profitability", "size": "MAU", "color": "Color"}
    options : dict
        图表选项，e.g. {"x_mid": 77.5, "y_mid": -14, "title": "自定义标题"}
        如果不指定 x_mid 和 y_mid，则不画象限线
    title : str
        图表标题
    subtitle : str
        图表副标题（显示在底部）
    
    Returns
    -------
    ChartResult with .html attribute
    """
    warnings = []
    options = options or {}
    mapping = mapping or {}

    if df is None:
        if excel_path:
            try:
                df = pd.read_excel(excel_path)
            except Exception as e:
                return ChartResult(warnings=[f"读取Excel失败: {e}"])
        else:
            return ChartResult(warnings=["需要 df 或 excel_path"])

    if df.empty:
        return ChartResult(warnings=["数据为空"])

    # 确保列名全部为字符串
    df.columns = df.columns.astype(str)

    # 列名映射
    xh = mapping.get("x") or x or "Scale"
    yh = mapping.get("y") or y or "Profitability"
    sh = mapping.get("size") or size or "MAU"
    ch = mapping.get("color") or color or "Color"
    title = options.get("title", title)
    subtitle = options.get("subtitle", subtitle)

    # 提取列
    if xh not in df.columns:
        return ChartResult(warnings=[f"找不到列: {xh}"])
    if yh not in df.columns:
        return ChartResult(warnings=[f"找不到列: {yh}"])
    if sh not in df.columns:
        return ChartResult(warnings=[f"找不到列: {sh}"])
    if ch not in df.columns:
        return ChartResult(warnings=[f"找不到列: {ch}"])

    # 城市列（用于标签）
    city_col = None
    for col in df.columns:
        if col.lower() == "city":
            city_col = col
            break
    if not city_col:
        city_col = df.columns[0]  # 默认第一列

    # 数值转换
    dfx = pd.to_numeric(df[xh], errors="coerce")
    dfy = pd.to_numeric(df[yh], errors="coerce")
    dfs = pd.to_numeric(df[sh], errors="coerce")
    dfc = pd.to_numeric(df[ch], errors="coerce")

    valid = dfx.notna() & dfy.notna() & dfs.notna() & dfc.notna()
    if valid.sum() == 0:
        return ChartResult(warnings=["无有效数据点"])

    xn = dfx[valid]
    yn = dfy[valid]
    sn = dfs[valid]
    cn = dfc[valid]

    xlo, xhi = float(xn.min()), float(xn.max())
    ylo, yhi = float(yn.min()), float(yn.max())
    slo, shi = float(sn.min()), float(sn.max())
    clo, chi = float(cn.min()), float(cn.max())

    # 坐标轴范围扩展 6%
    xp = (xhi - xlo) * 0.06
    yp = (yhi - ylo) * 0.06
    xlo, xhi = (xlo - xp, xhi + xp) if xp > 0 else (xlo - 0.1, xhi + 0.1)
    ylo, yhi = (ylo - yp, yhi + yp) if yp > 0 else (ylo - 0.1, yhi + 0.1)

    # 象限线（可选）
    x_mid = options.get("x_mid")
    y_mid = options.get("y_mid")
    if x_mid is not None:
        x_mid = float(x_mid)
    if y_mid is not None:
        y_mid = float(y_mid)

    # 构建数据点
    rows = []
    for idx, r in df[valid].iterrows():
        try:
            xv = float(r[xh])
            yv = float(r[yh])
            sv = float(r[sh])
            cv = float(r[ch])
        except Exception:
            continue

        # 气泡大小映射：18 + (val - min) / (max - min) * 62
        if shi > slo:
            px = int(18 + (sv - slo) / (shi - slo) * 62)
        else:
            px = 40

        # 颜色映射：根据 Color 列的值（1-4）选择 Bain 配色
        color_map = {
            1: BAIN_COLORS["cluster_1"],
            2: BAIN_COLORS["cluster_2"],
            3: BAIN_COLORS["cluster_3"],
            4: BAIN_COLORS["cluster_4"],
        }
        item_color = color_map.get(int(cv), BAIN_GRAY)

        # 城市名
        city_name = str(r[city_col]) if pd.notna(r[city_col]) else f"Point {idx}"

        # tooltip
        tip = f"{city_name}<br>{xh}: {round(xv, 1)}<br>{yh}: {round(yv, 1)}<br>{sh}: {round(sv, 1)}"

        point = {
            "name": city_name,
            "value": [xv, yv, px],
            "itemStyle": {"color": item_color, "opacity": 0.85, "borderColor": "#fff", "borderWidth": 2},
            "tip": tip,
        }
        rows.append(point)

    if not rows:
        return ChartResult(warnings=["无有效数据点"])

    # 按 Color 分组（用于图例）
    groups: Dict[int, List] = defaultdict(list)
    for idx, r in df[valid].iterrows():
        try:
            cv = int(r[ch])
        except Exception:
            cv = 1
        if idx < len(rows):
            groups[cv].append(rows[df[valid].index.get_loc(idx)])

    # 构建 series（按 Cluster 分组）
    series_list = []
    legend_data = []
    cluster_names = {
        1: "Cluster-1",
        2: "Cluster-2",
        3: "Cluster-3",
        4: "Cluster-4",
    }

    for cluster_id in sorted(groups.keys()):
        cluster_rows = groups[cluster_id]
        if not cluster_rows:
            continue

        cluster_name = cluster_names.get(cluster_id, f"Cluster-{cluster_id}")
        cluster_color = color_map.get(cluster_id, BAIN_GRAY)

        s = {
            "type": "scatter",
            "name": cluster_name,
            "data": cluster_rows,
            "symbolSize": "function(d){return d[2] || 40;}",
            "label": {
                "show": True,
                "position": "top",
                "formatter": "function(p){return p.data&&p.data.name?p.data.name:'';}",
                "fontSize": 11,
                "color": BAIN_PRIMARY,
                "fontWeight": "bold",
            },
            "itemStyle": {"color": cluster_color, "opacity": 0.85, "borderColor": "#fff", "borderWidth": 2},
            "tooltip": {"trigger": "item", "formatter": "function(p){return (p.data&&p.data.tip)?p.data.tip:'';}"},
        }
        series_list.append(s)
        legend_data.append(cluster_name)

    # 象限线（仅当 x_mid 和 y_mid 都存在时才画）
    if x_mid is not None and y_mid is not None and series_list:
        markline = {
            "silent": True,
            "symbol": "none",
            "lineStyle": {"type": "dashed", "width": 1.5, "color": BAIN_GRAY},
            "label": {"formatter": "", "show": False},
            "data": [
                {"xAxis": x_mid},
                {"yAxis": y_mid},
            ],
        }
        series_list[0]["markLine"] = markline

    # ECharts 配置
    echarts_opt = {
        "animation": True,
        "title": {
            "text": title,
            "left": "center",
            "top": "1%",
            "textStyle": {"color": BAIN_PRIMARY, "fontSize": 18, "fontWeight": "bold", "fontFamily": "Arial, sans-serif"},
        },
        "tooltip": {
            "trigger": "item",
            "axisPointer": {"type": "cross"},
            "backgroundColor": "rgba(255,255,255,0.95)",
            "borderColor": BAIN_LIGHT,
            "borderWidth": 1,
            "textStyle": {"color": "#333", "fontSize": 12},
        },
        "legend": {
            "show": True,
            "bottom": "12%",
            "left": "center",
            "data": legend_data,
            "textStyle": {"color": "#333", "fontSize": 12},
            "itemGap": 20,
        },
        "xAxis": {
            "type": "value",
            "name": xh,
            "nameLocation": "middle",
            "nameGap": 42,
            "min": xlo,
            "max": xhi,
            "axisLabel": {"fontSize": 12, "color": "#333"},
            "axisLine": {"lineStyle": {"color": BAIN_LIGHT, "width": 1.5}},
            "splitLine": {"show": False},
            "nameTextStyle": {"color": BAIN_PRIMARY, "fontSize": 13, "fontWeight": "bold"},
        },
        "yAxis": {
            "type": "value",
            "name": yh,
            "nameLocation": "middle",
            "nameGap": 45,
            "min": ylo,
            "max": yhi,
            "axisLabel": {"fontSize": 12, "color": "#333"},
            "axisLine": {"lineStyle": {"color": BAIN_LIGHT, "width": 1.5}},
            "splitLine": {"show": False},
            "nameTextStyle": {"color": BAIN_PRIMARY, "fontSize": 13, "fontWeight": "bold"},
        },
        "series": series_list,
        "grid": {
            "left": "8%",
            "right": "8%",
            "top": "10%",
            "bottom": "22%",
        },
    }

    opt_json = _json.dumps(echarts_opt, ensure_ascii=False)

    # 底部标签说明
    legend_html = ""
    if subtitle:
        legend_html = f"<div class='subtitle'>{_jesc(subtitle)}</div>"

    # 完整 HTML
    html = (
        "<!DOCTYPE html><html lang='zh-CN'><head><meta charset='UTF-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1.0'>"
        f"<title>{_jesc(title)}</title>"
        "<style>"
        "*{margin:0;padding:0;box-sizing:border-box}"
        "html,body{width:100%;height:100%;font-family:Arial,sans-serif;background:#fff}"
        f"#header{{padding:12px 24px;background:#fff;border-bottom:2px solid {BAIN_LIGHT};box-shadow:0 1px 4px rgba(0,0,0,.06)}}"
        f"#header h1{{font-size:18px;color:{BAIN_PRIMARY};font-weight:700}}"
        f"#header .sub{{font-size:12px;color:{BAIN_GRAY};margin-top:4px}}"
        "#chart{width:100%;height:calc(100vh - 120px)}"
        f"#footer{{padding:12px 24px;background:#fff;border-top:1px solid {BAIN_LIGHT};text-align:center}}"
        f".subtitle{{font-size:12px;color:#666;line-height:1.6}}"
        "</style></head><body>"
        f"<div id='header'><h1>{_jesc(title)}</h1></div>"
        "<div id='chart'></div>"
        f"<div id='footer'>{legend_html}</div>"
        "<script src='https://assets.pyecharts.org/assets/v6/echarts.min.js'></script>"
        "<script>(function(){"
        "if(!window.echarts){document.getElementById('chart').innerHTML='ECharts加载失败';return;}"
        "var chart=echarts.init(document.getElementById('chart'),'white',{renderer:'canvas',locale:'ZH'});"
        f"var option={opt_json};"
        "for(var i=0;i<option.series.length;i++){"
        "  var s=option.series[i];"
        "  if(s.tooltip&&typeof s.tooltip.formatter==='string'){"
        "    try{s.tooltip.formatter=eval('('+s.tooltip.formatter+')');}catch(e){}"
        "  }"
        "  if(s.label&&typeof s.label.formatter==='string'){"
        "    try{s.label.formatter=eval('('+s.label.formatter+')');}catch(e){}"
        "  }"
        "  if(s.symbolSize&&typeof s.symbolSize==='string'){"
        "    try{s.symbolSize=eval('('+s.symbolSize+')');}catch(e){}"
        "  }"
        "}"
        "chart.setOption(option);"
        "window.addEventListener('resize',function(){chart.resize();});"
        "})();</script></body></html>"
    )

    meta = {
        "chart_id": "Bain_Bubble_PPT",
        "n_rows": int(len(df)),
        "n_points": int(len(rows)),
        "x_col": xh,
        "y_col": yh,
        "size_col": sh,
        "color_col": ch,
        "x_mid": x_mid,
        "y_mid": y_mid,
    }
    return ChartResult(html=html, spec={}, warnings=warnings, meta=meta)
