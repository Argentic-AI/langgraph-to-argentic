"""AFTER: the same agent on Argentic. Same tools, same prompt, same task, same model.

    python after.py             # the first 4 tickets
    python after.py 8           # all 8; more repeats the same cases

Needs ARGENTIC_API_KEY (https://getargentic.com/platform) and MODEL_KEY.
"""
import os
import sys
import time

from argentic_ai import Argentic, run, summarize_replay
from argentic_ai.langchain import from_langchain_tools  # converts your tools, nothing else

from curve import show
from tools import MODEL, SYSTEM, TASK, Desk, make_tools


class Metered(Argentic):
    """The client, plus the prompt size of each wake, per model call."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.prompt_tokens: list[int] = []

    def wake(self, *args, **kw):
        resp = super().wake(*args, **kw)
        usage = resp.raw.get("usage") or {}
        if usage.get("prompt_tokens") and resp.turns:
            # a wake can take a few model calls: report the average prompt size per call
            self.prompt_tokens.append(round(usage["prompt_tokens"] / resp.turns))
        return resp


def main(tickets: int) -> None:
    client = Metered(log=lambda s: None)
    if not client.api_key or not client.model_key:
        sys.exit("Set ARGENTIC_API_KEY and MODEL_KEY first (see README.md).")
    desk = Desk(tickets)
    agent, run_id = f"support-{int(time.time())}", f"queue-{int(time.time())}"  # a new agent each run

    result = run(
        client, agent=agent, run_id=run_id, task=TASK, system=SYSTEM,
        tools=from_langchain_tools(make_tools(desk)),   # your tools, unchanged
        model={"provider": "nvidia", "id": MODEL, "prices": {"in": 0, "out": 0}}, max_steps=500, log=lambda s: None,
    )

    print("reply:", result.reply)
    print(desk.outcome())
    show("after (Argentic)", client.prompt_tokens, per="wake, averaged over its model calls")
    if result.wakes:
        print("\nreplay:", summarize_replay(client.replay(agent, result.wakes[0])))
        dash = os.environ.get("ARGENTIC_DASHBOARD_URL", "https://getargentic.com").rstrip("/")
        print(f"every prompt, rebuilt from the record: {dash}/platform/runs/{agent}/{result.wakes[0]}/")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 4)
