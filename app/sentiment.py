from textblob import TextBlob
import json
import os

def analyse_sentiment(text: str) -> str:
    """
    Returns the sentiment category of the input text.
    Categories: 'positive', 'neutral', 'negative'
    """
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity

    if polarity > 0.2:
        return "positive"
    elif polarity < -0.2:
        return "negative"
    else:
        return "neutral"
    
def log_sentiment(sentiment, path="data/sentiment_log.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    log = []

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            log = json.load(f)

    log.append({"sentiment": sentiment})
    with open(path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)


