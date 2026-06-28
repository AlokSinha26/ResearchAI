# Autonomous Research Agent

A multi-step autonomous agent that dynamically selects tools — web search, PDF reading, and memory recall — to research, summarize, and synthesize answers to natural-language questions. Built with LangGraph for agent orchestration and FastAPI for a streaming API layer.

## What it does

Given a question, the agent:
1. **Decides** which tool(s) it needs (web search, PDF extraction, or memory lookup) — no hardcoded routing, the LLM chooses based on the query
2. **Executes** those tools, looping back to reasoning until it has enough information
3. **Synthesizes** everything it gathered into a single coherent answer
4. **Returns** the result as schema-validated structured data (via Pydantic), not a freeform blob of text

The whole process streams live over HTTP — a client sees each step (tool selection, tool results, final synthesis) as it happens, rather than waiting on one long blocking call.

## Architecture

```
User query
    │
    ▼
┌─────────────┐
│  LangGraph  │◄────┐
│   Agent     │     │  (loops until no more tools needed)
└──────┬──────┘     │
       │            │
       ▼            │
┌─────────────┐     │
│ Tool Router │─────┘
│ web_search  │
│ read_pdf    │
│ query_memory│
└─────────────┘
       │
       ▼
┌──────────────────┐
│ Structured Output │  → Pydantic-validated ResearchOutput
│   (finalize step) │     (sources, synthesis, confidence)
└──────────────────┘
       │
       ▼
FastAPI streaming response (Server-Sent Events)
```

**Design choice:** the agentic tool-selection loop and the structured-output step are kept separate. The agent runs freely first (exploratory, multiple tool calls, non-deterministic reasoning), then a single finalize call converts the gathered context into a validated schema. Trying to force schema compliance *during* the tool-calling loop is less reliable than separating "explore" from "report."

## Tech stack

- **Python** — core implementation
- **LangGraph** — stateful agent graph, conditional routing between reasoning and tool execution
- **LangChain** — tool abstraction layer (provider-agnostic: the LLM backend is swappable with a one-line change, currently configured for Google's Gemini API, originally built against Anthropic's Claude API)
- **FastAPI** — async streaming endpoint using Server-Sent Events
- **Pydantic** — structured, validated output schema (`ResearchOutput`, `SourceSummary`)
- **Tools**: `ddgs` (web search), `pypdf` + `httpx` (PDF fetching/extraction), in-memory key-value store (research memory)

## Setup

```bash
# Clone and enter the project
git clone <your-repo-url>
cd research-agent

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\Activate.ps1      # Windows PowerShell
# source venv/bin/activate      # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
GOOGLE_API_KEY=your_key_here
```

Get a free key at [ai.google.dev](https://ai.google.dev) (Google AI Studio).

## Running it

Start the API server:
```bash
uvicorn app.main:app
```

Send a request:
```bash
curl -N -X POST http://127.0.0.1:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "What is LangGraph and how does it differ from a basic LangChain agent?"}'
```

You'll see streamed JSON events as the agent works, followed by a final structured result:
```json
{"type": "step", "role": "HumanMessage", "content": "..."}
{"type": "tool_call", "tools": ["web_search"]}
{"type": "tool_result", "content": "..."}
{"type": "step", "role": "AIMessage", "content": "..."}
{"type": "final", "content": {
  "query": "...",
  "sources_used": [...],
  "synthesis": "...",
  "confidence": "high"
}}
```

## Performance

Benchmarked across 5 research questions spanning AI/ML topics (model comparisons, framework explanations, current events), measuring wall-clock time from request to final structured answer.

| Metric | Result |
|---|---|
| Average agent response time | **21.0 seconds** |
| Estimated average manual research time | **~4 minutes** (240s) |
| Estimated time reduction | **~91%** |

Raw timing data: see [`agent_benchmark_results.csv`](./agent_benchmark_results.csv).

**Methodology note:** agent-side timing is directly measured (`benchmark_agent.py` times real requests against the live API). The manual baseline is an estimate of typical multi-source research time for comparable questions, not a stopwatched measurement — included for honest context rather than overstated precision.

## Project structure

```
app/
├── main.py        # FastAPI app, streaming /research endpoint
├── agent.py       # LangGraph graph definition, tool-selection logic
├── tools.py        # web_search, read_pdf, query_memory tool implementations
├── schemas.py     # Pydantic output schema (ResearchOutput, SourceSummary)
└── memories.py    # Simple in-memory key-value store for research notes
benchmark_agent.py # Automated timing script against the live endpoint
requirements.txt
```

## Known limitations

- Memory is in-process and non-persistent (resets on server restart) — a production version would use a real vector store or database
- Web search relies on snippet-based results, which can occasionally surface outdated or low-quality sources; the agent doesn't currently verify recency or cross-check conflicting figures beyond basic synthesis
- No retry/backoff logic for LLM provider rate limits yet

## Built with

Developed iteratively in Cursor, using AI-assisted code generation and debugging throughout — from initial scaffolding through diagnosing environment, dependency, and API-quota issues during testing.
