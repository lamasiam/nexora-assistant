"""
ask.py
Takes a plain-English question, converts it into an embedding the same way
ingest.py did for the documents, then asks ChromaDB which stored document(s)
are closest in meaning. This is PURE RETRIEVAL — it returns the matching
document text, not yet a generated natural-language answer. That comes in
Phase 3, once we confirm retrieval itself is accurate.
"""

from sentence_transformers import SentenceTransformer
import chromadb

model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_or_create_collection("nexora_docs")

if collection.count() == 0:
    print("No documents indexed yet — run ingest.py first.")
else:
    question = input("Ask a question: ")
    question_embedding = model.encode(question).tolist()

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=2,  # show the top 2 closest matches
    )

    print("\nMost relevant document(s):")
    for doc, meta, distance in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        print(f"\n--- From: {meta['source']}  (distance: {distance:.3f}, lower = closer match) ---")
        print(doc[:400], "...")
