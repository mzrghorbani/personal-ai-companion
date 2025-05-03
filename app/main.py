from memory import load_memory, save_memory, summarise_memory
from persona import respond_with_personality
from sentiment import analyse_sentiment
import os

DATA_PATH = "data/memory_store.json"

def main():
    print("Welcome to your personal AI companion. Type 'exit' to quit.\n")
    
    memory = load_memory(DATA_PATH)

    while True:
        user_input = input("You: ")

        if user_input.lower() in ['exit', 'quit']:
            print("AI: Take care. Talk to you soon.")
            break

        sentiment = analyse_sentiment(user_input)
        response = respond_with_personality(user_input, memory, sentiment)
        print(f"AI: {response}")

        memory.append({"user": user_input, "ai": response})
        save_memory(DATA_PATH, memory)

        if len(memory) > 20:
            memory = summarise_memory(memory)
            save_memory(DATA_PATH, memory)

if __name__ == "__main__":
    main()
