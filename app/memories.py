# app/memories.py
_store: dict[str, str] = {}

def save_memory(topic: str, content: str):
    _store[topic] = content

def search_memory(topic: str) -> str:
    matches = [v for k, v in _store.items() if topic.lower() in k.lower()]
    return "\n".join(matches) if matches else "No prior notes found."