"""
ingest.py
Reads every .md file in the 'documents' folder, splits each one into
smaller topic-focused chunks (by '## ' section headings), converts
each chunk into an embedding, and stores it in a local ChromaDB
database so it can be searched later.

Run this once now, and again any time you add or change a document.
IMPORTANT: if you're re-running this after already indexing whole
documents before, delete the 'chroma_db' folder first so old,
un-chunked entries don't linger alongside the new chunked ones.
"""

import os
import re
from sentence_transformers import SentenceTransformer
import chromadb

DOCS_FOLDER = "documents"


def chunk_document(text):
    """Split a markdown document into sections by '## ' headings.
    Each section (heading + its content) becomes its own chunk, so
    retrieval can match a specific topic instead of a whole multi-topic
    file. Falls back to the whole document if no '## ' headings exist.
    """
    sections = re.split(r"\n(?=## )", text)
    sections = [s.strip() for s in sections if s.strip()]
    return sections if len(sections) > 1 else [text]


print("Loading the embedding model (first run downloads it — needs internet once)...")
model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_or_create_collection("nexora_docs")

files = [f for f in os.listdir(DOCS_FOLDER) if f.endswith(".md")]

if not files:
    print(f"No .md files found in '{DOCS_FOLDER}'. Did you move them in?")
else:
    for filename in files:
        filepath = os.path.join(DOCS_FOLDER, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_document(text)
        for idx, chunk in enumerate(chunks):
            embedding = model.encode(chunk).tolist()
            # Each chunk gets its own ID, but metadata still points back
            # to the original filename — so citations stay at the
            # document level, not the confusing chunk level.
            collection.upsert(
                ids=[f"{filename}__chunk{idx}"],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[{"source": filename}],
            )
        print(f"Indexed: {filename} ({len(chunks)} chunk(s))")

    print(f"\nDone! {len(files)} document(s) are now searchable.")
