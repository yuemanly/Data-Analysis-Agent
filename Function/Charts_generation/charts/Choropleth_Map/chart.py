"""
弦图 Chord Diagram - 关系图表
图表分类: 关系 Relationship | 书章节: Ch8

统一接口:
    generate(df, mapping, options) -> ChartResult
    
支持两种数据格式：
1. 邻接矩阵：n×n DataFrame，行列名为节点标签，单元格值为关系强度
2. 边列表：source/target/value 三列 DataFrame
"""
import os, sys, json, io
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd

_PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from charts.base import ChartResult

__all__ = ["generate"]

# 麦肯锡配色方案
MCKINSEY_COLORS = [
    "#003D7A",  # 深蓝 - 主色
    "#0084D1",  # 中蓝 - 次色
    "#00A4EF",  # 浅蓝 - 辅色
    "#7FBA00",  # 绿色 - 正向/增长
    "#FFB81C",  # 金色 - 中性/警示
    "#F7630C",  # 橙色 - 警示
    "#DA3B01",  # 红色 - 负向/下降
    "#A4373A",  # 深红 - 强调/危险
    "#6B2C91",  # 紫色 - 特殊/创新
    "#00B4EF",  # 青色 - 补充
]

_DATA_FMT = "邻接矩阵（n×n）或边列表（source/target/value）"
_DESC = "节点环状排列，弧线粗细表示关系强度。支持高亮特定节点或关系。"


def _auto_col(df: pd.DataFrame, *hints: str, exclude: set = None) -> Optional[str]:
    """根据提示自动查找匹配的列名。"""
    exclude = exclude or set()
    strs = [c for c in df.columns if df[c].dtype == object and c not in exclude]
    nums = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c not in exclude]
    col_lower = {c.lower(): c for c in df.columns if c not in exclude}
    
    # 1. 精确匹配 hints
    for h in hints:
        h_lower = h.lower()
        if h_lower in col_lower:
            return col_lower[h_lower]
    
    # 2. 模糊匹配（包含关系）
    for h in hints:
        h_lower = h.lower()
        for col in df.columns:
            if col in exclude:
                continue
            col_lower_name = col.lower()
            if h_lower in col_lower_name or col_lower_name in h_lower:
                return col
    
    # 3. 类型匹配
    if hints:
        hint = hints[0].lower()
        if any(kw in hint for kw in ["source", "target", "label", "name", "group"]):
            if strs:
                return strs[0]
            if nums:
                return nums[0]
        elif any(kw in hint for kw in ["value", "size", "amount", "count"]):
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


def _detect_format(df: pd.DataFrame) -> Tuple[str, Optional[str], Optional[str], Optional[str]]:
    """检测数据格式：邻接矩阵 或 边列表。
    
    返回: (format_type, source_col, target_col, value_col)
    """
    # 策略1：检查是否为邻接矩阵（行列名相同）
    if df.index.name or (hasattr(df.index, 'names') and df.index.names[0]):
        # 有行标签
        if set(df.index) == set(df.columns):
            # 行列标签相同 → 邻接矩阵
            return ("adjacency", None, None, None)
    
    # 策略2：检查第一列是否为节点标签（字符串），其余列为数值
    # 这是常见的邻接矩阵格式：第一列是行标签，其余列是数据
    if len(df.columns) > 1:
        first_col = df.columns[0]
        # 检查第一列是否全为字符串
        if df[first_col].dtype == object:
            # 检查其余列是否全为数值
            remaining_cols = df.columns[1:]
            all_numeric = all(pd.api.types.is_numeric_dtype(df[col]) for col in remaining_cols)
            if all_numeric:
                # 检查第一列的值是否与其余列名有重叠（邻接矩阵特征）
                first_col_values = set(df[first_col].astype(str).unique())
                remaining_col_names = set(str(c) for c in remaining_cols)
                # 如果有重叠或第一列值数量接近列数，可能是邻接矩阵
                if len(first_col_values) >= len(remaining_cols) * 0.5:
                    return ("adjacency_with_label_col", first_col, None, None)
    
    # 策略3：检查是否为边列表（source/target/value 三列）
    exclude = set()
    src = _auto_col(df, "source", "from", "起点", exclude=exclude)
    if src:
        exclude.add(src)
        tgt = _auto_col(df, "target", "to", "终点", exclude=exclude)
        if tgt:
            exclude.add(tgt)
            val = _auto_col(df, "value", "amount", "流量", exclude=exclude)
            if val:
                return ("edge_list", src, tgt, val)
    
    # 默认假设为邻接矩阵
    return ("adjacency", None, None, None)


def _edge_list_to_adjacency(df: pd.DataFrame, src_col: str, tgt_col: str, val_col: str) -> pd.DataFrame:
    """将边列表转换为邻接矩阵。"""
    d = df[[src_col, tgt_col, val_col]].copy()
    d[val_col] = pd.to_numeric(d[val_col], errors="coerce").fillna(0)
    d = d[d[val_col] > 0].dropna()
    
    nodes = sorted(set(d[src_col].astype(str).values) | set(d[tgt_col].astype(str).values))
    n = len(nodes)
    matrix = pd.DataFrame(0.0, index=nodes, columns=nodes)
    
    for _, row in d.iterrows():
        src_val = str(row[src_col])
        tgt_val = str(row[tgt_col])
        val = float(row[val_col])
        if src_val in matrix.index and tgt_val in matrix.columns:
            matrix.loc[src_val, tgt_val] = val
    
    return matrix


def _build_chord_html(
    matrix: pd.DataFrame,
    title: str,
    highlight_node: Optional[str] = None,
    highlight_color: str = "#003D7A"
) -> str:
    """使用 D3.js 构建交互式弦图 HTML。"""
    
    nodes = list(matrix.index)
    n = len(nodes)
    
    # 构建 D3 格式的数据
    links = []
    for i, src in enumerate(nodes):
        for j, tgt in enumerate(nodes):
            val = float(matrix.iloc[i, j])
            if val > 0:
                links.append({
                    "source": i,
                    "target": j,
                    "value": val
                })
    
    # 节点颜色：高亮节点用特殊颜色，其他循环使用麦肯锡配色
    node_colors = []
    for node in nodes:
        if highlight_node and node == highlight_node:
            node_colors.append(highlight_color)
        else:
            idx = nodes.index(node) % len(MCKINSEY_COLORS)
            node_colors.append(MCKINSEY_COLORS[idx])
    
    # 转换为 JSON
    data = {
        "nodes": [{"id": node, "color": color} for node, color in zip(nodes, node_colors)],
        "links": links
    }
    
    data_json = json.dumps(data)
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: "Heiti SC", "Microsoft YaHei", sans-serif;
            background: #fafafa;
            padding: 40px;
        }}
        .container {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            padding: 24px;
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            color: #222;
            font-size: 22px;
            margin-bottom: 6px;
        }}
        .subtitle {{
            color: #888;
            font-size: 13px;
            margin-bottom: 24px;
        }}
        #chord-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 600px;
            background: white;
            border-radius: 8px;
            margin: 20px 0;
        }}
        svg {{
            max-width: 100%;
            height: auto;
        }}
        .chord {{
            fill-opacity: 0.67;
            stroke: none;
        }}
        .chord:hover {{
            fill-opacity: 0.8;
        }}
        .node-label {{
            font-size: 12px;
            font-weight: 500;
            text-anchor: middle;
            pointer-events: none;
        }}
        .tooltip {{
            position: absolute;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            display: none;
            z-index: 1000;
        }}
        .legend {{
            margin-top: 24px;
            padding: 16px;
            background: #f5f5f5;
            border-radius: 8px;
        }}
        .legend-title {{
            font-weight: 600;
            margin-bottom: 12px;
            color: #333;
        }}
        .legend-item {{
            display: inline-block;
            margin-right: 20px;
            margin-bottom: 8px;
            font-size: 12px;
        }}
        .legend-color {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 2px;
            margin-right: 6px;
            vertical-align: middle;
        }}
        .info {{
            margin-top: 20px;
            padding: 16px;
            background: #f9f9f9;
            border-left: 4px solid #0084D1;
            border-radius: 4px;
            font-size: 13px;
            color: #555;
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="subtitle">弦图 Chord Diagram | D3.js</div>
        
        <div id="chord-container"></div>
        
        <div class="legend">
            <div class="legend-title">节点颜色</div>
            <div id="legend-content"></div>
        </div>
        
        <div class="info">
            <strong>说明：</strong>节点沿圆周排列，弧线粗细表示关系强度。
            将鼠标悬停在弧线上查看详细信息。
        </div>
    </div>
    
    <div class="tooltip" id="tooltip"></div>
    
    <script>
        const data = {data_json};
        const width = 800;
        const height = 800;
        const innerRadius = Math.min(width, height) * 0.3;
        const outerRadius = innerRadius + 30;
        
        const svg = d3.select("#chord-container")
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .attr("viewBox", [-width / 2, -height / 2, width, height]);
        
        const g = svg.append("g");
        
        // 计算弦图布局
        const chord = d3.chord()
            .padAngle(0.05)
            .sortSubgroups(d3.descending);
        
        // 构建邻接矩阵
        const matrix = Array(data.nodes.length).fill(0).map(() => Array(data.nodes.length).fill(0));
        data.links.forEach(link => {{
            matrix[link.source][link.target] = link.value;
        }});
        
        const chords = chord(matrix);
        
        // 绘制弧线
        const arc = d3.arc()
            .innerRadius(innerRadius)
            .outerRadius(outerRadius);
        
        const ribbon = d3.ribbon()
            .source(d => d.source)
            .target(d => d.target);
        
        // 绘制节点弧
        g.selectAll("g")
            .data(chords.groups)
            .join("g")
            .append("path")
            .attr("fill", (d, i) => data.nodes[i].color)
            .attr("stroke", (d, i) => d3.rgb(data.nodes[i].color).darker())
            .attr("d", arc);
        
        // 绘制弦
        g.selectAll(".chord")
            .data(chords)
            .join("path")
            .attr("class", "chord")
            .attr("d", ribbon)
            .attr("fill", (d, i) => {{
                const sourceColor = data.nodes[d.source.index].color;
                return d3.rgb(sourceColor).copy({{opacity: 0.6}});
            }})
            .attr("stroke", (d, i) => {{
                const sourceColor = data.nodes[d.source.index].color;
                return d3.rgb(sourceColor).darker();
            }})
            .on("mouseover", function(event, d) {{
                const tooltip = document.getElementById("tooltip");
                const sourceName = data.nodes[d.source.index].id;
                const targetName = data.nodes[d.target.index].id;
                const value = matrix[d.source.index][d.target.index];
                tooltip.innerHTML = `<strong>${{sourceName}} → ${{targetName}}</strong><br>强度: ${{value.toFixed(2)}}`;
                tooltip.style.display = "block";
                tooltip.style.left = (event.pageX + 10) + "px";
                tooltip.style.top = (event.pageY + 10) + "px";
                d3.select(this).attr("fill-opacity", 0.9);
            }})
            .on("mousemove", function(event) {{
                const tooltip = document.getElementById("tooltip");
                tooltip.style.left = (event.pageX + 10) + "px";
                tooltip.style.top = (event.pageY + 10) + "px";
            }})
            .on("mouseout", function() {{
                document.getElementById("tooltip").style.display = "none";
                d3.select(this).attr("fill-opacity", 0.67);
            }});
        
        // 绘制节点标签
        g.selectAll(".node-label")
            .data(chords.groups)
            .join("text")
            .attr("class", "node-label")
            .attr("dy", "0.35em")
            .attr("transform", (d, i) => {{
                const angle = (d.startAngle + d.endAngle) / 2;
                const x = Math.cos(angle - Math.PI / 2) * (outerRadius + 40);
                const y = Math.sin(angle - Math.PI / 2) * (outerRadius + 40);
                return `translate(${{x}},${{y}})rotate(${{angle * 180 / Math.PI - 90}})`;
            }})
            .text((d, i) => data.nodes[i].id)
            .attr("fill", "#333")
            .attr("font-weight", "500");
        
        // 生成图例
        const legendContent = document.getElementById("legend-content");
        data.nodes.forEach(node => {{
            const item = document.createElement("div");
            item.className = "legend-item";
            item.innerHTML = `<span class="legend-color" style="background-color: ${{node.color}}"></span>${{node.id}}`;
            legendContent.appendChild(item);
        }});
    </script>
</body>
</html>"""
    
    return html


def generate(
    df: pd.DataFrame = None,
    mapping: Dict[str, str] = None,
    options: Dict[str, Any] = None,
    # ── 向后兼容 ──────────────────────────────
    excel_path: str = None,
    source: str = "source",
    target: str = "target",
    value: str = "value",
    title: str = "弦图",
    **kwargs
) -> ChartResult:
    """生成弦图。
    
    支持两种数据格式：
    1. 邻接矩阵：n×n DataFrame，行列名为节点标签
    2. 边列表：source/target/value 三列 DataFrame
    """
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

    title = options.get("title", title)
    highlight_node = options.get("highlight_node")
    highlight_color = options.get("highlight_color", "#003D7A")

    # 检测数据格式
    fmt, src_col, tgt_col, val_col = _detect_format(df)

    if fmt == "adjacency_with_label_col":
        # 邻接矩阵格式：第一列是节点标签，其余列是数据
        label_col = src_col  # 重用 src_col 存储标签列名
        # 将第一列设置为索引
        matrix = df.set_index(label_col).copy()
        # 确保行列名相同
        if not (set(matrix.index) == set(matrix.columns)):
            warnings.append("邻接矩阵的行列标签不匹配")
            return ChartResult(warnings=warnings)
    elif fmt == "edge_list":
        # 边列表格式
        src_col = mapping.get("source") or src_col or source
        tgt_col = mapping.get("target") or tgt_col or target
        val_col = mapping.get("value") or val_col or value

        _src = _auto_col(df, src_col, "source", "起点", "from")
        _tgt = _auto_col(df, tgt_col, "target", "终点", "to")
        _val = _auto_col(df, val_col, "value", "流量", "amount")

        if _src is None or _src not in df.columns:
            warnings.append(f"找不到必填字段 [source]")
            return ChartResult(warnings=warnings)
        if _tgt is None or _tgt not in df.columns:
            warnings.append(f"找不到必填字段 [target]")
            return ChartResult(warnings=warnings)
        if _val is None or _val not in df.columns:
            warnings.append(f"找不到必填字段 [value]")
            return ChartResult(warnings=warnings)

        # 转换为邻接矩阵
        matrix = _edge_list_to_adjacency(df, _src, _tgt, _val)
    else:
        # 邻接矩阵格式
        matrix = df.copy()
        # 确保行列名相同
        if not (set(matrix.index) == set(matrix.columns)):
            warnings.append("邻接矩阵的行列标签不匹配")
            return ChartResult(warnings=warnings)

    if matrix.empty:
        return ChartResult(warnings=["无有效数据"])

    # 验证数据
    try:
        matrix = matrix.astype(float)
    except Exception as e:
        return ChartResult(warnings=[f"数据类型转换失败: {e}"])

    # 生成 HTML
    html = _build_chord_html(matrix, title, highlight_node, highlight_color)

    meta = {
        "chart_id": "chord_diagram",
        "n_nodes": len(matrix),
        "n_edges": (matrix > 0).sum().sum(),
        "format": fmt,
    }
    return ChartResult(html=html, spec={}, warnings=warnings, meta=meta)
