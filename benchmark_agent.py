# benchmark_agent.py
import time
import requests
import json
import csv

QUESTIONS = [
    "What are the main differences between the latest Gemini and GPT model releases?",
    "What is LangGraph and how does it differ from a basic LangChain agent?",
    "What are the current best practices for prompt engineering with tool-calling LLMs?",
    "What is Anthropic's Model Context Protocol (MCP) and why does it matter?",
    "What are the biggest criticisms or limitations of current AI coding assistants?",
    "What's the latest news on AI regulation in the EU or US this year?",
]

URL = "http://127.0.0.1:8000/research"
results = []

for q in QUESTIONS:
    print(f"\nRunning: {q}")
    start = time.time()

    try:
        response = requests.post(URL, json={"query": q}, stream=True, timeout=120)
        final_answer = None

        for line in response.iter_lines():
            if line and line.startswith(b"data: "):
                chunk = json.loads(line[6:])
                if chunk["type"] == "final":
                    final_answer = chunk["content"]

        elapsed = time.time() - start
        print(f"  -> {elapsed:.1f} seconds")

        results.append({
            "question": q,
            "agent_seconds": round(elapsed, 1),
            "confidence": final_answer["confidence"] if final_answer else "N/A",
            "num_sources": len(final_answer["sources_used"]) if final_answer else 0
        })

    except Exception as e:
        elapsed = time.time() - start
        print(f"  -> FAILED after {elapsed:.1f} seconds: {e}")
        results.append({
            "question": q,
            "agent_seconds": "FAILED",
            "confidence": "N/A",
            "num_sources": 0
        })

    time.sleep(10)  # increased pause to respect free-tier limits

with open("agent_benchmark_results.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["question", "agent_seconds", "confidence", "num_sources"])
    writer.writeheader()
    writer.writerows(results)

print("\nDone. Results saved to agent_benchmark_results.csv")
for r in results:
    print(r)