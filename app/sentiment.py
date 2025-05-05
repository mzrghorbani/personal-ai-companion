from textblob import TextBlob

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

