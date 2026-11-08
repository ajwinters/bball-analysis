"""Read-only access to the bballagg Postgres database on honeydew.

Connects over the local Unix socket as the read-only role `bball_reader`
(peer auth mapped from the Linux user, no password). bballagg owns the data;
this repo only reads it. See scripts/setup_db_reader.sh for how the role was made.

Override with env vars if needed: BBALL_DB_NAME, BBALL_DB_USER, BBALL_DB_HOST.
"""

import os
from functools import cache

import pandas as pd
import sqlalchemy as sa

DB_NAME = os.environ.get("BBALL_DB_NAME", "bballagg")
DB_USER = os.environ.get("BBALL_DB_USER", "bball_reader")
DB_HOST = os.environ.get("BBALL_DB_HOST", "/var/run/postgresql")


@cache
def engine() -> sa.Engine:
    """SQLAlchemy engine. marimo SQL cells pick this up if you assign it to a variable."""
    url = sa.URL.create(
        "postgresql+psycopg2", username=DB_USER, database=DB_NAME, query={"host": DB_HOST}
    )
    return sa.create_engine(url, pool_pre_ping=True)


def query(sql: str, **params) -> pd.DataFrame:
    """Run SQL and return a DataFrame. Use %(name)s placeholders: query(sql, season="2024-25")."""
    with engine().connect() as con:
        res = con.exec_driver_sql(sql, params or None)  # psycopg2 style: %(name)s, literal %%
        return pd.DataFrame(res.fetchall(), columns=list(res.keys()))


def tables(pattern: str = "%") -> list[str]:
    """Table names in the public schema matching a LIKE pattern, e.g. tables('nba_boxscore%')."""
    df = query(
        "select table_name from information_schema.tables "
        "where table_schema = 'public' and table_name like %(p)s order by 1",
        p=pattern,
    )
    return df["table_name"].tolist()


def columns(table: str) -> pd.DataFrame:
    """Column names and types for one table."""
    return query(
        "select column_name, data_type from information_schema.columns "
        "where table_schema = 'public' and table_name = %(t)s order by ordinal_position",
        t=table,
    )
