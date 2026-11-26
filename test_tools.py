"""Offline checks, no keys: python -m unittest -v"""
import unittest

from argentic_ai.langchain import from_langchain_tools

from tools import Desk, make_tools


class Tools(unittest.TestCase):
    def setUp(self):
        self.desk = Desk(3)
        self.tools = {t.name: t for t in make_tools(self.desk)}

    def test_queue_walks_to_empty(self):
        first = self.tools["next_ticket"].invoke({})
        self.assertEqual(first["ticket"], "T-101")
        self.tools["close_ticket"].invoke({"ticket_id": "T-101", "note": "done"})
        self.assertEqual(self.tools["next_ticket"].invoke({})["ticket"], "T-102")
        for t in ("T-102", "T-103"):
            self.tools["close_ticket"].invoke({"ticket_id": t, "note": "done"})
        self.assertEqual(self.tools["next_ticket"].invoke({}), {"empty": True})

    def test_refund_rules(self):
        self.assertIn("refunded", self.tools["refund_order"].invoke({"order_id": "5001", "amount_usd": 42}))
        self.assertIn("already refunded", self.tools["refund_order"].invoke({"order_id": "5001", "amount_usd": 42}))
        self.assertIn("over $100", self.tools["refund_order"].invoke({"order_id": "5004", "amount_usd": 120}))
        self.assertEqual(self.desk.refunds, {"5001": 42})

    def test_argentic_accepts_the_same_tools(self):
        converted = from_langchain_tools(make_tools(self.desk))
        self.assertEqual([t.name for t in converted],
                         ["next_ticket", "lookup_order", "refund_order", "send_email", "close_ticket"])
        out = converted[2].execute({"order_id": "5002", "amount_usd": 18}, type("Ctx", (), {"idempotency_key": "a:1"})())
        self.assertIn("refunded $18.00", out)


if __name__ == "__main__":
    unittest.main()
