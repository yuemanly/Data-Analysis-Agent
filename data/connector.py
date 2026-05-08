#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Data source connectors: Excel (via SQLite in-memory) and SQL databases."""
import sqlite3
import pandas as pd
from typing import Tuple, List, Optional

MAX_DISPLAY_ROWS = 200
MAX_CHART_ROWS = 5000


class DataSource:
    name: str = ""

    def get_schema(self) -> str:
        raise NotImplementedError

    def execute_query(self, sql: str) -> Tuple[pd.DataFrame, str]:
        """Returns (dataframe, error_string). error_string is empty on success."""
        raise NotImplementedError

    @staticmethod
    def format_result(df: pd.DataFrame) -> str:
        if df.empty:
            return "Query returned no results."
        total = len(df)
        preview = df.head(MAX_DISPLAY_ROWS)
        text = preview.to_string(index=False, max_cols=30)
        if total > MAX_DISPLAY_ROWS:
            text += f"\n\n... showing {MAX_DISPLAY_ROWS} of {total} rows"
        return text


class ExcelDataSource(DataSource):
    """Load one or more sheets from an Excel file into a shared SQLite in-memory DB."""

    def __init__(self, file_path: str, filename: str):
        self.name = filename
        self.file_path = file_path
        self._conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._tables: List[str] = []
        self._load(file_path)

    def _clean_col(self, col: str) -> str:
        for ch in (" ", ".", "(", ")", "/", "\\", "-", "—"):
            col = col.replace(ch, "_")
        return col.strip("_") or "col"

    def _load(self, path: str):
        xl = pd.ExcelFile(path)
        for sheet in xl.sheet_names:
            df = xl.parse(sheet)
            df.columns = [self._clean_col(str(c)) for c in df.columns]
            df = df.dropna(how="all")
            table = self._clean_col(sheet) or f"sheet{len(self._tables)+1}"
            df.to_sql(table, self._conn, if_exists="replace", index=False)
            self._tables.append(table)
        if not self._tables:
            raise ValueError("Excel 文件中未发现有效工作表。")

    def get_schema(self) -> str:
        cursor = self._conn.cursor()
        parts: List[str] = []
        for table in self._tables:
            cursor.execute(f'PRAGMA table_info("{table}")')
            cols = cursor.fetchall()
            cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
            rows = cursor.fetchone()[0]
            col_lines = [f"  {c[1]}  {c[2]}" for c in cols]
            parts.append(f"Table: {table}  ({rows} rows)\n" + "\n".join(col_lines))
        return "\n\n".join(parts)

    def execute_query(self, sql: str) -> Tuple[pd.DataFrame, str]:
        try:
            return pd.read_sql_query(sql, self._conn), ""
        except Exception as exc:
            return pd.DataFrame(), str(exc)


class CSVDataSource(DataSource):
    """Load a single CSV file into a SQLite in-memory DB."""

    def __init__(self, file_path: str, filename: str):
        self.name = filename
        self.file_path = file_path
        self._conn = sqlite3.connect(":memory:", check_same_thread=False)
        table = filename.rsplit(".", 1)[0].replace(" ", "_").replace("-", "_") or "data"
        self._table = table
        df = pd.read_csv(file_path, encoding="utf-8-sig")
        df.columns = [str(c).strip().replace(" ", "_") for c in df.columns]
        df = df.dropna(how="all")
        df.to_sql(table, self._conn, if_exists="replace", index=False)

    def get_schema(self) -> str:
        cursor = self._conn.cursor()
        cursor.execute(f'PRAGMA table_info("{self._table}")')
        cols = cursor.fetchall()
        cursor.execute(f'SELECT COUNT(*) FROM "{self._table}"')
        rows = cursor.fetchone()[0]
        col_lines = [f"  {c[1]}  {c[2]}" for c in cols]
        return f"Table: {self._table}  ({rows} rows)\n" + "\n".join(col_lines)

    def execute_query(self, sql: str) -> Tuple[pd.DataFrame, str]:
        try:
            return pd.read_sql_query(sql, self._conn), ""
        except Exception as exc:
            return pd.DataFrame(), str(exc)


class SQLDataSource(DataSource):
    """Connect to any SQLAlchemy-supported database."""

    def __init__(self, connection_string: str, display_name: str = ""):
        from sqlalchemy import create_engine, text, inspect as sa_inspect

        self._engine = create_engine(connection_string, pool_pre_ping=True)
        # Validate the connection immediately
        with self._engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        if display_name:
            self.name = display_name
        else:
            try:
                url = self._engine.url
                self.name = f"{url.host}/{url.database or ''}"
            except Exception:
                self.name = "SQL Database"

        self._inspect = sa_inspect(self._engine)

    def get_schema(self) -> str:
        parts: List[str] = []
        try:
            tables = self._inspect.get_table_names()[:50]
        except Exception:
            tables = []
        for table in tables:
            try:
                cols = self._inspect.get_columns(table)
                col_lines = [f"  {c['name']}  {c['type']}" for c in cols]
                parts.append(f"Table: {table}\n" + "\n".join(col_lines))
            except Exception:
                parts.append(f"Table: {table}  (schema unavailable)")
        return "\n\n".join(parts) if parts else "No tables found."

    def execute_query(self, sql: str) -> Tuple[pd.DataFrame, str]:
        from sqlalchemy import text

        try:
            with self._engine.connect() as conn:
                df = pd.read_sql(text(sql), conn)
            return df, ""
        except Exception as exc:
            return pd.DataFrame(), str(exc)
