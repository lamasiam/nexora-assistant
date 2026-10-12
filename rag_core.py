"""
rag_core.py
The shared RAG (Retrieval-Augmented Generation) pipeline, used by both
answer.py (terminal) and app.py (web). Keeping this logic in ONE place
means a bug fix or prompt improvement only needs to happen once.
"""

import requests
from sentence_transformers import SentenceTransformer
import chromadb

_model = None
_collection = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path="chroma_db")
        _collection = client.get_or_create_collection("nexora_docs")
    return _collection


def get_context(question, n_results=3, max_distance=1.0):
    """Find the most relevant document(s) for the question.

    Always keeps the single closest match. Additional matches are only
    included if they're genuinely close in meaning (distance below
    max_distance) — not just "less far than the rest." This keeps the
    cited Source(s) list honest: we only cite what actually informed
    the answer, not whatever happened to be second-closest.
    """
    model = _get_model()
    collection = _get_collection()
    question_embedding = model.encode(question).tolist()
    results = collection.query(query_embeddings=[question_embedding], n_results=n_results)

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    filtered_docs = [docs[0]]
    filtered_sources = [metas[0]["source"]]
    for doc, meta, dist in zip(docs[1:], metas[1:], distances[1:]):
        if dist <= max_distance:
            filtered_docs.append(doc)
            filtered_sources.append(meta["source"])

    context_text = "\n\n".join(filtered_docs)
    return context_text, filtered_sources


def generate_answer(question, context, role):
    """Ask the local Ollama model to answer, tailored to the employee's role."""
    prompt = f"""You are a helpful internal company assistant for Nexora R&D employees.
The person asking is a {role}.

Answer the employee's question using ONLY the information in the context below.
If the context contains different rules for different employee types (for example,
interns/trainees vs confirmed full-time staff), give the answer that applies
specifically to a {role} — do not default to the full-time answer unless the
employee is full-time. You may briefly mention that other employee types have
different rules, but lead with the answer for a {role}.
If the answer is not contained in the context, say clearly that you don't have
that information, rather than guessing or making something up. If the context
describes a multi-step process, include every step in your answer — do not
omit any step, especially ones related to security, safety, or deadlines.
Keep the answer short and direct, but never at the cost of leaving out a
necessary step.

Context:
{context}

Question: {question}

Answer:"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2},  # low = more consistent, factual answers
        },
        timeout=300,
    )
    response.raise_for_status()
    return response.json()["response"].strip()


def answer_question(question, role):
    """The full pipeline in one call: retrieve relevant context, then generate an answer."""
    context, sources = get_context(question)
    answer = generate_answer(question, context, role)
    return answer, list(set(sources))
