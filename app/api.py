from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from .llm import generate_response, DEFAULT_MODEL
from .sentiment import analyse_sentiment, log_sentiment
from .memory_store import (
    load_memory, save_memory,
    summarise_memory, chunk_memory
)
from .vector_memory import (
    summarise_chunk, save_summary,
    get_relevant_memories, clear_vector_memory,
    generate_reflection, get_all_summaries, summarise_recent
)
from .persona import (
    get_persona_prompt,
    personas,
    CURRENT_PERSONA,
    save_current_persona,
)

import json
import requests
import time
import os
import uuid
from contextlib import asynccontextmanager

MEMORY_PATH = "data/memory_store.json"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load memory on startup
    global memory
    memory = load_memory(MEMORY_PATH)
    global memory_snapshot
    memory_snapshot = get_all_summaries()[-3:]

    yield

    # Clear memory on shutdown
    print("Clearing memory...")
    memory.clear()
    save_memory(MEMORY_PATH, memory)
    print("Memory cleared.")

app = FastAPI(lifespan=lifespan)

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
            id_summary = str(uuid.uuid4())
            summary = summarise_chunk(chunk, generate_response)
            save_summary(summary, id_summary)
            summaries.append(f"- {summary.strip()}")

        ai_reply = "Here's what I recall from our recent conversation:\\n\\n" + "\\n".join(summaries)
        
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
    
    # Get relevant memories
    try:
        relevant_memories = get_relevant_memories(user_message)
        relevant_memories_text = "\n".join(relevant_memories) if relevant_memories else "No relevant memories found."
    except Exception as e:
        relevant_memories_text = "No relevant memories (error accessing vector DB)."
    
    # Load a summary snapshot
    startup_memories = "\n".join([f"- {s}" for s in memory_snapshot])

    full_prompt = (
        f"{persona}\n"
        f"(Sentiment: {sentiment})\n"
        f"User Memory Snapshot:\n{startup_memories}\n\n"
        f"Recent Chat:\n{chat_history}\n"
        f"Relevant Memories:\n{relevant_memories_text}\n"
        f"User: {user_message}\nAI:"
    )

    ai_reply = generate_response(full_prompt, model=model)

    # Save to memory
    memory.append({"user": user_message, "ai": ai_reply})
    save_memory(MEMORY_PATH, memory)

    # Save summary
    id_summary = str(uuid.uuid4())
    save_summary(ai_reply, id_summary)

    # trigger new summary generation
    summarise_recent(memory)

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
        summaries = get_all_summaries()
        summary_text = "\n".join([f"- {s}" for s in summaries[-3:]])

    # Create the reflective prompt for the model
    prompt = (
        f"As an AI companion, reflect on the user's recent activity and emotional tone.\n\n"
        f"Recent summaries:\n{summary_text}\n\n"
        f"Sentiment trend:\n{sentiment_summary}\n\n"
        f"Reflect briefly, in 2-3 sentences, offering encouragement or support."
    )

    reflection = generate_response(prompt)
    return {
        # "summary_insight": summary_text,
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

@app.delete("/memory/vector")
def delete_vector_memory():
    clear_vector_memory()
    return {"message": "Vector memory cleared."}

