# -*- coding: utf-8 -*-
"""
Bain Bubble Chart Generator - English version
"""
import sys
from pathlib import Path
import pandas as pd
import json as _json

_PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from charts.base import ChartResult

__all__ = ["generate"]

# Bain Color Scheme
BAIN_COLORS = {
    "dk1": "#000000",
    "lt1": "#FFFFFF",
    "dk2": "#E41E26",
    "lt2": "#EDEDED",
    "accent1": "#E41E26",
    "accent2": "#FF5C5C",
    "accent3": "#A6192E",
    "accent4": "#F4E8E9",
    "accent5": "#EDEDED",
    "accent6": "#FFFFFF",
}

BAIN_PRIMARY = BAIN_COLORS["accent1"]
BAIN_ACCENT = BAIN_COLORS["accent2"]
BAIN_DARK = BAIN_COLORS["accent3"]
BAIN_GRAY = "#999999"


def _jesc(s: str) -> str:
    """JavaScript string escape"""
    return (str(s).replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t"))


def generate(
    data: list = None,
    title: str = "Bain Bubble Chart",
    subtitle: str = "",
    x_label: str = "Scale",
    y_label: str = "Profitability",
    x_mid: float = None,
    y_mid: float = None,
    footer_text: str = "",
    **kwargs
) -> ChartResult:
    """
    Generate Bain-colored bubble chart
    
    Parameters
    ----------
    data : list of dict
        Each dict contains:
        - City: city name
        - Scale2: bubble size (pixels)
        - Profitability1: Y-axis value
        - MAU: X-axis value
        - Color: color category (1/2/3/4)
    title : str
        Chart title
    subtitle : str
        Subtitle
    x_label : str
        X-axis label (default: Scale)
    y_label : str
        Y-axis label (default: Profitability)
    x_mid : float
        X-axis midline position
    y_mid : float
        Y-axis midline position
    footer_text : str
        Footer text
    
    Returns
    -------
    ChartResult with .html attribute
    """
    if not data:
        return ChartResult(warnings=["Data is empty"])
    
    df = pd.DataFrame(data)
    
    rows = []
    color_groups = {}
    
    for idx, row in df.iterrows():
        try:
            x_val = float(row.get("MAU", 0))
            y_val = float(row.get("Profitability1", 0))
            size_px = int(row.get("Scale2", 40))
            city = str(row.get("City", "Point {}".format(idx)))
            color_cat = str(row.get("Color", "1"))
            
            if color_cat not in color_groups:
                color_groups[color_cat] = []
            
            point = {
                "name": city,
                "value": [x_val, y_val, size_px],
                "itemStyle": {"opacity": 0.85, "borderColor": "#fff", "borderWidth": 2},
            }
            rows.append((point, color_cat))
            color_groups[color_cat].append(point)
        except Exception as e:
            continue
    
    if not rows:
        return ChartResult(warnings=["No valid data points"])
    
    x_vals = [r[0]["value"][0] for r in rows]
    y_vals = [r[0]["value"][1] for r in rows]
    
    xmin, xmax = min(x_vals), max(x_vals)
    ymin, ymax = min(y_vals), max(y_vals)
    
    xpad = (xmax - xmin) * 0.1 if xmax > xmin else 1
    ypad = (ymax - ymin) * 0.1 if ymax > ymin else 1
    
    xmin -= xpad
    xmax += xpad
    ymin -= ypad
    ymax += ypad
    
    # Color mapping - Bain colors
    color_map = {
        "1": BAIN_PRIMARY,
        "2": BAIN_ACCENT,
        "3": BAIN_DARK,
        "4": BAIN_GRAY,
    }
    
    series_list = []
    legend_data = []
    
    # Always show all 4 clusters in legend, even if no data
    for color_cat in ["1", "2", "3", "4"]:
        cat_rows = color_groups.get(color_cat, [])
        cat_color = color_map.get(color_cat, BAIN_GRAY)
        
        s = {
            "type": "scatter",
            "name": "Cluster-{}".format(color_cat),
            "data": cat_rows,
            "symbolSize": "function(d){return d[2] || 40;}",
            "label": {
                "show": True,
                "position": "top",
                "formatter": "function(p){return p.data && p.data.name ? p.data.name : '';}",
                "fontSize": 11,
                "color": BAIN_PRIMARY,
                "fontWeight": "bold",
            },
            "itemStyle": {
                "color": cat_color,
                "opacity": 0.85,
                "borderColor": "#fff",
                "borderWidth": 2,
            },
            "tooltip": {
                "trigger": "item",
                "formatter": "function(p){if(!p.data)return '';var d=p.data;return d.name+'<br/>Scale: '+d.value[0].toFixed(1)+'<br/>Profitability: '+d.value[1].toFixed(1)+'<br/>MAU: '+d.value[2];}",
            },
        }
        
        if not series_list and (x_mid is not None or y_mid is not None):
            markline_data = []
            if x_mid is not None:
                markline_data.append({"xAxis": x_mid})
            if y_mid is not None:
                markline_data.append({"yAxis": y_mid})
            
            s["markLine"] = {
                "silent": True,
                "symbol": "none",
                "lineStyle": {
                    "type": "dashed",
                    "width": 1.5,
                    "color": BAIN_GRAY,
                },
                "label": {"show": False},
                "data": markline_data,
            }
        
        series_list.append(s)
        legend_data.append("Cluster-{}".format(color_cat))
    
    echarts_opt = {
        "animation": True,
        "title": {
            "text": title,
            "subtext": subtitle,
            "left": "center",
            "top": "2%",
            "textStyle": {
                "color": BAIN_PRIMARY,
                "fontSize": 18,
                "fontWeight": "bold",
                "fontFamily": "Arial, sans-serif",
            },
            "subtextStyle": {
                "color": BAIN_GRAY,
                "fontSize": 12,
            },
        },
        "tooltip": {
            "trigger": "item",
            "axisPointer": {"type": "cross"},
            "backgroundColor": "rgba(255,255,255,0.95)",
            "borderColor": BAIN_ACCENT,
            "borderWidth": 1,
            "textStyle": {"color": "#333", "fontSize": 12},
        },
        "legend": {
            "show": True,
            "bottom": "12%",
            "left": "center",
            "orient": "horizontal",
            "data": legend_data,
            "textStyle": {"color": "#333", "fontSize": 11, "fontFamily": "Arial"},
        },
        "xAxis": {
            "type": "value",
            "name": x_label,
            "nameLocation": "middle",
            "nameGap": 40,
            "min": xmin,
            "max": xmax,
            "axisLabel": {"fontSize": 11, "color": "#333", "fontFamily": "Arial"},
            "axisLine": {"lineStyle": {"color": BAIN_GRAY, "width": 1}},
            "splitLine": {"show": False},
            "nameTextStyle": {"color": BAIN_PRIMARY, "fontSize": 12, "fontWeight": "bold", "fontFamily": "Arial"},
        },
        "yAxis": {
            "type": "value",
            "name": y_label,
            "nameLocation": "middle",
            "nameGap": 50,
            "min": ymin,
            "max": ymax,
            "axisLabel": {"fontSize": 11, "color": "#333", "fontFamily": "Arial"},
            "axisLine": {"lineStyle": {"color": BAIN_GRAY, "width": 1}},
            "splitLine": {"show": False},
            "nameTextStyle": {"color": BAIN_PRIMARY, "fontSize": 12, "fontWeight": "bold", "fontFamily": "Arial"},
        },
        "grid": {
            "left": "12%",
            "right": "8%",
            "top": "15%",
            "bottom": "20%",
        },
        "series": series_list,
    }
    
    opt_json = _json.dumps(echarts_opt, ensure_ascii=False)
    
    # Build footer with size legend
    size_legend = "<strong>Bubble Size:</strong> Size represents MAU (Daily Active Users)"
    if footer_text:
        footer_content = size_legend + "<br>" + footer_text
    else:
        footer_content = size_legend
    
    html = (
        "<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1.0'>"
        f"<title>{_jesc(title)}</title>"
        "<style>"
        "* { margin: 0; padding: 0; box-sizing: border-box; }"
        "html, body { width: 100%; height: 100%; font-family: Arial, sans-serif; background: #fff; }"
        "#chart { width: 100%; height: calc(100vh - 100px); }"
        "#footer { "
        "  position: fixed; bottom: 0; left: 0; right: 0; "
        "  height: 100px; padding: 12px 24px; "
        f"  background: #f9f9f9; border-top: 1px solid #e8e8e8; "
        f"  color: #666; font-size: 12px; line-height: 1.6; font-family: Arial, sans-serif; "
        "  overflow-y: auto; "
        "}"
        "</style>"
        "</head><body>"
        "<div id='chart'></div>"
        f"<div id='footer'>{_jesc(footer_content)}</div>"
        "<script src='https://assets.pyecharts.org/assets/v6/echarts.min.js'></script>"
        "<script>"
        "(function(){"
        "  if(!window.echarts) { "
        "    document.getElementById('chart').innerHTML = 'ECharts loading failed'; "
        "    return; "
        "  }"
        "  var chart = echarts.init(document.getElementById('chart'), 'white', {renderer: 'canvas', locale: 'EN'});"
        f"  var option = {opt_json};"
        "  for(var i = 0; i < option.series.length; i++) {"
        "    var s = option.series[i];"
        "    if(s.tooltip && typeof s.tooltip.formatter === 'string') {"
        "      try { s.tooltip.formatter = eval('(' + s.tooltip.formatter + ')'); } catch(e) {}"
        "    }"
        "    if(s.label && typeof s.label.formatter === 'string') {"
        "      try { s.label.formatter = eval('(' + s.label.formatter + ')'); } catch(e) {}"
        "    }"
        "    if(s.symbolSize && typeof s.symbolSize === 'string') {"
        "      try { s.symbolSize = eval('(' + s.symbolSize + ')'); } catch(e) {}"
        "    }"
        "  }"
        "  chart.setOption(option);"
        "  window.addEventListener('resize', function() { chart.resize(); });"
        "})();"
        "</script>"
        "</body></html>"
    )
    
    meta = {
        "chart_id": "Bain_Bubble",
        "n_points": len(rows),
        "color_groups": len(color_groups),
        "x_mid": x_mid,
        "y_mid": y_mid,
    }
    
    return ChartResult(html=html, spec={}, warnings=[], meta=meta)
