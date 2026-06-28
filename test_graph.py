# test_graph.py
from dotenv import load_dotenv
load_dotenv()

from app.agent import run_research

result = run_research("What is the current weather in Varanasi, India right now?")

print(result.model_dump_json(indent=2))