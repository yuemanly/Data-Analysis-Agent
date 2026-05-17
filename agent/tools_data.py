# -*- coding: utf-8 -*-
"""Mixin: data-oriented tools (schema, query, analysis, chart, clean, profile)."""
import re
import sqlite3


class DataToolsMixin:
    """All methods here rely on self.data_source, self._schema_cache,
    self.ppt_color_scheme — defined in BusinessAgent.__init__."""

    # ── Knowledge base lookup ─────────────────────────────────────────────────

    def _tool_query_knowledge(self, question: str) -> str:
        try:
            from Function.Knowledge.knowledge_base import KnowledgeBase
            kb = KnowledgeBase()
            results = kb.search(question)
        except Exception as e:
            return f"Knowledge base unavailable: {e}"

        if not any(results.values()):
            return "No relevant knowledge found."

        lines: list[str] = []

        for m in results["metrics"]:
            lines.append(f"[Metric] {m['name']}")
            if m.get("alias"):
                lines.append(f"  Alias: {m['alias']}")
            if m.get("definition"):
                lines.append(f"  Definition: {m['definition']}")
            if m.get("sql_template"):
                lines.append(f"  SQL template: {m['sql_template']}")
            if m.get("notes"):
                lines.append(f"  Notes: {m['notes']}")

        for r in results["rules"]:
            lines.append(f"[Rule/{r['severity'].upper()}] {r['rule_id']}: {r['description']}")
            if r.get("condition"):
                lines.append(f"  Condition: {r['condition']}")

        for n in results["notes"]:
            lines.append(f"[Context] {n['topic']}: {n['content']}")

        return "\n".join(lines)

    # ── Basic data access ─────────────────────────────────────────────────────

    def _tool_get_schema(self) -> str:
        if not self.data_source:
            return "No data source connected."
        if not self._schema_cache:
            self._schema_cache = self.data_source.get_schema()
        return self._schema_cache

    def _tool_query_data(self, sql: str) -> str:
        if not self.data_source:
            return "No data source. Please connect a database or upload an Excel file first."
        df, error = self.data_source.execute_query(sql)
        if error:
            return f"SQL Error: {error}"
        return self.data_source.format_result(df)

    def _tool_create_analysis_table(self, sql: str, table_name: str = "analysis_data") -> str:
        if not self.data_source:
            return "No data source connected."
        result = self.data_source.create_analysis_table(sql, table_name)
        self._schema_cache = None
        return result

    # ── DataFrame → DataSource writer (backward-compatible) ──────────────────

    def _write_analysis_df(self, df, table_name: str) -> None:
        """Write df into the connected data source as a queryable table.

        Tries the new connector API first; falls back to direct SQLite write
        for older connector.py versions that lack the _df parameter.
        """
        ds = self.data_source

        try:
            ds.create_analysis_table(sql=None, table_name=table_name, _df=df)
            self._schema_cache = None
            return
        except TypeError:
            pass  # old connector — fall through to direct SQLite write

        conn = getattr(ds, "_conn", None)
        if conn is None:
            if getattr(ds, "_cache_conn", None) is None:
                ds._cache_conn = sqlite3.connect(":memory:", check_same_thread=False)
                ds._cache_tables = set()
            conn = ds._cache_conn
            ds._cache_tables.add(table_name)

        df.to_sql(table_name, conn, if_exists="replace", index=False)
        self._schema_cache = None

    # ── Analysis tool ─────────────────────────────────────────────────────────

    def _tool_run_analysis(
        self,
        analysis_name: str,
        sql: str,
        target_column: str,
        groupby_column: str = "",
        n_deciles: int = 10,
    ) -> str:
        if not self.data_source:
            return "No data source connected."

        df, error = self.data_source.execute_query(sql)
        if error:
            return f"SQL Error while fetching data: {error}"
        if df.empty:
            return "Query returned no rows — cannot run analysis."

        try:
            from Function.Analyze.registry import get as get_analysis
            entry = get_analysis(analysis_name)
        except KeyError as exc:
            return str(exc)
        except Exception as exc:
            return f"Failed to load analysis module '{analysis_name}': {exc}"

        run_fn = entry.get("run")
        if run_fn is None:
            return f"Analysis module '{analysis_name}' failed to load."

        try:
            ret = run_fn(
                df=df,
                target_column=target_column,
                groupby_column=groupby_column or None,
                n_deciles=n_deciles,
            )
        except Exception as exc:
            return f"Analysis error: {exc}"

        if len(ret) == 4:
            result_df, breakdown_df, extra_df, markdown = ret
        else:
            result_df, breakdown_df, markdown = ret
            extra_df = None

        try:
            self._write_analysis_df(result_df, "analysis_result")
            if not breakdown_df.empty:
                self._write_analysis_df(breakdown_df, "analysis_breakdown")
            if extra_df is not None and not extra_df.empty:
                _out_tbls = entry.get("output_tables", [])
                extra_table_name = _out_tbls[2] if len(_out_tbls) > 2 else "analysis_roc"
                self._write_analysis_df(extra_df, extra_table_name)
        except Exception as exc:
            return (
                markdown
                + f"\n\n⚠️ **结果表写入失败**：{exc}\n"
                "分析计算已完成，但结果无法存为可查询表格，请联系开发者。"
            )

        if analysis_name == "K_Means" and "cluster" in breakdown_df.columns:
            markdown += self._kmeans_build_labeled(sql, breakdown_df)

        return markdown

    def _kmeans_build_labeled(self, sql: str, breakdown_df) -> str:
        try:
            labeled_sql = re.sub(
                r"(?is)\bSELECT\b.+?\bFROM\b",
                "SELECT *\nFROM",
                sql,
                count=1,
            )
            full_df, err = self.data_source.execute_query(labeled_sql)
            if err or full_df.empty:
                return ""
            if len(full_df) != len(breakdown_df):
                return ""

            labeled_df = full_df.copy().reset_index(drop=True)
            labeled_df["cluster"] = breakdown_df["cluster"].values
            self._write_analysis_df(labeled_df, "cluster_labels")
            self._schema_cache = None

            cols_preview = ", ".join(str(c) for c in labeled_df.columns[:8])
            if len(labeled_df.columns) > 8:
                cols_preview += ", ..."
            return (
                "\n\n---\n"
                "### 📌 数据标签表 `cluster_labels`\n"
                f"已将聚类结果（cluster 列）回写到原始数据，"
                f"生成包含所有原始字段的标签表：\n\n"
                f"**列：** `{cols_preview}`\n\n"
                "可直接用于后续分析，例如：\n"
                "```sql\n"
                "-- 查看各簇的详细记录\n"
                "SELECT * FROM cluster_labels WHERE cluster = 0 LIMIT 20\n\n"
                "-- 统计各簇某字段的均值\n"
                "SELECT cluster, AVG(target_col) AS avg_val FROM cluster_labels GROUP BY cluster\n"
                "```"
            )
        except Exception:
            return ""

    # ── Chart tool ────────────────────────────────────────────────────────────

    def _tool_generate_chart(
        self, chart_type: str, sql: str, field_mapping: dict, title: str = ""
    ) -> dict:
        if not self.data_source:
            return {"error": "No data source connected."}
        df, error = self.data_source.execute_query(sql)
        if error:
            return {"error": f"Data query failed: {error}"}
        if df.empty:
            return {"error": "Query returned no rows — cannot generate chart."}

        from chart_generate import generate_chart as _gen

        options = {"title": title} if title else {}
        result = _gen(
            df=df,
            chart_type=chart_type,
            mapping=field_mapping,
            options=options,
            color_scheme=self.ppt_color_scheme,
        )
        if "error" in result:
            return {"error": result["error"]}
        return {"html": result.get("html", ""), "chart_type": chart_type}

    # ── Table discovery helpers ───────────────────────────────────────────────

    def _discover_all_tables(self) -> list:
        if not self.data_source:
            return []
        df, err = self.data_source.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY rowid"
        )
        if not err and not df.empty:
            return df["name"].tolist()
        schema = self._tool_get_schema()
        return re.findall(r"^Table:\s+(\S+)", schema, re.MULTILINE)

    def _get_first_raw_table(self) -> str:
        tables = self._discover_all_tables()
        raw = [t for t in tables if not t.startswith("analysis_") and t != "cleaned_data"]
        return raw[0] if raw else (tables[0] if tables else "")

    # ── Profile & clean ───────────────────────────────────────────────────────

    def _tool_profile_data(self, table_name: str = "", columns: list = None) -> dict:
        if not self.data_source:
            return {"text": "❌ 请先连接数据源。", "charts": []}

        tname = table_name or self._get_first_raw_table()
        if not tname:
            return {"text": "❌ 数据源中没有可用的表格。", "charts": []}

        df, err = self.data_source.execute_query(f'SELECT * FROM "{tname}"')
        if err or df is None or df.empty:
            return {"text": f"❌ 读取表 '{tname}' 失败：{err}", "charts": []}

        try:
            from Function.Clean.data_profile import profile
            text, charts = profile(df, columns or None)
            return {"text": f"### 数据概况 · `{tname}`\n\n" + text, "charts": charts}
        except Exception as exc:
            return {"text": f"❌ 数据概况生成失败：{exc}", "charts": []}

    def _tool_clean_data(
        self,
        operation: str,
        table_name: str = "",
        columns=None,
        fill_method: str = "mean",
        lower_pct: float = 1.0,
        upper_pct: float = 99.0,
        trim_column: str = "",
        min_val=None,
        max_val=None,
        output_table: str = "cleaned_data",
    ) -> str:
        if not self.data_source:
            return "❌ 请先连接数据源。"

        tname = table_name or self._get_first_raw_table()
        if not tname:
            return "❌ 数据源中没有可用的表格。"

        df, err = self.data_source.execute_query(f'SELECT * FROM "{tname}"')
        if err or df is None or df.empty:
            return f"❌ 读取表 '{tname}' 失败：{err}"

        try:
            if operation == "fill_na":
                from Function.Clean.missing_handler import fill_missing
                cleaned_df, summary = fill_missing(df, fill_method, columns)
            elif operation == "winsorize":
                from Function.Clean.winsorize import winsorize
                cleaned_df, summary = winsorize(df, lower_pct, upper_pct, columns)
            elif operation == "trimming":
                if not trim_column:
                    return "❌ trimming 操作需要指定 trim_column。"
                if min_val is None or max_val is None:
                    return "❌ trimming 操作需要同时指定 min_val 和 max_val。"
                from Function.Clean.trimming import trim
                cleaned_df, summary = trim(df, trim_column, float(min_val), float(max_val))
            else:
                return f"❌ 未知操作 '{operation}'，支持：fill_na / winsorize / trimming"
        except Exception as exc:
            return f"❌ 清洗失败：{exc}"

        try:
            self._write_analysis_df(cleaned_df, output_table)
            self._schema_cache = None
        except Exception as exc:
            return summary + f"\n\n⚠️ 结果表写入失败：{exc}"

        return (
            summary
            + f"\n\n✅ 清洗结果已保存为表 `{output_table}`，可直接用于后续分析和图表生成。"
        )
