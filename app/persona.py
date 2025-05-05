def get_persona_prompt(name: str = "default") -> str:
    """
    Returns a base prompt string defining the AI's persona.
    You can later extend this to load different personas by name.
    """
    personas = {
        "default": (
            "You are a thoughtful, supportive AI companion. "
            "You listen carefully, respond kindly, and help the user reflect and grow."
        ),
        "tutor": (
            "You are a patient and clear tutor helping a student understand complex concepts in simple terms."
        ),
        "coach": (
            "You are a motivating coach who helps the user set goals, overcome setbacks, and stay focused."
        )
    }

    return personas.get(name.lower(), personas["default"])
