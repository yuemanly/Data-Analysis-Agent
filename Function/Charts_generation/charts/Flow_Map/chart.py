"""
动态流向图 Flow Map - 地理
图表分类: 地理 Geographic | 书章节: Ch7
感知排名: ★★★★★

统一接口:
    generate(df, mapping, options) -> ChartResult

动态流向图用箭头和涟漪效果表示地点间的流向关系。
支持自动检测起点、终点、流量列。
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

_PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from charts.base import ChartResult

__all__ = ["generate"]

_DATA_FMT = "from列(起点) + to列(终点) + value列(流量)"
_DESC = "用箭头和涟漪效果表示地点间的流向关系，支持动态效果。"


def _is_string_col(s: pd.Series) -> bool:
    if pd.api.types.is_numeric_dtype(s):
        return False
    if pd.api.types.is_datetime64_any_dtype(s):
        return False
    return True


def _detect_string_cols(df: pd.DataFrame, exclude: set) -> list:
    """检测所有字符串列。"""
    cols = []
    for c in df.columns:
        if c not in exclude and _is_string_col(df[c]):
            cols.append(c)
    return cols


def _detect_value_col(df: pd.DataFrame, exclude: set, hint: str = None) -> Optional[str]:
    """识别数值列。"""
    if hint:
        for c in df.columns:
            if c not in exclude and c.lower() == hint.lower():
                return c
    for c in df.columns:
        if c not in exclude and pd.api.types.is_numeric_dtype(df[c]):
            return c
    return None


def generate(
    df: pd.DataFrame = None,
    mapping: Dict[str, str] = None,
    options: Dict[str, Any] = None,
    excel_path: str = None,
    frm: str = None,
    to: str = None,
    value: str = "value",
    title: str = "动态流向图",
    maptype: str = "china",
    **kwargs,
) -> ChartResult:
    """
    参数说明：
        frm    : 起点列名
        to     : 终点列名
        value  : 流量列名
        maptype: 'china' | 省名 | 市名
    """
    from pyecharts.charts import Geo
    from pyecharts import options as opts
    from pyecharts.globals import ChartType, SymbolType

    warnings_: list = []
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

    frm_hint = mapping.get("from") or mapping.get("frm") or frm
    to_hint = mapping.get("to") or to
    val_hint = mapping.get("value") or value
    title = options.get("title", title)
    maptype = options.get("maptype", maptype)

    used: set = set()
    
    # 检测起点列
    _from = None
    if frm_hint and frm_hint in df.columns:
        _from = frm_hint
    else:
        str_cols = _detect_string_cols(df, used)
        if str_cols:
            _from = str_cols[0]
    
    if _from:
        used.add(_from)
    
    # 检测终点列
    _to = None
    if to_hint and to_hint in df.columns:
        _to = to_hint
    else:
        str_cols = _detect_string_cols(df, used)
        if str_cols:
            _to = str_cols[0]
    
    if _to:
        used.add(_to)
    
    # 检测流量列
    _value = _detect_value_col(df, used, val_hint)
    if _value:
        used.add(_value)

    if _from is None:
        warnings_.append("找不到起点列 [from]")
        return ChartResult(warnings=warnings_)
    if _to is None:
        warnings_.append("找不到终点列 [to]")
        return ChartResult(warnings=warnings_)
    if _value is None:
        warnings_.append("找不到流量列 [value]")
        return ChartResult(warnings=warnings_)

    # 构建数据
    points: list = []  # (地名, 流量)
    flows: list = []   # (起点, 终点)
    point_dict = {}    # 地名 -> 流量

    for _, row in df.iterrows():
        try:
            frm_name = str(row[_from]).strip()
            to_name = str(row[_to]).strip()
            val = float(row[_value])
            val = round(val, 2)
            
            flows.append((frm_name, to_name))
            
            # 累计流量
            if frm_name not in point_dict:
                point_dict[frm_name] = 0
            if to_name not in point_dict:
                point_dict[to_name] = 0
            point_dict[frm_name] += val
            point_dict[to_name] += val
        except Exception as e:
            warnings_.append(f"行数据解析失败: {e}")
            continue

    if not flows:
        warnings_.append("没有有效流向数据")
        return ChartResult(warnings=warnings_)

    # 构建点数据
    points = [(name, val) for name, val in point_dict.items()]

    # 构建 Geo
    geo = Geo()
    geo.add_schema(maptype=maptype)
    
    # 添加数据点（涟漪效果）
    geo.add(
        series_name="流量",
        data_pair=points,
        type_=ChartType.EFFECT_SCATTER,
        symbol_size=8,
        effect_opts=opts.EffectOpts(scale=2.5, color="#0084D1"),
        label_opts=opts.LabelOpts(is_show=False),
        itemstyle_opts=opts.ItemStyleOpts(color="#0084D1", opacity=0.8),
    )
    
    # 添加流向线（箭头）
    geo.add(
        series_name="流向",
        data_pair=flows,
        type_=ChartType.LINES,
        effect_opts=opts.EffectOpts(
            symbol=SymbolType.ARROW,
            symbol_size=10,
            color="#FFB81C",
        ),
        linestyle_opts=opts.LineStyleOpts(curve=0.2),
        label_opts=opts.LabelOpts(is_show=False),
    )

    geo.set_global_opts(
        title_opts=opts.TitleOpts(
            title=title,
            title_textstyle_opts=opts.TextStyleOpts(
                color="#003D7A", font_size=18,
                font_family="Heiti SC, Microsoft YaHei, sans-serif",
                font_weight="bold",
            ),
        ),
        tooltip_opts=opts.TooltipOpts(
            trigger="item",
            formatter="{b}",
        ),
    )

    raw_html = geo.render_embed()

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: 100%; height: 100%;
  font-family: "Heiti SC", "Microsoft YaHei", sans-serif;
  background: #fff; }}
#header {{
  padding: 14px 24px; background: #fff;
  border-bottom: 1px solid #e8ecf0;
  box-shadow: 0 1px 4px rgba(0,0,0,.05);
}}
#header h1 {{ font-size: 18px; color: #003D7A; font-weight: 700; }}
#header .sub {{ font-size: 12px; color: #999; margin-top: 3px; }}
#chart {{ width: 100%; height: calc(100vh - 60px); }}
</style>
</head>
<body>
<div id="header">
  <h1>{title}</h1>
  <div class="sub">共 {len(points)} 个地点 · {len(flows)} 条流向</div>
</div>
<div id="chart">
{raw_html}
</div>
</body>
</html>"""

    meta = {
        "chart_id": "flow_map",
        "n_rows": len(df),
        "n_points": len(points),
        "n_flows": len(flows),
        "from_col": _from,
        "to_col": _to,
        "value_col": _value,
        "maptype": maptype,
    }

    return ChartResult(html=html, spec={}, warnings=warnings_, meta=meta)
