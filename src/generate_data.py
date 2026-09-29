"""Generate a reproducible fictional retail dataset for the portfolio project."""

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
SEED = 42


def generate_dataset(seed: int = SEED) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)

    regions = pd.DataFrame(
        {
            "region_id": [f"R{i:02d}" for i in range(1, 6)],
            "region_name": ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"],
            "macro_region": ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"],
        }
    )
    region_ids = regions["region_id"].to_numpy()

    category_catalog = {
        "Eletrônicos": ("Fone", "Monitor", "Teclado", "Mouse", "Webcam", "Notebook"),
        "Casa": ("Luminária", "Organizador", "Cafeteira", "Ventilador", "Jogo de panelas"),
        "Escritório": ("Cadeira", "Mesa", "Caderno", "Caneta", "Impressora"),
        "Esportes": ("Garrafa", "Colchonete", "Mochila", "Bicicleta", "Halteres"),
        "Acessórios": ("Carteira", "Relógio", "Óculos", "Cinto", "Bolsa"),
    }
    product_rows = []
    for index in range(1, 61):
        category = list(category_catalog)[(index - 1) % len(category_catalog)]
        names = category_catalog[category]
        base_price = float(rng.choice([49.9, 89.9, 149.9, 249.9, 499.9, 899.9]))
        product_rows.append(
            {
                "product_id": f"P{index:03d}",
                "product_name": f"{names[(index - 1) // len(category_catalog) % len(names)]} {index:02d}",
                "category": category,
                "unit_price": base_price,
                "unit_cost": round(base_price * float(rng.uniform(0.48, 0.76)), 2),
            }
        )
    products = pd.DataFrame(product_rows)

    sellers = pd.DataFrame(
        {
            "seller_id": [f"V{i:03d}" for i in range(1, 25)],
            "seller_name": [f"Vendedor {i:02d}" for i in range(1, 25)],
            "region_id": rng.choice(region_ids, size=24),
            "hire_date": pd.to_datetime(
                rng.choice(pd.date_range("2019-01-01", "2023-12-31"), size=24)
            ).strftime("%Y-%m-%d"),
        }
    )

    customer_count = 700
    customers = pd.DataFrame(
        {
            "customer_id": [f"C{i:05d}" for i in range(1, customer_count + 1)],
            "customer_name": [f"Cliente {i:04d}" for i in range(1, customer_count + 1)],
            "region_id": rng.choice(region_ids, size=customer_count),
            "signup_date": pd.to_datetime(
                rng.choice(pd.date_range("2020-01-01", "2022-12-31"), size=customer_count)
            ).strftime("%Y-%m-%d"),
            "customer_segment": rng.choice(
                ["Consumer", "Corporate", "Small Business"],
                size=customer_count,
                p=[0.62, 0.23, 0.15],
            ),
        }
    )

    order_count = 7_000
    calendar = pd.date_range("2023-01-01", "2025-12-31", freq="D")
    month_weights = np.array(
        [0.85, 0.80, 0.90, 0.88, 0.92, 0.95, 0.90, 0.92, 0.98, 1.08, 1.45, 1.25]
    )
    date_weights = month_weights[calendar.month - 1].astype(float)
    date_weights /= date_weights.sum()
    order_dates = rng.choice(calendar.to_numpy(), size=order_count, p=date_weights)
    customer_ids = customers["customer_id"].to_numpy()
    one_time_customer_count = int(customer_count * 0.65)
    order_customers = np.concatenate(
        [
            customer_ids[:one_time_customer_count],
            rng.choice(
                customer_ids[one_time_customer_count:],
                size=order_count - one_time_customer_count,
            ),
        ]
    )
    rng.shuffle(order_customers)
    product_ids = products["product_id"].to_numpy()
    seller_ids = sellers["seller_id"].to_numpy()
    product_weights = np.linspace(1.8, 0.5, len(products))
    product_weights /= product_weights.sum()
    seller_weights = np.linspace(1.5, 0.7, len(sellers))
    seller_weights /= seller_weights.sum()

    sales_rows = []
    sale_id = 1
    for order_number in range(order_count):
        order_id = f"PED{order_number + 1:06d}"
        customer_id = str(order_customers[order_number])
        customer_region = customers.loc[
            customers["customer_id"].eq(customer_id), "region_id"
        ].iloc[0]
        seller_id = str(rng.choice(seller_ids, p=seller_weights))
        line_count = int(rng.integers(1, 4))
        chosen_products = rng.choice(
            product_ids, size=line_count, replace=False, p=product_weights
        )
        for product_id in chosen_products:
            product = products.loc[products["product_id"].eq(product_id)].iloc[0]
            quantity = int(rng.integers(1, 5))
            discount_pct = float(rng.choice([0, 0.05, 0.10, 0.15, 0.20], p=[0.42, 0.23, 0.20, 0.10, 0.05]))
            sales_rows.append(
                {
                    "sale_id": f"S{sale_id:07d}",
                    "order_id": order_id,
                    "sale_date": pd.Timestamp(order_dates[order_number]).strftime("%Y-%m-%d"),
                    "customer_id": customer_id,
                    "product_id": product_id,
                    "seller_id": seller_id,
                    "region_id": customer_region,
                    "quantity": quantity,
                    "unit_price": product["unit_price"],
                    "discount_pct": discount_pct,
                }
            )
            sale_id += 1

    sales = pd.DataFrame(sales_rows)
    return {
        "regions": regions,
        "customers": customers,
        "products": products,
        "sellers": sellers,
        "sales": sales,
    }


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    tables = generate_dataset()
    for table_name, frame in tables.items():
        frame.to_csv(RAW_DIR / f"{table_name}.csv", index=False, encoding="utf-8")
        print(f"{table_name}: {len(frame):,} registros")


if __name__ == "__main__":
    main()
