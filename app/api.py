from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from .llm import generate_response, DEFAULT_MODEL
from .sentiment import analyse_sentiment
from .memory import load_memory, save_memory
from .persona import get_persona_prompt
from .memory import summarise_memory, load_memory, save_memory

import requests
import time

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
    if "what do you remember?" in user_message.lower():
        summary_text = "\n".join([
            f"User: {m['user']}\nAI: {m['ai']}"
            for m in summarise_memory(memory)
        ])
        ai_reply = (
            "Here’s what I recall from our recent conversation:\n\n"
            f"{summary_text}\n\n"
            "Let me know if you want to continue where we left off."
        )
        
        # Add to memory even though this wasn't LLM-generated
        memory.append({"user": user_message, "ai": ai_reply})
        save_memory(MEMORY_PATH, memory)

        # ⚠ Do NOT save this special interaction to memory
        return {"response": ai_reply}

    # Normal chat flow
    sentiment = analyse_sentiment(user_message)
    persona = get_persona_prompt()

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



