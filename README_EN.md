# Business Analyst Agent

<p align="center">
  <img src="./Images/Banner.png" alt="Business Analyst Agent Banner" width="100%" />
</p>

<p align="right"><a href="./README.md">中文</a></p>

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![Flask](https://img.shields.io/badge/Backend-Flask-black.svg)
![Plotly](https://img.shields.io/badge/Visualization-Plotly-3F4F75.svg)
![LLM](https://img.shields.io/badge/LLM-OpenAI%20Compatible-green.svg)
![Charts](https://img.shields.io/badge/Charts-43_Types-orange.svg)
![License](https://img.shields.io/badge/License-Apache%202.0-yellow.svg)

> An AI Agent built for business analytics.  
> After connecting to a data source, users can ask questions in natural language and the system will automatically:
>
> - Detect schema
> - Generate & run SQL
> - Generate charts
> - Produce concise business insights

---

## ✨ Overview

**Business Analyst Agent** is a conversational business data analysis system.  
Upload an Excel/CSV file or connect to a database, then ask questions like chatting:

```text
How does sales trend over the last 3 months?
Which region has the highest profit?
Generate a user growth chart.
```

The system will automatically:

1. Understand intent
2. Inspect data schema
3. Generate SQL
4. Execute queries
5. Recommend appropriate charts
6. Summarize insights

It also supports **SSE (Server-Sent Events)** streaming so you can see the analysis progress in real time.

---

## 🚀 Key Features

### 🧠 Natural Language Analytics
No need to write SQL manually. The agent turns plain language into SQL + results + insights.

### 🔌 Multiple Data Sources
Supported:

- Excel
- CSV
- SQLite
- MySQL
- PostgreSQL
- SQL Server

Planned:

- DuckDB
- Spark

### 📊 Smart Chart Recommendation (43 Types)
Built-in support for **43 chart types**, covering:

- Comparing
- Time / Trend
- Distribution
- Relationship
- Part-to-Whole
- Geospatial

The agent selects charts automatically based on the query result.

### ⚡ SSE Real-time Feedback
Streaming progress like:

```text
[1/4] Reading schema...
[2/4] Generating SQL...
[3/4] Running query...
[4/4] Creating chart & insights...
```

### 🤖 Configurable LLM Providers
Built-in support:

- **DeepSeek** (default: `deepseek-chat`)
- **OpenAI** (default: `gpt-4o-mini`)
- **Anthropic Claude** (default: `claude-3-5-haiku-20241022`)

Also supports any **OpenAI SDK compatible API** via custom:

- `base_url`
- `model`
- `api_key`

---

## 🖼️ UI Preview

### Data Preview
![Data Preview](Images/Data_preview.png)

---

### Data Query
![Data Query](Images/Data_query.png)

---

### Auto Generated Chart
![Auto Generated](Images/Auto_generated_image.png)

---

## Installation

### Option 1: One-Click Install + Launch (Recommended)

#### Windows (PowerShell)

```powershell
iwr -useb https://raw.githubusercontent.com/Zafer-Liu/Data-Analysis-Agent/main/install.ps1 | iex
```

After installation, you can start it in either of the following ways:

- Double-click to run (Windows):
  ```bat
  %USERPROFILE%\data-analysis-agent.bat
  ```
- Or start manually from the project directory:
  ```powershell
  cd $env:USERPROFILE\.data-analysis-agent\Data-Analysis-Agent
  .\.venv\Scripts\activate
  python app.py
  ```

#### macOS / Linux (Shell)

```bash
curl -fsSL https://raw.githubusercontent.com/Zafer-Liu/Data-Analysis-Agent/main/install.sh | sh
```

After installation, launch with:

```bash
data-analysis-agent
```

If you see `command not found`, add `~/.local/bin` to your PATH (in `~/.bashrc` or `~/.zshrc`):

```bash
export PATH="$HOME/.local/bin:$PATH"
```


---

### Option 2: Windows One-click Start (Only if dependencies are already installed)

Run in the project directory:

```bat
start.bat
```

> Note: This option requires Python to be installed and dependencies to be available on your machine (or `start.bat` already handles dependency installation).

---

### Option 3: Manual Start (Universal)

#### 1) Install dependencies

```bash
pip install -r requirements.txt
```

#### 2) Start the service

```bash
python app.py
```

---

## Access URL

```text
http://localhost:5001
```

---

## 🛠 Slash Commands

| Command | Status | Description |
|---|---|---|
| `/chart` | ✅ | Prefer chart generation |
| `/sql` | ✅ | Execute SQL directly and return a table |
| `/analyze` | 🔲 | Advanced statistical analysis (WIP) |
| `/report` | 🔲 | Export Word/PDF report (WIP) |

---

## 📁 Suggested Project Structure

```text
Business-Analyst-Agent/
│
├── app.py
├── requirements.txt
├── start.bat
│
├── Function/
│   ├── Charts_generation/
│   │   ├── charts/
│   │   └── registry.py
│   ├── SQL/
│   ├── LLM/
│   └── DataSource/
│
├── Images/
└── README.md
```

---

## ⚙️ Configuration

### LLM Setup
If you see “LLM not configured”, open the sidebar ⚙ and fill in:

- API Key
- Base URL (optional)
- Model

Save to apply.

### Adding New Chart Types
1. Add a new chart folder under:
   ```text
   Function/Charts_generation/charts/
   ```
2. Register it in:
   ```python
   Function/Charts_generation/registry.py
   ```
3. Restart the app.

---

## 🗺️ Roadmap

- ✅ Phase 1: Conversational analytics + multi data sources + 43 charts + SSE streaming
- 🔲 Phase 2: Drag-and-drop dashboards
- 🔲 Phase 3: `/report` automated report export (Word/PDF)
- 🔲 Phase 4: DuckDB / Spark support for big data

---

## ❓ FAQ

**Q: It says LLM is not configured.**  
A: Fill in your API key in the sidebar ⚙ and save.

**Q: Chart links disappear after restart.**  
A: Charts are currently stored in memory. Restarting the service clears them. Persistence will be added later.

**Q: How do I add a new chart type?**  
A: Add it under `Function/Charts_generation/charts/` and register it in `registry.py`, then restart.

---

## 📄 License
Apache License 2.0

---

## ⭐ Goal
Make business analytics as easy as chatting.