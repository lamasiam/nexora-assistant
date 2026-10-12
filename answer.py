"""
answer.py
Terminal version of the assistant — now just a thin wrapper around
rag_core.py, so both this and the web app (app.py) share the exact
same retrieval + prompt logic. Useful for quick debugging without
opening a browser.
"""

import requests
import rag_core

collection = rag_core._get_collection()

if collection.count() == 0:
    print("No documents indexed yet — run ingest.py first.")
else:
    role_input = input("Are you an intern/trainee or a full-time employee? ").strip().lower()
    role = "intern/trainee" if "intern" in role_input or "trainee" in role_input else "full-time employee"

    question = input("Ask a question: ")

    print("\nThinking...")
    try:
        answer, sources = rag_core.answer_question(question, role)
    except requests.exceptions.ConnectionError:
        print("\nCouldn't reach Ollama. Make sure the Ollama app is running, "
              "and you've run 'ollama pull llama3.2' at least once.")
    except requests.exceptions.ReadTimeout:
        print("\nOllama took too long to respond. Try running 'ollama run llama3.2' "
              "once in a separate terminal first to load the model into memory, "
              "then run this script again — it should be much faster the second time.")
    else:
        print("\nAnswer:")
        print(answer)
        print(f"\nSource(s): {', '.join(sources)}")
