import requests
import yaml

# Load from YAML
def load_config(path="app/config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

config = load_config()
DEFAULT_MODEL = config.get("model", "phi")
OLLAMA_URL = "http://localhost:11434/api/generate"

def generate_response(prompt: str, model: str = None) -> str:
    model = model or DEFAULT_MODEL
    formatted_prompt = (
        f"You are a helpful, supportive AI companion.\n"
        f"User: {prompt}\nAI:"
    )

    try:
        response = requests.post(OLLAMA_URL, json={
            "model": model,
            "prompt": formatted_prompt,
            "stream": False
        })

        if response.ok:
            data = response.json()
            return data.get("response", "").strip() or "[The model returned an empty response.]"
        else:
            return f"[Model error: {response.status_code}]"

    except Exception as e:
        return f"[Connection error: {e}]"
