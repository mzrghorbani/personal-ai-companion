import uuid
import chromadb
from sentence_transformers import SentenceTransformer
from .persona import get_persona_prompt
from .llm import generate_response
from .memory_store import chunk_memory, summarise_memory

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="summaries")
model = SentenceTransformer('all-mpnet-base-v2')

def get_vector(text):
    return model.encode(text).tolist()

def save_summary(summary, id_summary=None):
    vector = get_vector(summary)
    collection.add(
        embeddings=[vector],
        documents=[summary],
        ids=[id_summary or str(uuid.uuid4())],
    )

def get_relevant_memories(user_input, n_results=3):
    vector = get_vector(user_input)
    results = collection.query(
        query_embeddings=[vector],
        n_results=n_results
    )
    return results['documents'][0] if results['documents'] else []

def summarise_chunk(chunk, generate_fn):
    text = "\n".join([f"User: {m['user']}\nAI: {m['ai']}" for m in chunk])
    prompt = (
        f"{get_persona_prompt()}\n\n"
        "Summarise the following conversation in exactly 2 short bullet points. "
        "Each point must be no more than 20 words. Focus only on the user's actions, questions, or emotions.\n\n"
        f"{text}\n\n"
        "Summary:\n-"
    )
    return generate_fn(prompt)

def get_all_summaries():
    results = collection.get(include=['documents'])
    return results['documents']

def summarise_recent(memory):
    try:
        trimmed = summarise_memory(memory)
        summary = summarise_chunk(trimmed, generate_response)
        id_summary = str(uuid.uuid4())
        save_summary(summary, id_summary)
        return {"message": "Summary saved successfully."}
    except Exception as e:
        print(f"An error occurred in summarize_new: {e}")

def clear_vector_memory():
    collection.delete(where_document=None)

def generate_reflection(sentiments=None):
    results = collection.query(
        query_embeddings=None,
        n_results=3,
        include=['documents']
    )
    summaries = results['documents'][0] if results['documents'] else []
    summary_text = "\n".join([f"- {s}" for s in summaries])

    if not sentiments:
        sentiment_summary = "No sentiment data available."
    else:
        total = len(sentiments)
        counts = {s: sentiments.count(s) for s in set(sentiments)}
        top = max(counts, key=counts.get)
        sentiment_summary = f"You've mostly expressed **{top}** emotions, based on {total} recent messages."

    prompt = (
        f"{get_persona_prompt()}\n\n"
        f"As an AI companion, reflect on the user's recent activity and emotional tone.\n\n"
        f"Recent summaries:\n{summary_text}\n\n"
        f"Sentiment trend:\n{sentiment_summary}\n\n"
        f"Reflect briefly, in 2-3 sentences, offering encouragement or support."
    )

    return generate_response(prompt)
