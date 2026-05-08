# Business Analyst Agent · 智能商业数据分析助手

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](#)
[![Flask](https://img.shields.io/badge/Backend-Flask-black.svg)](#)
[![Plotly](https://img.shields.io/badge/Visualization-Plotly-3F4F75.svg)](#)
[![LLM](https://img.shields.io/badge/LLM-OpenAI%20Compatible-green.svg)](#)
[![Charts](https://img.shields.io/badge/Charts-43_Types-orange.svg)](#)
[![License](https://img.shields.io/badge/License-GPL-yellow.svg)](#)

> 连接数据源，用自然语言提问，AI 自动查询、分析并生成交互式图表。  
> Connect a data source, ask in plain language — AI queries, analyzes, and generates interactive charts.

---

## 目录 / Table of Contents

- [项目简介](#项目简介)
- [功能特性](#功能特性)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [使用说明](#使用说明)
- [斜杠命令](#斜杠命令)
- [LLM 模型配置](#llm-模型配置)
- [支持的图表类型](#支持的图表类型)
- [路线图](#路线图)
- [常见问题](#常见问题)
- [许可证](#许可证)

---

## 项目简介

**Business Analyst Agent** 是一个面向商业分析师的对话式数据分析平台。

用户上传 Excel/CSV 文件或连接 SQL 数据库后，可以用自然语言直接提问。Agent 会自动：

1. **理解 schema** — 读取表结构和字段类型
2. **生成 SQL** — 针对问题编写精确查询
3. **生成图表** — 从 43 种图表中选择最合适的类型并渲染
4. **给出洞察** — 附上简洁的商业分析结论

整个过程通过 SSE 流式输出，每一步实时可见。

---

## 功能特性

### 对话式数据分析
- 自然语言提问，无需写 SQL
- 多轮对话，支持追问和深入分析
- 工具调用步骤实时展示（读取结构 → 执行查询 → 生成图表）

### 多数据源支持
- **Excel / CSV** — 直接上传，自动加载到 SQLite in-memory
- **SQL 数据库** — 支持 MySQL、PostgreSQL、SQLite、SQL Server（SQLAlchemy 连接字符串）

### 43 种专业图表
- 覆盖对比、趋势、分布、占比、关系、地理 6 大类
- 基于 `Function/Charts_generation/charts/registry.py` 动态加载，Agent 自动感知全量图表
- 图表以 iframe 内嵌展示，支持 Plotly 交互（缩放、悬停、筛选）

### 灵活的模型配置
- 内置支持 **DeepSeek / OpenAI / Anthropic Claude**
- 支持任意 OpenAI SDK 兼容接口（自定义 base_url + model + api_key）
- 所有配置通过 UI 设置面板完成，无需改代码

### 斜杠命令系统
- `/chart` — 优先生成可视化图表
- `/sql` — 直接执行 SQL 并展示结果表格

---

## 快速开始

### 环境要求
- Python 3.8+
- Windows（提供 `start.bat` 一键启动）

### 安装与启动

**Windows — 双击启动（推荐）**
```
start.bat
```
脚本会自动创建虚拟环境、安装依赖、检测端口冲突，然后启动服务。

**手动启动**
```bash
pip install -r requirements.txt
python app.py
```

### 访问地址
```
http://localhost:5001
```

### 快速上手流程

1. 打开 `http://localhost:5001`
2. 点击 **⚙ 模型设置** → 配置 LLM API Key
3. 点击 **📂 上传 Excel / CSV** 或 **🗄️ 连接 SQL 数据库**
4. 在对话框输入问题，例如：
   - `各品类的销售额是多少？`
   - `/chart 近 12 个月的销售趋势`
   - `哪个地区的利润率最高，用图表展示`

---

## 项目结构

```
Business_Analytics_Agent/
├── api/                              # Flask Blueprint 路由层
│   ├── __init__.py                   #   create_app() 工厂函数
│   ├── state.py                      #   共享单例：session_manager / config_manager / chart_store
│   ├── chat.py                       #   /api/session/*/chat（SSE 流）、/api/chart/<id>
│   ├── datasource.py                 #   /api/session/*/upload、connect-db、datasource
│   └── models.py                     #   /api/models/*
│
├── agent/
│   └── agent.py                      #   BusinessAgent：工具调用循环，动态加载 43 种图表
│
├── data/
│   ├── connector.py                  #   ExcelDataSource / CSVDataSource / SQLDataSource
│   └── session.py                    #   ChatSession / SessionManager（内存）
│
├── Function/
│   └── Charts_generation/            # 图表生成模块
│       ├── chart_generate.py         #   统一入口：generate_chart()
│       └── charts/                   #   43 种图表各自独立目录
│           ├── registry.py           #   图表元数据注册表（Agent 启动时动态读取）
│           ├── base.py               #   ChartResult / FieldMapping 数据类
│           ├── color_schemes.py      #   配色方案（McKinsey / BCG / Bain / EY）
│           └── <ChartType>/          #   每种图表含 chart.py + __init__.py
│
├── LLM/
│   ├── llm_config_manager.py         #   LLMConfigManager + get_llm_client()
│   ├── llm_recommender.py            #   图表推荐引擎
│   └── llm_config.json               #   运行时配置（含 API Key，勿入 git）
│
├── templates/
│   ├── agent_chat.html               #   ★ 对话主界面（SSE + 图表内嵌）
│   ├── js/                           #   前端脚本
│   └── styles/                       #   样式表
│
├── Test/
│   ├── test_smoke_all.py
│   └── diagnose.py
│
├── app.py                      # ★ 主入口
├── requirements.txt
├── start.bat                         # Windows 一键启动
└── test.bat
```

---

## 使用说明

### 数据源

| 类型 | 操作 | 说明 |
|------|------|------|
| Excel / CSV | 侧栏 → 📂 上传文件 | 自动加载为 SQLite，支持多 Sheet |
| SQL 数据库 | 侧栏 → 🗄️ 连接数据库 | 输入 SQLAlchemy 连接字符串 |

**连接字符串示例：**
```
mysql+pymysql://user:pass@host:3306/dbname
postgresql://user:pass@host:5432/dbname
sqlite:///./data.db
```

### 提问技巧

- 直接描述分析目标，Agent 会自动决定是否查询和出图
- 使用 `/chart` 命令强制优先生成图表
- 点击 **🗂 数据结构** 按钮查看当前数据源的表和字段

---

## 斜杠命令

在输入框键入 `/` 唤起命令菜单，或直接输入命令前缀自动触发。

| 命令 | 状态 | 行为 |
|------|------|------|
| `/chart` | ✅ 可用 | 优先生成图表，Agent 聚焦于可视化输出 |
| `/sql` | ✅ 可用 | 直接执行 SQL，结果格式化为表格 |
| `/analyze` | 🔲 开发中 | 深度统计分析：趋势、异常、相关性 |
| `/report` | 🔲 开发中 | 输出结构化分析报告（Word / PDF） |

---

## LLM 模型配置

点击侧栏 **⚙** 图标打开模型设置面板。

### 内置提供商

| 提供商 | 默认 Model | 说明 |
|--------|-----------|------|
| DeepSeek | `deepseek-chat` | 推荐，性价比高，中文优秀 |
| OpenAI | `gpt-4o-mini` | 官方 API |
| Anthropic Claude | `claude-3-5-haiku-20241022` | 适合复杂推理 |

### 自定义模型

支持任意 OpenAI SDK 兼容接口：填入名称、Base URL、Model ID、API Key 即可。

---

## 支持的图表类型

> 共 **43 种**，以 `Function/Charts_generation/charts/registry.py` 为准。  
> Agent 启动时自动读取，无需手动维护此列表。

### 对比类 COMPARING
`Bar_Chart` · `Grouped_Bar_Chart` · `Stacked_Bar_Chart` · `Diverging_Bar_Chart` · `Dot_Plot` · `Bullet_Chart` · `Waffle` · `Marimekko_ABS` · `Marimekko_PCT` · `Sankey_Chart` · `Heatmap` · `Waterfall`

### 时间趋势类 TIME
`Line_Chart` · `Area_Chart` · `Stacked_Area_Chart` · `Slope_Chart` · `Bump_Chart` · `Sparkline` · `Cycle_Chart` · `Circular_Line_Chart` · `Horizon_Chart` · `Connected_Scatter`

### 分布类 DISTRIBUTION
`Histogram_Pareto_chart` · `Box-and-Whisker_Plot` · `Violin_Chart` · `Ridgeline_Plot` · `Beeswarm_Plot` · `Pyramid_Chart` · `Error_Bar_Chart` · `stem_leaf`

### 关系类 RELATIONSHIP
`Scatter_Plot` · `Bubble_Plot` · `Chord_Diagram` · `Arc_Chart` · `Network_Diagram` · `Parallel_Coordinates_Plot`

### 占比类 PART-TO-WHOLE
`Pie_Chart` · `Nightingale_Chart` · `Treemap` · `Sunburst_Diagram`

### 地理类 GEOSPATIAL
`Flow_Map` · `Dot_Density_Map` · `Choropleth_Map`

---

## 路线图

| Phase | 状态 | 内容 |
|-------|------|------|
| Phase 1 · 对话界面 | ✅ 完成 | SSE 流式输出、多数据源、43 种图表、模型管理 |
| Phase 2 · 业务看板 | 🔲 待开发 | 多图拖拽仪表板，可分享只读链接 |
| Phase 3 · 报告输出 | 🔲 待开发 | `/report` 一键生成 Word/PDF 分析报告 |
| Phase 4 · 大数据 | 🔲 规划中 | DuckDB / Spark，支持亿级数据集 |

---

## 常见问题

**Q: 启动后提示"未配置任何 LLM 模型"？**  
A: 点击侧栏 ⚙ → 内置提供商 → 填入 API Key → 保存。

**Q: 上传 Excel 后提示解析失败？**  
A: 确认文件格式为 `.xlsx` / `.xls` / `.csv`，且第一行为表头。

**Q: 图表生成失败，提示 Chart type not found？**  
A: `chart_type` 必须与 `registry.py` 中的 `chart_id` 完全一致（区分大小写）。

**Q: 重启服务后图表链接失效？**  
A: 图表 HTML 存储在内存，重启后需重新生成。持久化存储在 Phase 2 中实现。

**Q: 如何新增图表类型？**  
A: 在 `Function/Charts_generation/charts/` 下新建目录，实现 `generate()` 函数，在 `registry.py` 注册后重启服务，Agent 自动感知。

---

## 许可证

本项目基于 **GPL License** 开源。
