import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/bizintel.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def load_csv_to_db(filepath: str, table_name: str = "sales") -> dict:
    """
    Read a CSV file, clean column names, and load into SQLite.
    Returns a summary of what was loaded.
    """
    df = pd.read_csv(filepath, encoding="latin-1")

    # Normalize column names: lowercase, replace spaces with underscores
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
        .str.replace("/", "_")
    )

    # Parse date columns automatically
    for col in df.columns:
        if "date" in col:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Drop fully empty rows
    df.dropna(how="all", inplace=True)

    # Load into SQLite (replace table if exists)
    df.to_sql(table_name, con=engine, if_exists="replace", index=False)

    return {
        "table": table_name,
        "rows": len(df),
        "columns": list(df.columns),
        "message": f"Successfully loaded {len(df)} rows into table '{table_name}'",
    }


def get_engine():
    return engine


def run_query(sql: str) -> pd.DataFrame:
    """Run a raw SQL query and return a DataFrame."""
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    return df


def get_table_info() -> str:
    """
    Return schema info for the LangChain SQL agent to understand the DB.
    """
    with engine.connect() as conn:
        # Get all table names
        tables = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        ).fetchall()

        info = []
        for (table_name,) in tables:
            cols = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
            col_names = [c[1] for c in cols]
            sample = conn.execute(
                text(f"SELECT * FROM {table_name} LIMIT 3")
            ).fetchall()
            info.append(
                f"Table: {table_name}\nColumns: {', '.join(col_names)}\nSample rows: {sample}\n"
            )

    return "\n".join(info)