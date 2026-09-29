import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.clean_data import clean_tables
from src.generate_data import generate_dataset


class RetailPipelineTests(unittest.TestCase):
    def test_generation_is_reproducible_and_has_relational_keys(self):
        first = generate_dataset()
        second = generate_dataset()
        self.assertEqual(first["sales"].shape, second["sales"].shape)
        pd.testing.assert_frame_equal(first["sales"], second["sales"])
        self.assertGreaterEqual(len(first["sales"]), 10_000)
        self.assertTrue(set(first["sales"]["customer_id"]).issubset(first["customers"]["customer_id"]))
        orders_per_customer = first["sales"].drop_duplicates(["customer_id", "order_id"]).groupby("customer_id").size()
        recurring_rate = orders_per_customer.ge(2).mean()
        self.assertTrue(0.2 <= recurring_rate <= 0.6)
        purchases = first["sales"].merge(
            first["customers"][["customer_id", "signup_date"]], on="customer_id"
        )
        self.assertTrue((purchases["sale_date"] >= purchases["signup_date"]).all())

    def test_cleaning_calculates_nonnegative_discount_and_margin_fields(self):
        tables = clean_tables()
        sales = tables["sales"]
        self.assertTrue(sales["net_revenue"].ge(0).all())
        self.assertTrue(sales["discount_amount"].ge(0).all())
        self.assertTrue(sales["estimated_margin"].notna().all())
        self.assertEqual(sales["sale_id"].nunique(), len(sales))


if __name__ == "__main__":
    unittest.main()
