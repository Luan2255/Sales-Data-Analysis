"""Clean raw CSVs, derive sales metrics, and load a local SQLite database."""

from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
DATABASE_PATH = PROCESSED_DIR / "retail_sales.db"
SCHEMA_PATH = ROOT / "sql" / "schema.sql"
TABLES = ("regions", "customers", "products", "sellers", "sales")


def clean_tables() -> dict[str, pd.DataFrame]:
    tables = {name: pd.read_csv(RAW_DIR / f"{name}.csv") for name in TABLES}
    primary_keys = {
        "regions": "region_id",
        "customers": "customer_id",
        "products": "product_id",
        "sellers": "seller_id",
        "sales": "sale_id",
    }
    for name, frame in tables.items():
        for column in frame.columns:
            if pd.api.types.is_string_dtype(frame[column].dtype):
                frame[column] = frame[column].str.strip()
        frame.drop_duplicates(subset=primary_keys[name], inplace=True)

    for name, key in (("customers", "signup_date"), ("sellers", "hire_date")):
        tables[name][key] = pd.to_datetime(tables[name][key], errors="coerce")
        tables[name].dropna(subset=[key], inplace=True)
        tables[name][key] = tables[name][key].dt.strftime("%Y-%m-%d")

    sales = tables["sales"]
    sales["sale_date"] = pd.to_datetime(sales["sale_date"], errors="coerce")
    sales.dropna(subset=["sale_date"], inplace=True)
    sales = sales.loc[
        sales["quantity"].gt(0)
        & sales["unit_price"].gt(0)
        & sales["discount_pct"].between(0, 1)
    ].copy()

    dimensions = {
        "customer_id": set(tables["customers"]["customer_id"]),
        "product_id": set(tables["products"]["product_id"]),
        "seller_id": set(tables["sellers"]["seller_id"]),
        "region_id": set(tables["regions"]["region_id"]),
    }
    valid_rows = pd.Series(True, index=sales.index)
    for key, known_ids in dimensions.items():
        valid_rows &= sales[key].isin(known_ids)
    sales = sales.loc[valid_rows].merge(
        tables["products"][['product_id', 'unit_cost']],
        on="product_id",
        how="left",
        validate="many_to_one",
    )
    sales["gross_revenue"] = sales["quantity"] * sales["unit_price"]
    sales["discount_amount"] = sales["gross_revenue"] * sales["discount_pct"]
    sales["net_revenue"] = sales["gross_revenue"] - sales["discount_amount"]
    sales["estimated_cost"] = sales["quantity"] * sales["unit_cost"]
    sales["estimated_margin"] = sales["net_revenue"] - sales["estimated_cost"]
    sales["margin_pct"] = np.where(
        sales["net_revenue"].gt(0),
        sales["estimated_margin"] / sales["net_revenue"],
        np.nan,
    )
    sales["sale_date"] = sales["sale_date"].dt.strftime("%Y-%m-%d")
    tables["sales"] = sales.round(
        {"gross_revenue": 2, "discount_amount": 2, "net_revenue": 2,
         "estimated_cost": 2, "estimated_margin": 2, "margin_pct": 4}
    )
    return tables


def load_sqlite(tables: dict[str, pd.DataFrame]) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        connection.execute("DELETE FROM sales")
        connection.execute("DELETE FROM sellers")
        connection.execute("DELETE FROM products")
        connection.execute("DELETE FROM customers")
        connection.execute("DELETE FROM regions")
        for name in TABLES:
            tables[name].to_sql(name, connection, if_exists="append", index=False)


def main() -> None:
    tables = clean_tables()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.to_csv(PROCESSED_DIR / f"{name}.csv", index=False, encoding="utf-8")
        print(f"{name}: {len(frame):,} registros limpos")
    load_sqlite(tables)
    print(f"SQLite: {DATABASE_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
