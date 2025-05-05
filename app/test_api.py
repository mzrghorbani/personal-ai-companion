import requests

print("Welcome to your AI Companion (via API). Type 'exit' to quit.\n")

while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        print("Goodbye!")
        break

    try:
        response = requests.post("http://localhost:8000/chat", json={
            "message": user_input
        })

        if response.ok:
            print(f"AI: {response.json().get('response', '[No response]')}\n")
        else:
            print("AI: Request failed.\n")

    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
