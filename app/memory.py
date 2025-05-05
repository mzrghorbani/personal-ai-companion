import json
import os

def load_memory(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_memory(path, memory):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(memory, f, indent=2)

def summarise_memory(memory):
    # Skip summary-type entries to prevent memory echoing
    recent = [m for m in memory if m["user"] != "summary"]
    return recent[-5:]

