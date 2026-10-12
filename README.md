# Nexora Assistant

An AI onboarding assistant for new interns and trainees. They ask a question in plain English
and get a short answer, with the source document named. It runs fully on a local machine
(local AI model, local search database), so no paid API is needed.

It is a prototype built as an internship Initiative project. All documents in `documents/`
are **fictional** sample policies for a made-up company, not real company data.

## What it does

- Finds the right document for a question using semantic search (by meaning, not keywords)
- Writes a short answer with a local AI model, using only the retrieved text
- Answers for the right employee type (Intern/Trainee or Full-time)
- Says "I don't have that information" instead of guessing
- Works on two channels with the same brain: a web chat page and a Telegram bot

## How it works

1. `ingest.py` splits each document into sections and stores them as embeddings in ChromaDB.
2. A question is turned into an embedding, and the closest sections are retrieved.
3. Ollama (Llama 3.2) writes the answer from those sections only.
4. `rag_core.py` holds this logic. `app.py` (web) and `telegram_bot.py` (Telegram) both use it.

## Tools

Python, Flask, Sentence-Transformers (all-MiniLM-L6-v2), ChromaDB, Ollama with Llama 3.2,
Telegram Bot API (plain HTTPS long polling).

## Setup

You need Python 3.10+, [Ollama](https://ollama.com), and about 3 GB of free disk space.

```
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
ollama pull llama3.2
python ingest.py               # builds the search index from documents/
```

## Run the web app

```
python app.py
```

Open http://127.0.0.1:5000

## Run the Telegram bot

1. In Telegram, talk to @BotFather, send `/newbot`, and copy the token it gives you.
2. Create a file named `.env` next to `telegram_bot.py` with one line:
   ```
   TELEGRAM_BOT_TOKEN=your_token_here
   ```
3. Run:
   ```
   python telegram_bot.py
   ```
4. Open your bot in Telegram and send `/start`.

Never commit the `.env` file. It is listed in `.gitignore`.

## Testing

```
python evaluate.py
```

Runs 12 test questions (10 answerable, 2 that must be refused) through the real pipeline
and saves `results.csv`.

| Metric | Result |
|---|---|
| Retrieval accuracy (right document found) | 100% (10/10) |
| Answer accuracy (key fact in answer) | 90% (9/10) |
| Hallucination avoidance (admits it doesn't know) | 100% (2/2) |

During development, retrieval improved from 80% to 100% after splitting documents into
sections, and answers improved after the prompt was changed to require every step of a process.

## Known limitations

- The test set is small (12 questions) and uses fictional documents.
- AI wording can vary slightly between runs, so one keyword check can fail on a correct answer.
- The Telegram bot remembers each user's role only while it is running.
- The bot handles one message at a time, which is fine for a pilot but not for many users.
- Messages sent through Telegram pass through Telegram's servers, even though the AI model
  and the documents stay local.
- Anyone who finds the bot's username can message it. Add access control before using real
  documents.

## Project structure

```
app.py              web server
templates/          web chat page
rag_core.py         search + answer logic (shared)
ingest.py           builds the search index
telegram_bot.py     Telegram channel
evaluate.py         accuracy test runner
test_cases.py       the 12 test questions
ask.py, answer.py   terminal tools for debugging
documents/          fictional sample policies
```
