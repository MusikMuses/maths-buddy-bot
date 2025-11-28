import os
from flask import Flask, request
import requests
import openai
import json

app = Flask(__name__)

# === GET VALUES FROM RENDER ENVIRONMENT ===
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY


# === FUNCTION TO SEND MESSAGES BACK TO WHATSAPP ===
def send_message(to, text):
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": text}
    }
    requests.post(url, json=data, headers=headers)


# === WEBHOOK VERIFICATION (META USES GET) ===
@app.route('/webhook', methods=['GET'])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification failed", 403


# === PROCESS INCOMING WHATSAPP MESSAGES (META USES POST) ===
@app.route('/webhook', methods=['POST'])
def incoming():
    data = request.get_json()

    try:
        msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
        sender = msg["from"]

        if "text" in msg:
            user_message = msg["text"]["body"]
        else:
            user_message = "Please send a maths question in text 🙂"

        system_prompt = open("system_prompt.txt").read()

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )

        reply = response["choices"][0]["message"]["content"]
        send_message(sender, reply)

    except Exception as e:
        print("ERROR:", e)

    return "OK", 200


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
