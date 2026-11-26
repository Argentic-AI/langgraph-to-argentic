# langgraph-to-argentic

Argentic is an engine that keeps AI agents right for hours while prompt size is bounded. This repo is one small support agent written twice: as a LangChain/LangGraph loop (`before.py`) and on Argentic (`after.py`). Both use the same five tools, the same system prompt, the same task and the same model.

You keep your `@tool` functions and your system prompt. You drop the loop. Argentic runs the loop and builds each prompt from its own record, so it replaces the whole loop, checkpointer included. If you like your graph, this repo is not for you. If your agent gets worse the longer it runs, and the fixes so far have been a bigger window, trimming or summarising, read on.

## Before: a LangGraph loop

`before.py` builds the agent with LangChain's `create_agent`, which is a LangGraph graph underneath, and the transcript grows with every tool call:

```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model=MODEL, base_url=MODEL_BASE_URL, api_key=os.environ["MODEL_KEY"], temperature=0)
agent = create_agent(llm, make_tools(desk), system_prompt=SYSTEM)
out = agent.invoke({"messages": [("user", TASK)]}, {"recursion_limit": 500})
```

The default recursion limit is 25, which stops a long run, so the script raises it.

## After: the same tools on Argentic

`after.py` hands the same tools and the same prompt to `run()`:

```python
from argentic_ai import Argentic, run
from argentic_ai.langchain import from_langchain_tools

result = run(
    Argentic(),                                   # reads ARGENTIC_API_KEY and MODEL_KEY
    agent="support-agent", run_id="queue-1",
    task=TASK, system=SYSTEM,
    tools=from_langchain_tools(make_tools(desk)),  # your tools, unchanged
    model={"provider": "nvidia", "id": MODEL, "prices": {"in": 0, "out": 0}},
    max_steps=500,                                # the default is 8 wakes
)
print(result.reply)
```

`from_langchain_tools` takes your LangChain tools as they are. `tools.py` is imported by both scripts and neither edits it.

## Run it

You need Python 3.10+, an Argentic key from https://getargentic.com/platform, and a free NVIDIA key from https://build.nvidia.com.

```bash
git clone https://github.com/Argentic-AI/langgraph-to-argentic && cd langgraph-to-argentic
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ARGENTIC_API_KEY=aek_...
export MODEL_KEY=nvapi-...
python before.py
python after.py
```

In fish:

```fish
python3 -m venv .venv; and source .venv/bin/activate.fish
pip install -r requirements.txt
set -x ARGENTIC_API_KEY aek_...
set -x MODEL_KEY nvapi-...
```

`requirements.txt` installs the Argentic client straight from a pinned commit of [Argentic-AI/argentic-plugins](https://github.com/Argentic-AI/argentic-plugins). Each script takes a ticket count: `python before.py 8` works all eight tickets, and a larger number repeats the same cases under new ticket numbers. With four tickets, expect a few minutes on the free model, depending on how busy it is.

Each script prints the reply, what your tools actually did (tickets closed, refunds, emails) and the prompt size of each model call. Run `python -m unittest -v` for the offline checks, which need no keys.

## What a short run shows

The two scripts do the same work and print the same kind of chart, so you can compare them on your own run. What the chart shows:

- Both prompts grow over a short run, and Argentic's starts larger.
- The engine holds its prompt under a ceiling and a plain loop has none. A run long enough to reach that ceiling is much longer than this demo, so this repo does not show it, and nothing here measures answer quality.
- For long runs, with the model, engine version and date next to each number, see the research posts at https://getargentic.com/research.

The prompt size for `before.py` is the provider's count for each call. For `after.py` it is the provider's count for each wake divided by the model calls in that wake, because the API reports them per wake.

## One difference to know about

With Argentic, a tool call is a request: your code runs the tool and the result goes to the model on the next wake. The system prompt says so in one sentence, and the model has to follow it. When we tried Argentic's free default (`nemotron-3.5-lightning-30b-a3b`) on 2026-11-26, it kept calling tools without waiting for results and guessed refund amounts. `nvidia/nemotron-3.5-super-vl-120b-a12b`, which this repo uses, waited. If your agent misbehaves in the same way, try a stronger model before blaming the port.

## See what the model was sent

`after.py` ends with a link to the run in your dashboard, and a line that re-checks the run against the record without calling the model. Open the link and press **Check** under **Proof of what ran** to compare every prompt with what the model received.

## When not to switch

- Short sessions that fit the window are simpler on a plain loop.
- Argentic runs the loop, so graph features such as branching nodes, a checkpointer and `interrupt()` do not carry over.
- Coding and filesystem agents are not what Argentic is for.
- Argentic is hosted only. The client libraries are MIT.

## Files

| File | What it is |
|---|---|
| `tools.py` | The five tools, the system prompt and the task. Imported by both. |
| `before.py` | The LangGraph loop. |
| `after.py` | The same agent on Argentic. |
| `curve.py` | Prints the prompt sizes. |
| `test_tools.py` | Offline checks. |

MIT licensed.
