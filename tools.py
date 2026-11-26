"""The part you keep: five tools, the system prompt and the task.

before.py and after.py both import this file and neither changes it.
The tools run in your process and touch your systems. Here they touch a small
in-memory desk, so the demo needs no database and no mail server.
"""
import os
import sys

from langchain_core.tools import tool

# You name the model in the environment. Nothing here picks one. See README.md.
MODEL_VARS = ("ARGENTIC_MODEL_ID", "ARGENTIC_MODEL_BASE_URL", "ARGENTIC_PRICE_IN", "ARGENTIC_PRICE_OUT", "MODEL_KEY")


def require_model_env() -> None:
    """Stop with a clear message if the model is not named. There is no default model."""
    missing = [v for v in MODEL_VARS if not os.environ.get(v)]
    if missing:
        sys.exit("Name your model first. Not set: " + ", ".join(missing) + ". See README.md.")

SYSTEM = (
    "You are the support agent for Acme. Work one ticket at a time: look the order up, "
    "refund it only if it arrived broken or never arrived (and only up to $100), "
    "email the customer, then close the ticket. "
    "Tool calls are requests: the result of each arrives in the next message. "
    "Call one tool per turn and wait for its result before you decide the next step."
)
TASK = (
    "Work the support queue until next_ticket says it is empty. When it is, reply with "
    "one line: how many tickets you closed and the total refunded."
)

# (ticket, order, customer email, order total, what the customer wrote)
QUEUE = [
    ("T-101", "5001", "ana@example.com", 42.00, "The screen arrived cracked."),
    ("T-102", "5002", "ben@example.com", 18.00, "Tracking hasn't moved in three weeks. It never arrived."),
    ("T-103", "5003", "cho@example.com", 65.00, "I ordered blue and got green. Can I swap it?"),
    ("T-104", "5004", "dev@example.com", 120.00, "The package never arrived."),
    ("T-105", "5005", "eli@example.com", 29.00, "Love it. How do I wash it?"),
    ("T-106", "5006", "fay@example.com", 74.00, "It arrived smashed into pieces."),
    ("T-107", "5007", "gus@example.com", 15.00, "The box was dented but the item is fine."),
    ("T-108", "5008", "hal@example.com", 52.00, "The handle snapped off on day one. It's broken."),
]


class Desk:
    """Stand-in for your helpdesk, orders database, payment provider and mail server."""

    def __init__(self, tickets: int = len(QUEUE)):
        # more than 8 tickets: the same eight cases again under new ticket and order numbers
        self.queue = [(f"T-{101 + i}", str(5001 + i), email, total, text)
                      for i, (_, _, email, total, text) in enumerate(QUEUE[i % len(QUEUE)] for i in range(tickets))]
        self.closed: list[str] = []
        self.refunds: dict[str, float] = {}
        self.emails: list[tuple[str, str]] = []

    def outcome(self) -> str:
        return (f"what your tools did: {len(self.closed)} of {len(self.queue)} tickets closed, "
                f"{len(self.refunds)} refunds totalling ${sum(self.refunds.values()):.2f}, "
                f"{len(self.emails)} emails sent")


def make_tools(desk: Desk):
    orders = {o: {"customer": email, "total": total} for _, o, email, total, _ in desk.queue}

    @tool
    def next_ticket() -> dict:
        """Get the next open ticket from the queue, or say the queue is empty."""
        for t, order, email, _, text in desk.queue:
            if t not in desk.closed:
                return {"ticket": t, "order_id": order, "customer": email, "message": text}
        return {"empty": True}

    @tool
    def lookup_order(order_id: str) -> dict:
        """Look up an order: customer email and total in dollars."""
        return orders.get(order_id, {"error": "no such order"})

    @tool
    def refund_order(order_id: str, amount_usd: float) -> str:
        """Refund an order. $100 at most per order."""
        if amount_usd > 100:
            return "refused: over $100, a person has to approve this"
        if order_id in desk.refunds:
            return "refused: this order was already refunded"
        desk.refunds[order_id] = amount_usd
        return f"refunded ${amount_usd:.2f} on order {order_id}"

    @tool
    def send_email(to: str, subject: str, body: str) -> str:
        """Email a customer."""
        desk.emails.append((to, subject))
        return f"email sent to {to}"

    @tool
    def close_ticket(ticket_id: str, note: str) -> str:
        """Close a support ticket."""
        if ticket_id not in desk.closed:
            desk.closed.append(ticket_id)
        return f"ticket {ticket_id} closed"

    return [next_ticket, lookup_order, refund_order, send_email, close_ticket]
