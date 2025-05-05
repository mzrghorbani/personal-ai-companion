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

Starts the background API server on http://localhost:11434

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

Opens an interactive chat in the terminal

Useful for manual testing—but not needed when calling from your app

### What Happens When You Call /api/generate

Your Python code (via FastAPI) sends a prompt to:

```bash
http://localhost:11434/api/generate
```

With payload:

```json
{
  "model": "phi",
  "prompt": "Hello!",
  "stream": false
}
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

## Running the Model and Interact via API

### Install Dependencies

```bash
pip install fastapi uvicorn
```

### Run Your API Server

```bash
uvicorn app.api:app --reload
```

### Run api.py (single request)

```bash
python .\app\test_api.py
```

Exit the conversation by entering "exit"!

## Stop & Start Services

- ollama serve running on port 11434
- uvicorn app.api:app --reload running on port 8000
- Your model properly loaded via config.yaml

## Check API Status

FastAPI /status endpoint at http://localhost:8000/status acts as a central health check for:

- API backend (FastAPI / Uvicorn)
- The model server (Ollama)
- The specific model defined in config.yaml

The status must return:

```json
{"model":"minstral","status":"model_error","timestamp":"2025-05-05 11:24:36"}
```

## Sentiment Module (sentiment.py)

What it does:

- Analyses the emotional tone of each user message
- Classifies it as:
  - 'positive': generally upbeat or affirming
  - 'neutral': factual or ambiguous
  - 'negative': frustrated, sad, or critical

## Persona Module (persona.py)

What it does:

- Provides a system-level instruction that defines the AI’s personality
  - Kind? Playful? Logical?
- Currently returns a static string that gets included in the LLM prompt

## Memory (memory.py)

What it does:

- Integrate memory into the model

