"""Tests for QuickBooks tax coding review pipeline."""

import unittest
from oa_client import OAClient
import coding_check
import qbo_client


class QuickBooksTaxDemoTests(unittest.TestCase):
    def setUp(self):
        self.oa = OAClient(token=None)  # Mock mode
        self.plan = self.oa.start("Review bookkeeping tax coding", "US")
        slug = (self.plan.get("skills_to_load") or [None])[0]
        self.skill = self.oa.get_skill(slug)

    def test_mock_oa_client_start_and_get_skill(self):
        self.assertEqual(self.plan["jurisdiction"], "US")
        self.assertEqual(self.plan["skills_to_load"][0], "us-bookkeeping-coding")
        self.assertEqual(self.skill["tier"], 1)
        self.assertIn("Amir Pelinkovic", self.skill["verifier"])

    def test_coding_check_capital_asset(self):
        tx = {
            "id": "tx-1",
            "vendor": "Dell",
            "amount": 12000.0,
            "account": "Office Supplies",
            "description": "Server hardware",
        }
        res = coding_check.check(tx, self.skill)
        self.assertEqual(res["status"], "warn")
        self.assertIn("Capital asset expensed", res["headline"])

    def test_coding_check_meals_50_percent(self):
        tx = {
            "id": "tx-2",
            "vendor": "Joe's Grill",
            "amount": 200.0,
            "account": "Meals - 100%",
            "description": "Client dinner",
        }
        res = coding_check.check(tx, self.skill)
        self.assertEqual(res["status"], "warn")
        self.assertIn("50% deductible", res["headline"])

    def test_coding_check_personal_expense(self):
        tx = {
            "id": "tx-3",
            "vendor": "Amazon",
            "amount": 800.0,
            "account": "Office Expenses",
            "description": "Owner personal headphones",
        }
        res = coding_check.check(tx, self.skill)
        self.assertEqual(res["status"], "warn")
        self.assertIn("Personal expense", res["headline"])

    def test_coding_check_safe_harbor_ok(self):
        tx = {
            "id": "tx-4",
            "vendor": "Apple",
            "amount": 1500.0,
            "account": "Office Supplies",
            "description": "MacBook Air laptop",
        }
        res = coding_check.check(tx, self.skill)
        self.assertEqual(res["status"], "ok")
        self.assertIn("safe harbor", res["headline"])

    def test_sample_transactions_extraction(self):
        txns = qbo_client.extract("samples/transactions.json")
        self.assertEqual(len(txns), 5)
        norm = qbo_client.normalize(txns[0])
        self.assertEqual(norm["vendor"], "Dell")
        self.assertEqual(norm["amount"], 12000.0)


if __name__ == "__main__":
    unittest.main()
