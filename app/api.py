import json
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from .llm import generate_response, DEFAULT_MODEL
from .sentiment import analyse_sentiment, log_sentiment
from .memory import load_memory, save_memory
from .memory import (
    summarise_memory, 
    load_memory, 
    save_memory, 
    chunk_memory, 
    summarise_chunk, 
    save_summary, 
    load_summaries, 
    generate_reflection)
from .persona import (
    get_persona_prompt,
    personas,
    CURRENT_PERSONA,
    save_current_persona,
)

import requests
import time
import os

app = FastAPI()

MEMORY_PATH = "data/memory_store.json"
memory = load_memory(MEMORY_PATH)

class ChatRequest(BaseModel):
    message: str
    model: str | None = None  # Optional override

@app.post("/chat")
def chat(req: ChatRequest):
    user_message = req.message.strip()
    model = req.model or DEFAULT_MODEL

    # Check for memory introspection
    if "what do you remember" in user_message.lower():
        # Dynamic summarisation using the model
        chunks = chunk_memory(memory, chunk_size=5)
        summaries = []

        for chunk in chunks:
            summary = summarise_chunk(chunk, generate_response)
            save_summary(summary)  # Optional: comment out if you don't want to store
            summaries.append(f"- {summary.strip()}")

        ai_reply = "Here's what I recall from our recent conversation:\n\n" + "\n".join(summaries)
        
        # Optionally log this exchange to memory
        memory.append({"user": user_message, "ai": ai_reply})
        save_memory(MEMORY_PATH, memory)

        return {"response": ai_reply}
    elif user_message.lower() in ["bye", "exit", "/bye", "/exit"]:
        ai_reply = generate_reflection()
        memory.append({"user": user_message, "ai": ai_reply})
        save_memory(MEMORY_PATH, memory)
        return {"response": ai_reply}

    # Normal chat flow for sentiment analysis
    sentiment = analyse_sentiment(user_message)
    log_sentiment(sentiment)
    
    # Normal chat flow for response generation
    persona = get_persona_prompt(CURRENT_PERSONA)

    chat_history = "\n".join([
        f"User: {m['user']}\nAI: {m['ai']}"
        for m in summarise_memory(memory)
    ])

    full_prompt = (
        f"{persona}\n"
        f"(Sentiment: {sentiment})\n"
        f"{chat_history}\n"
        f"User: {user_message}\nAI:"
    )

    ai_reply = generate_response(full_prompt, model=model)

    # Save to memory
    memory.append({"user": user_message, "ai": ai_reply})
    save_memory(MEMORY_PATH, memory)

    return {"response": ai_reply}

@app.get("/status")
def status():
    try:
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": DEFAULT_MODEL,
            "prompt": "ping",
            "stream": False
        }, timeout=3)

        model_status = "ok" if response.ok else "model_error"
    except Exception:
        model_status = "ollama_unreachable"

    return JSONResponse({
        "model": DEFAULT_MODEL,
        "status": model_status,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })
    
@app.get("/memory")
def get_memory():
    # Return recent memory (trimmed to last 5 exchanges)
    summary = summarise_memory(memory)
    return {"memory": summary}

@app.delete("/memory")
def clear_memory():
    memory.clear()
    save_memory(MEMORY_PATH, memory)
    return {"message": "Memory cleared."}

@app.get("/summarise")
def summarise_conversation(model: str | None = None):
    model = model or DEFAULT_MODEL

    # Get memory (last few entries)
    trimmed = summarise_memory(memory)

    # Build raw chat history
    history_text = "\n".join([
        f"User: {m['user']}\nAI: {m['ai']}"
        for m in trimmed
    ])

    # Use the model to summarise
    prompt = (
        "Summarise the following conversation between an AI companion and a user. "
        "Keep it short, kind, and reflective.\n\n"
        f"{history_text}\n\n"
        "Summary:"
    )

    summary = generate_response(prompt, model=model)

    return {
        "summary": summary
    }
    
@app.post("/summarise/memory")
def summarise_full_memory():
    chunks = chunk_memory(memory, chunk_size=5)
    results = []

    for chunk in chunks:
        summary = summarise_chunk(chunk, generate_response)
        save_summary(summary)
        results.append(summary)

    return {"summaries": results}

@app.get("/summary")
def get_summary_log():
    summaries = load_summaries("data/summary_log.json")
    return {"summaries": summaries}

@app.delete("/summary")
def clear_summary_log():
    path = "data/summary_log.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)
    return {"message": "Summary log emptied."}

@app.get("/sentiment/trend")
def get_sentiment_trend():
    path = "data/sentiment_log.json"
    if not os.path.exists(path):
        return {"trend": "No sentiment data yet."}
    with open(path, "r", encoding="utf-8") as f:
        sentiments = [entry["sentiment"] for entry in json.load(f)]
    total = len(sentiments)
    counts = {s: sentiments.count(s) for s in set(sentiments)}
    return {
        "total_messages": total,
        "distribution": counts
    }
    
@app.delete("/sentiment")
def clear_sentiment_log():
    path = "data/sentiment_log.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)
    return {"message": "Sentiment log emptied."}
    
@app.get("/reflect")
def reflect_on_user():
    # Load memory summaries
    summaries = load_summaries("data/summary_log.json")
    summary_text = "\n".join([f"- {s['summary']}" for s in summaries[-3:]])  # Last 3 summaries
    
    # Load sentiment trend
    path = "data/sentiment_log.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            sentiments = [entry["sentiment"] for entry in json.load(f)]
    else:
        sentiments = []

    sentiment_summary = "No sentiment data available."
    if sentiments:
        total = len(sentiments)
        counts = {s: sentiments.count(s) for s in set(sentiments)}
        top = max(counts, key=counts.get)
        sentiment_summary = f"You've mostly expressed **{top}** emotions, based on {total} recent messages."

    # Create the reflective prompt for the model
    prompt = (
        f"As an AI companion, reflect on the user's recent activity and emotional tone.\n\n"
        f"Recent summaries:\n{summary_text}\n\n"
        f"Sentiment trend:\n{sentiment_summary}\n\n"
        f"Reflect briefly, in 2-3 sentences, offering encouragement or support."
    )

    reflection = generate_response(prompt)
    return {
        "summary_insight": summary_text,
        "sentiment_insight": sentiment_summary,
        "reflection": reflection.strip()
    }
    
@app.get("/persona")
def get_current_persona():
    return {"current_persona": CURRENT_PERSONA}

@app.post("/persona/{persona_name}")
def set_persona(persona_name: str):
    global CURRENT_PERSONA
    if persona_name in personas:
        CURRENT_PERSONA = persona_name
        return {"message": f"Persona switched to '{persona_name}'."}
    return {"error": "Persona not recognised.", "available": list(personas.keys())}

