# Personal AI Companion

A modular, terminal-based personal AI assistant designed to store memory, respond supportively, and adapt based on user sentiment.

## Features

- Text-based chat interface
- Local JSON memory storage
- Sentiment-aware responses
- Modular and extendable codebase

## Getting Started

- Python 3.11.9 (Tested)
- Dependencies (Tested)

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python -m textblob.download_corpora
```

## Download Ollama

For Windows users, Ollama is available here:

```bash
https://ollama.com/download/windows
```

List of all [models](https://ollama.com/library) currently supported.

For Linux users, Ollama can be installed by:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

## Here's Ollama Model Workflow

```bash
ollama serve
```

Starts the background API server on <http://localhost:11434>

This is all you need for your Python app to send requests

```bash
ollama pull <model>
```

(Optional) Downloads the model manually before first use

Example: ollama pull phi

If you don’t do this, Ollama will automatically pull the model the first time you call it through the API.

```bash
ollama run <model>
```

Ollama will:

- Load the model into memory (if not already loaded)
- Run the prompt
- Return the response as JSON
- Keep the model cached in RAM for faster reuse

### Port Troubleshooting

How to Check What's Using Port 11434 (Windows):

```bash
netstat -aon | findstr :11434
```

Find the Application Using That PID:

```bash
tasklist /FI "PID eq <pid_number>"
```

How to Stop the Process:

```bash
taskkill /PID <pid_number> /F
```

## Modeling Process

A local, modular AI companion that can:

- Remember your past conversations
- Reflect on your mood and goals
- Switch between different personas (e.g. coach, study buddy, therapist)
- Respond naturally using an LLM served via Ollama

## Features

- FastAPI backend with clean /chat interface
- LLM integration via Ollama (supports Mistral, Phi, etc.)
- Memory system that stores conversation context in memory_store.json
- Summarisation of memory into short bullet logs
- Sentiment analysis for each user message
- Runtime persona switching (e.g. "switch to coach")
- Reflection mode triggered on exit
- Configurable via config.yaml

## Setup

Step 1 - Start Ollama and Load Model

```bash
ollama serve
ollama run mistral  # or phi, etc.
```

Ensure your model name matches the one in app/config.yaml.

Step 2 - Start the API Server

```bash
uvicorn app.api:app --reload
```

Step 3 - Interact via Terminal (for testing)

```bash
python app/test_api.py
```

Type messages and interact with the model. Type "exit" to end the conversation.

## API Overview

### Health Check

```bash
GET /status
```

### Returns

```json
{
  "model": "mistral",
  "status": "ok",
  "timestamp": "2025-05-05T11:24:36"
}
```

### Memory

- Stores recent user/AI exchanges in data/memory_store.json
- Summarised into bullet points via /summarise/memory
- Queryable with "What do you remember?"

```bash
DELETE /memory
```

### Sentiment Tracking

- Classifies each user message as positive, neutral, or negative
- Stored in data/sentiment_log.json

```bash
DELETE /sentiment
```

### Persona System

- Define AI behaviour (e.g. "supportive", "coach", "study_buddy")
- Switch at runtime:

```bash
switch to coach
```

Or via API:

```bash
POST /persona/coach
GET  /persona
```

### Reflective Exit

Typing "bye" or "exit" triggers a reflection response that:

- Analyses recent summaries and sentiment
- Provides a gentle closing comment
- Logs it to memory

### Reset Data

```bash
curl.exe -X DELETE http://localhost:8000/memory     # clears chat memory
curl.exe -X DELETE http://localhost:8000/summary    # clears summary log
curl.exe -X DELETE http://localhost:8000/sentiment  # clears sentiment log
```

Project Structure

```bash
app/
├── api.py            # Main FastAPI server
├── llm.py            # Interface with Ollama
├── memory.py         # Chat memory logic + summarisation
├── sentiment.py      # Sentiment analysis and logging
├── persona.py        # Persona management + state
├── test_api.py       # Local testing script
└── config.yaml       # Model and global settings
```

### Coming Soon Ideas

- Persistent user profiles
- Emotion dashboards
- Custom user-defined personas
- Long-term memory indexing
