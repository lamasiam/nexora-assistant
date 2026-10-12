"""
telegram_bot.py
Telegram channel for the assistant. It uses the same rag_core.py brain as
the web app, so answers are identical on both channels.

How it works: the script repeatedly asks Telegram "any new messages?"
(called long polling). Because WE call Telegram, no public URL, ngrok or
webhook is needed. It runs fine on a laptop behind any network.

Needs a .env file next to this script containing:
    TELEGRAM_BOT_TOKEN=your_token_from_BotFather
"""

import os
import sys
import time

import requests
from dotenv import load_dotenv

import rag_core

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
if not TOKEN:
    sys.exit("TELEGRAM_BOT_TOKEN is missing. Create a .env file next to this script "
             "with the line: TELEGRAM_BOT_TOKEN=your_token")

API = f"https://api.telegram.org/bot{TOKEN}"

INTERN = "intern/trainee"
FULLTIME = "full-time employee"
BTN_INTERN = "Intern / Trainee"
BTN_FULLTIME = "Full-time"

# Remembers each chat's role while the bot is running (resets to intern on restart).
roles = {}

# Two buttons under the text box, like the toggle on the web page.
KEYBOARD = {
    "keyboard": [[{"text": BTN_INTERN}, {"text": BTN_FULLTIME}]],
    "resize_keyboard": True,
}

WELCOME = (
    "Hi! I'm the Nexora Assistant. Ask me about leave, IT, onboarding, "
    "expenses, or work-from-home policy.\n\n"
    "Right now I'm answering as: {role}.\n"
    "Use the buttons below to switch between Intern / Trainee and Full-time."
)


def call(method, payload=None, timeout=15):
    """Send one request to the Telegram Bot API."""
    return requests.post(f"{API}/{method}", json=payload or {}, timeout=timeout)


def send_message(chat_id, text, with_keyboard=False):
    payload = {"chat_id": chat_id, "text": text[:4000]}  # Telegram limit is 4096
    if with_keyboard:
        payload["reply_markup"] = KEYBOARD
    try:
        call("sendMessage", payload)
    except requests.exceptions.RequestException as e:
        # Print only the error type: the full message could contain the token.
        print(f"Could not send a message ({type(e).__name__}).")


def send_typing(chat_id):
    try:
        call("sendChatAction", {"chat_id": chat_id, "action": "typing"})
    except requests.exceptions.RequestException:
        pass


def handle_message(message):
    chat_id = message["chat"]["id"]
    text = (message.get("text") or "").strip()

    if not text:
        send_message(chat_id, "I can only read text messages for now.")
        return

    role = roles.get(chat_id, INTERN)

    # Commands look like "/start" or "/start@botname"
    command = text.lower().split()[0].split("@")[0] if text.startswith("/") else ""

    if command in ("/start", "/help"):
        send_message(chat_id, WELCOME.format(role=role), with_keyboard=True)
        return

    if text == BTN_INTERN or command == "/intern":
        roles[chat_id] = INTERN
        send_message(chat_id, "Okay, I'll answer as for an intern/trainee.", with_keyboard=True)
        return

    if text == BTN_FULLTIME or command == "/fulltime":
        roles[chat_id] = FULLTIME
        send_message(chat_id, "Okay, I'll answer as for a full-time employee.", with_keyboard=True)
        return

    if command:
        send_message(chat_id, "I don't know that command. Just type your question, "
                              "or send /help.")
        return

    # Otherwise, treat it as a question for the assistant.
    send_typing(chat_id)
    try:
        answer, sources = rag_core.answer_question(text, role)
    except requests.exceptions.ConnectionError:
        send_message(chat_id, "Sorry, my AI model isn't reachable right now. "
                              "(Is Ollama running?)")
        return
    except requests.exceptions.ReadTimeout:
        send_message(chat_id, "Sorry, that took too long. Please try again.")
        return
    except Exception as e:
        print(f"Error while answering ({type(e).__name__}).")
        send_message(chat_id, "Sorry, something went wrong while answering.")
        return

    reply = answer
    if sources:
        reply += "\n\nSource: " + ", ".join(sources)
    send_message(chat_id, reply)


def verify_token():
    """Ask Telegram who we are. Fails early with a clear message if the token is wrong."""
    try:
        r = call("getMe")
    except requests.exceptions.RequestException as e:
        sys.exit(f"Could not reach Telegram ({type(e).__name__}). Check your internet connection.")
    if r.status_code == 401:
        sys.exit("Telegram rejected the token. Check the line in your .env file: "
                 "no quotes, no spaces, and the full token copied from BotFather.")
    if r.status_code != 200:
        sys.exit(f"Telegram returned status {r.status_code} while checking the token.")
    return r.json()["result"]["username"]


def main():
    username = verify_token()
    print(f"Connected to Telegram as @{username}")
    print("Loading the search model (a few seconds)...")
    rag_core._get_model()
    rag_core._get_collection()
    print("Ready. Waiting for messages. Press Ctrl+C to stop.")

    offset = None  # tells Telegram which messages we've already handled
    while True:
        payload = {"timeout": 30, "allowed_updates": ["message"]}
        if offset is not None:
            payload["offset"] = offset

        try:
            r = call("getUpdates", payload, timeout=45)
        except requests.exceptions.RequestException as e:
            print(f"Network problem ({type(e).__name__}). Retrying in 5 seconds...")
            time.sleep(5)
            continue

        if r.status_code == 409:
            print("Conflict: another copy of this bot is already running. "
                  "Close the other terminal, then restart.")
            time.sleep(5)
            continue
        if r.status_code != 200:
            print(f"Telegram returned status {r.status_code}. Retrying in 5 seconds...")
            time.sleep(5)
            continue

        for update in r.json().get("result", []):
            offset = update["update_id"] + 1
            message = update.get("message")
            if message:
                try:
                    handle_message(message)
                except Exception as e:
                    print(f"Unexpected error ({type(e).__name__}).")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
