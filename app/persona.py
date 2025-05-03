def respond_with_personality(user_input, memory, sentiment):
    neutral_response = f"I hear you. Could you tell me more about that?"

    if sentiment == "positive":
        return "That's great to hear. What else has been going well?"
    elif sentiment == "negative":
        return "I'm really sorry you're feeling this way. I'm here with you."
    else:
        return neutral_response
