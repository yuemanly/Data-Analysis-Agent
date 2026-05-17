# Version Development Log

## v1.0
- The project officially released its first stable version
- Supports basic data upload, viewing, analysis, and visualization
- Supports common data sources such as Excel, CSV, and databases
- Enables common data analysis tasks through conversational interaction
- Provides basic chart generation and result export capabilities

---

## v2.0
**May/11/2026**

This update focuses on **stronger analytical capabilities, more consistent presentation, and better export features**.

### 1. Logging System Upgrade
- Added a unified logging system
- Automatically records runtime activity, tool calls, model requests, and exceptions
- Logs rotate daily and are retained for 30 days to help with troubleshooting

### 2. Unified Color Scheme
- Fixed inconsistent color schemes between charts and PPTs
- When users switch brand colors, both charts and reports will update accordingly
- Default color scheme is McKinsey, with support for BCG and others

### 3. Agent Architecture Refactoring
- Split the original single-file Agent into multiple modules
- Improved code maintainability and extensibility
- Makes future feature integration easier

### 4. Internationalization Support
- Added Chinese/English language switching
- Frontend interface can be switched between Chinese and English with one click
- Page text, prompts, and command descriptions are fully adapted

### 5. Slash Command Optimization
- Replaced the general analysis command with more specific commands
- Such as `/decile`, `/tree`, and `/kmeans`
- Makes it easier for users to understand the purpose of each command

### 6. Enhanced Export Features
- Added Excel and Word report export
- Supports generating downloadable files directly from analysis results
- `/export` and `/report` commands enable quick export tasks

### 7. Enhanced Data Cleaning Features
- Added data profiling, missing value handling, winsorization, and trimming
- Supports more flexible data preprocessing workflows
- Cleaned data can be used directly for further analysis

### 8. Data Preview Upgrade
- Replaced the original data structure view with a table preview
- Provides an experience closer to Excel
- Allows quick browsing of tables, fields, and sample data

### 9. Token Usage Tracking
- Added context window and output token statistics
- Users can view token usage directly in the interface
- Helps control model cost and context length

### 10. Thinking Mode Display
- Supports displaying the model’s reasoning process
- Users can view the model’s chain of thought when needed
- Useful for debugging and understanding complex analysis tasks

### 11. Frontend Experience Improvements
- Further modularized the page structure for easier maintenance
- Separated styles and scripts into independent files
- Improved interface stability and responsiveness

---
## v3.0

This upgrade focuses on external ecosystem integration and enhanced business knowledge capabilities, significantly expanding the Agent’s data acquisition abilities and adaptability to different fields.

### 1. MCP Tool Invocation Capability
- Added support for the MCP (Model Context Protocol); Agents can now dynamically invoke external MCP tools.
- Supports the use of calculators, code executors, third-party API wrappers, and other tools to expand analytical capabilities.
- Through a standardized protocol, any tool that complies with MCP specifications can be integrated.
- The entire process of tool invocation is automatically logged for easy debugging and auditing.

### 2. Business Knowledge Base Integration
- Added a business database feature that allows the import of internal company materials, product documentation, industry reports, etc.
- Materials are automatically processed in a vectorized manner to create a searchable knowledge base.
- When performing analyses, Agents automatically retrieve relevant information, enhancing their understanding and insight into specific business scenarios.- Supports multiple formats: Word, Excel, etc., to meet the needs of importing common documents.

### 3. Expansion of data sources: Google Sheets and custom APIs
- Integration with Google Sheets API: Allows direct access to data in Google Sheets as an analysis source.
- Custom database API interface: Provides a generic API adapter.
- All external data sources can be utilized along with a full set of functions such as data cleaning, previewing, and analysis.
