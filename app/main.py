# app/main.py
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from app.agent import app_graph, structured_llm

app = FastAPI()


class ResearchRequest(BaseModel):
    query: str


def extract_text(content):
    """Gemini sometimes returns content as a list of blocks instead of a plain string."""
    if isinstance(content, list):
        return "".join(block.get("text", "") for block in content if isinstance(block, dict))
    return content


@app.post("/research")
async def research(payload: ResearchRequest):
    query = payload.query
    initial_state = {"messages": [("user", query)]}

    async def event_stream():
        final_state = None

        # Stream each step of the agent's reasoning as it happens
        async for event in app_graph.astream(initial_state, stream_mode="values"):
            final_state = event
            last_msg = event["messages"][-1]
            role = type(last_msg).__name__

            if role == "AIMessage" and getattr(last_msg, "tool_calls", None):
                step_data = {
                    "type": "tool_call",
                    "tools": [tc["name"] for tc in last_msg.tool_calls]
                }
            elif role == "ToolMessage":
                step_data = {
                    "type": "tool_result",
                    "content": extract_text(last_msg.content)[:300]
                }
            else:
                step_data = {
                    "type": "step",
                    "role": role,
                    "content": extract_text(last_msg.content)
                }

            yield f"data: {json.dumps(step_data)}\n\n"

        # Once the agent loop is done, run the structured finalize step
        finalize_prompt = (
            "Based on the conversation above, produce a ResearchOutput summary. "
            "List every distinct source you used with a short summary, "
            "then give your overall synthesis and confidence level."
        )
        structured_result = structured_llm.invoke(
            final_state["messages"] + [("user", finalize_prompt)]
        )

        yield f"data: {json.dumps({'type': 'final', 'content': structured_result.model_dump()})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/")
async def root():
    return {"status": "Research agent is running"}