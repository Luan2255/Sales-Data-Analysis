"""Build a static portfolio preview from the processed SQLite database."""

from pathlib import Path
import sqlite3

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter


ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = ROOT / "data" / "processed" / "retail_sales.db"
OUTPUT_PATH = ROOT / "assets" / "powerbi_dashboard_preview.png"


PALETTE = {
    "ink": "#20312D",
    "green": "#176B5B",
    "coral": "#F07B55",
    "gold": "#E3B44A",
    "blue": "#386A8C",
    "muted": "#52615C",
    "paper": "#F7F8F5",
}


def main() -> None:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError("Execute src/clean_data.py antes de gerar a prévia.")
    with sqlite3.connect(DATABASE_PATH) as connection:
        kpis = pd.read_sql_query(
            "SELECT SUM(net_revenue) AS revenue, "
            "COUNT(DISTINCT order_id) AS orders, "
            "SUM(net_revenue) / COUNT(DISTINCT order_id) AS average_ticket, "
            "SUM(estimated_margin) / SUM(net_revenue) AS margin_pct FROM sales",
            connection,
        ).iloc[0]
        monthly = pd.read_sql_query(
            "SELECT substr(sale_date, 1, 7) AS month, SUM(net_revenue) AS revenue "
            "FROM sales GROUP BY month ORDER BY month",
            connection,
        )
        products = pd.read_sql_query(
            "SELECT p.product_name, SUM(s.net_revenue) AS revenue "
            "FROM sales s JOIN products p USING(product_id) "
            "GROUP BY p.product_id ORDER BY revenue DESC LIMIT 8",
            connection,
        )
        regions = pd.read_sql_query(
            "SELECT r.region_name, SUM(s.net_revenue) AS revenue "
            "FROM sales s JOIN regions r USING(region_id) "
            "GROUP BY r.region_id ORDER BY revenue DESC",
            connection,
        )
        sellers = pd.read_sql_query(
            "SELECT v.seller_name, SUM(s.net_revenue) AS revenue "
            "FROM sales s JOIN sellers v USING(seller_id) "
            "GROUP BY v.seller_id ORDER BY revenue DESC LIMIT 8",
            connection,
        )

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "text.color": PALETTE["ink"],
            "axes.labelcolor": PALETTE["muted"],
            "xtick.color": PALETTE["muted"],
            "ytick.color": PALETTE["muted"],
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    figure = plt.figure(figsize=(16, 10), facecolor=PALETTE["paper"])
    grid = figure.add_gridspec(3, 4, height_ratios=[0.65, 1.45, 1.45], hspace=0.58, wspace=0.6)
    figure.text(0.055, 0.95, "RETAIL  /  SALES PERFORMANCE", fontsize=11, weight="bold", color=PALETTE["green"])
    figure.text(0.055, 0.91, "Visão geral do negócio", fontsize=25, weight="bold", color=PALETTE["ink"])
    figure.text(0.945, 0.945, "2023 — 2025   •   DADOS SINTÉTICOS", fontsize=9, ha="right", color=PALETTE["muted"])

    cards = [
        ("FATURAMENTO", f"R$ {kpis.revenue / 1_000_000:.2f} mi", PALETTE["green"]),
        ("PEDIDOS", f"{int(kpis.orders):,}".replace(",", "."), PALETTE["blue"]),
        ("TICKET MÉDIO", f"R$ {kpis.average_ticket:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), PALETTE["coral"]),
        ("MARGEM ESTIMADA", f"{kpis.margin_pct:.1%}", PALETTE["gold"]),
    ]
    for index, (label, value, color) in enumerate(cards):
        axis = figure.add_subplot(grid[0, index])
        axis.set_facecolor("white")
        axis.set_xticks([])
        axis.set_yticks([])
        for spine in axis.spines.values():
            spine.set_visible(False)
        axis.text(0.08, 0.72, label, transform=axis.transAxes, fontsize=9, color=PALETTE["muted"], weight="bold")
        axis.text(0.08, 0.25, value, transform=axis.transAxes, fontsize=19, color=color, weight="bold")

    monthly_axis = figure.add_subplot(grid[1, :2])
    monthly_axis.plot(monthly.month, monthly.revenue, color=PALETTE["green"], linewidth=2.4)
    monthly_axis.fill_between(monthly.month, monthly.revenue, color=PALETTE["green"], alpha=0.08)
    monthly_axis.set_title("Faturamento líquido mensal", loc="left", weight="bold", pad=12)
    monthly_axis.set_ylabel("Receita (R$)")
    monthly_axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value / 1_000_000:.1f} mi"))
    monthly_axis.set_xticks(range(0, len(monthly), 6), monthly.month.iloc[::6], rotation=0)
    monthly_axis.grid(axis="y", alpha=0.2)
    monthly_axis.grid(axis="x", visible=False)

    product_axis = figure.add_subplot(grid[1, 2:])
    product_axis.barh(products.product_name.iloc[::-1], products.revenue.iloc[::-1], color=PALETTE["coral"])
    product_axis.set_title("Produtos líderes em faturamento", loc="left", weight="bold", pad=12)
    product_axis.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value / 1000:.0f} mil"))
    product_axis.grid(axis="x", alpha=0.2)
    product_axis.grid(axis="y", visible=False)

    region_axis = figure.add_subplot(grid[2, :2])
    region_axis.bar(regions.region_name, regions.revenue, color=[PALETTE["green"], PALETTE["blue"], PALETTE["coral"], PALETTE["gold"], "#8AA59B"])
    region_axis.set_title("Faturamento por região", loc="left", weight="bold", pad=12)
    region_axis.set_ylabel("Receita (R$)")
    region_axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value / 1_000_000:.1f} mi"))
    region_axis.tick_params(axis="x", rotation=15)
    region_axis.grid(axis="y", alpha=0.2)
    region_axis.grid(axis="x", visible=False)

    seller_axis = figure.add_subplot(grid[2, 2:])
    seller_axis.barh(sellers.seller_name.iloc[::-1], sellers.revenue.iloc[::-1], color=PALETTE["blue"])
    seller_axis.set_title("Vendedores líderes em faturamento", loc="left", weight="bold", pad=12)
    seller_axis.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value / 1000:.0f} mil"))
    seller_axis.grid(axis="x", alpha=0.2)
    seller_axis.grid(axis="y", visible=False)

    figure.text(0.055, 0.025, "Margem calculada com custos sintéticos. Prévia estática; medidas e filtros interativos no Power BI.", fontsize=9, color=PALETTE["muted"])
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight", facecolor=figure.get_facecolor())
    print(f"Prévia criada em {OUTPUT_PATH.relative_to(ROOT)}")
    plt.close(figure)


if __name__ == "__main__":
    main()
