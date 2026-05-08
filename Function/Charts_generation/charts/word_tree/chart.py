"""
词语树 Word Tree - 文本
图表分类: 文本 Text | 书章节: Ch8
感知排名: ★★★☆☆

统一接口:
    generate(df, mapping, options) -> ChartResult
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import base64
import io

import pandas as pd

_PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from charts.base import ChartResult

__all__ = ["generate"]

FONT_PATH = os.environ.get("CHARTS_FONT_PATH") or os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "AlibabaPuHuiTi-3-55-Regular.ttf"
)

_DATA_FMT = "text列（文本字符串）"
_DESC = "以根词为中心，词语越像树杈一样展开，展示词语包含关系。"


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
        if any(kw in hint for kw in ["source", "target", "label", "name", "group", "category", "phase", "row", "col", "path", "text", "word", "location", "geo", "item", "start", "end"]):
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
</style></head>
<body><div class="chart-wrap">
<h1>{title}</h1><div class="subtitle">{chart_name} | matplotlib+HTML</div>
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
    text: str = "text",
    root: str = "根词",
    title: str = "词语树",
    figsize: tuple = (14, 7),
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

    text_col = mapping.get("text") or text
    title = options.get("title", title)
    root = options.get("root", root)
    figsize = options.get("figsize", figsize)

    _text = _auto_col(df, text_col, "text", "文本内容", "text", "content", "words")

    if _text is None or _text not in df.columns:
        warnings.append(f"找不到必填字段 [text]")
        return ChartResult(warnings=warnings)

    text_val = " ".join(df[_text].astype(str).tolist())
    words = text_val.replace(",", " ").split()

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fp = plt.matplotlib.font_manager.FontProperties(fname=FONT_PATH) if os.path.exists(FONT_PATH) else "sans-serif"
    fig, ax = plt.subplots(figsize=figsize)
    ax.text(0.5, 0.5, root, ha="center", va="center",
            fontsize=28, fontweight="bold", fontproperties=fp,
            transform=ax.transAxes)

    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    sorted_w = sorted(freq.items(), key=lambda x: -x[1])[:20]
    y_positions = [0.3 + i * 0.05 for i in range(len(sorted_w))]
    for (w, f), y in zip(sorted_w, y_positions):
        ax.text(0.5 + 0.3, y, f"{w}({f})",
                fontsize=10, ha="left", va="center",
                fontproperties=fp, transform=ax.transAxes)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title(title, fontsize=14, fontproperties=fp)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)

    embed = f'<img src="data:image/png;base64,{img_b64}" style="max-width:100%">'
    html = _build_html(title, "word_tree", "matplotlib+HTML", _DATA_FMT, _DESC, embed)


    meta = {
        "chart_id": "word_tree",
        "n_rows": len(df),
        "text_col": _text,
        "root": root,
    }

    return ChartResult(html=html, spec={}, warnings=warnings, meta=meta)
