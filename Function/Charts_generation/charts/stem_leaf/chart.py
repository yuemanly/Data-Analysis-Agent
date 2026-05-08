"""
茎叶图 Stem-and-Leaf Plot - 分布
图表分类: 分布 Distribution | 书章节: Ch5
感知排名: ★★☆☆☆

统一接口:
    generate(df, mapping, options) -> ChartResult
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from collections import defaultdict

import pandas as pd

_PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from charts.base import ChartResult

__all__ = ["generate"]

_DATA_FMT = "value列（单列数值）"
_DESC = "茎叶图，文本格式展示数据分布，保留原始数值。"


def _auto_col(df: pd.DataFrame, *hints: str) -> Optional[str]:
    """根据提示自动查找匹配的列名。
    
    策略：
    1. 精确匹配 hints 中的任何一个
    2. 模糊匹配（包含关系）
    3. 类型匹配：根据 hint 的语义推断类型
    4. 自动推断：无 hints 时返回第一个合适的列
    """
    strs = [c for c in df.columns if df[c].dtype == object]
    nums = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    col_lower = {c.lower(): c for c in df.columns}
    
    # 1. 精确匹配 hints
    for h in hints:
        h_lower = h.lower()
        if h_lower in col_lower:
            return col_lower[h_lower]
    
    # 2. 模糊匹配（包含关系）
    for h in hints:
        h_lower = h.lower()
        for col in df.columns:
            col_lower_name = col.lower()
            if h_lower in col_lower_name or col_lower_name in h_lower:
                return col
    
    # 3. 类型匹配：根据 hint 的语义推断应该是什么类型
    if hints:
        hint = hints[0].lower()
        # 字符串类型的 hints
        if any(kw in hint for kw in ["source", "target", "label", "name", "group", "category", "phase", "row", "col", "path", "text", "word", "location", "geo"]):
            if strs:
                return strs[0]
            if nums:
                return nums[0]
        # 数值类型的 hints
        elif any(kw in hint for kw in ["value", "size", "amount", "count", "frequency", "score", "rank", "actual", "target", "range"]):
            if nums:
                return nums[0]
            if strs:
                return strs[0]
        # 通用的 x/y：x 通常是类别（字符串），y 通常是数值
        elif hint == "x":
            if strs:
                return strs[0]
            if nums:
                return nums[0]
        elif hint == "y":
            if nums:
                return nums[0]
            if strs:
                return strs[0]
    
    # 4. 无 hints 时自动推断
    if not hints:
        if strs:
            return strs[0]
        if nums:
            return nums[0]
    
    return None


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
table td,table th{{border:1px solid #ddd;padding:6px 14px;text-align:left}}
table th{{background:#f5f5f5;font-weight:600}}
</style></head>
<body><div class="chart-wrap">
<h1>{title}</h1><div class="subtitle">{chart_name} | text</div>
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
    value: str = "value",
    title: str = "茎叶图",
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

    value_col = mapping.get("value") or value
    title = options.get("title", title)

    _value = _auto_col(df, value_col, "value", "分数", "年龄", "价格", "num")

    if _value is None or _value not in df.columns:
        warnings.append(f"找不到必填字段 [value]")
        return ChartResult(warnings=warnings)

    vals = sorted(df[_value].astype(float).tolist())
    if not vals:
        warnings.append("无有效数值数据")
        return ChartResult(warnings=warnings)

    digits = len(str(int(max(vals))))
    fmt = "{:0>" + str(digits) + "d}"
    stems = defaultdict(list)
    for v in vals:
        stem = int(v // 10)
        leaf = int(v % 10)
        stems[stem].append(leaf)

    html_lines = ["<tr><th>茎(十位)</th><th>叶(个位)</th></tr>"]
    for stem in sorted(stems):
        leaves = " ".join(str(l) for l in sorted(stems[stem]))
        html_lines.append(f"<tr><td>{stem}</td><td>{leaves}</td></tr>")
    table = "<table style='border-collapse:collapse'>" + "".join(html_lines) + "</table>"

    html = _build_html(title, "stem_leaf", "text", _DATA_FMT, _DESC, table)


    meta = {
        "chart_id": "stem_leaf",
        "n_rows": len(df),
        "value_col": _value,
    }

    return ChartResult(html=html, spec={}, warnings=warnings, meta=meta)
