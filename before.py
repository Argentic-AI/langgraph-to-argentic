"""BEFORE: the support agent as a LangChain / LangGraph loop.

    python before.py            # the first 4 tickets
    python before.py 8          # all 8; more repeats the same cases

Needs MODEL_KEY: a free NVIDIA key from build.nvidia.com.
"""
import os
import sys

from langchain.agents import create_agent  # LangChain's agent loop, built on LangGraph
from langchain_openai import ChatOpenAI

from curve import show
from tools import MODEL, MODEL_BASE_URL, SYSTEM, TASK, Desk, make_tools


def main(tickets: int) -> None:
    desk = Desk(tickets)
    llm = ChatOpenAI(model=MODEL, temperature=0, api_key=os.environ["MODEL_KEY"],
                     base_url=MODEL_BASE_URL)
    agent = create_agent(llm, make_tools(desk), system_prompt=SYSTEM)
    # the default recursion limit (25) stops a long run; raise it
    out = agent.invoke({"messages": [("user", TASK)]}, {"recursion_limit": 500})

    print("reply:", out["messages"][-1].content)
    print(desk.outcome())
    # the provider's own count of what each model call was sent
    show("before (LangGraph loop)", [m.usage_metadata["input_tokens"] for m in out["messages"]
                                    if m.type == "ai" and m.usage_metadata])


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 4)
