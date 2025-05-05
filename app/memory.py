from .persona import get_persona_prompt
from .llm import generate_response

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

def chunk_memory(memory, chunk_size=5):
    """Split full memory into fixed-size chunks."""
    return [memory[i:i + chunk_size] for i in range(0, len(memory), chunk_size)]

def summarise_chunk(chunk, generate_fn):
    """Summarise a memory chunk using the LLM in short bullet points."""
    text = "\n".join([f"User: {m['user']}\nAI: {m['ai']}" for m in chunk])
    prompt = (
        f"{get_persona_prompt()}\n\n"
        "Summarise the following conversation in exactly 2 short bullet points. "
        "Each point must be no more than 20 words. Focus only on the user's actions, questions, or emotions.\n\n"
        f"{text}\n\n"
        "Summary:\n-"
    )
    return generate_fn(prompt)

def save_summary(summary, path="data/summary_log.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    summaries = []

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            summaries = json.load(f)

    summaries.append({"summary": summary})
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2)
        
def load_summaries(path="data/summary_log.json"):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
def generate_reflection():
    summaries = load_summaries("data/summary_log.json")
    summary_text = "\n".join([f"- {s['summary']}" for s in summaries[-3:]])

    path = "data/sentiment_log.json"
    sentiments = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            sentiments = [entry["sentiment"] for entry in json.load(f)]

    sentiment_summary = "No sentiment data available."
    if sentiments:
        total = len(sentiments)
        counts = {s: sentiments.count(s) for s in set(sentiments)}
        top = max(counts, key=counts.get)
        sentiment_summary = f"You’ve mostly expressed **{top}** emotions, based on {total} recent messages."

    prompt = (
        f"{get_persona_prompt()}\n\n"
        f"As an AI companion, reflect on the user's recent activity and emotional tone.\n\n"
        f"Recent summaries:\n{summary_text}\n\n"
        f"Sentiment trend:\n{sentiment_summary}\n\n"
        f"Reflect briefly, in 2–3 sentences, offering encouragement or support."
    )

    return generate_response(prompt)

    
    

