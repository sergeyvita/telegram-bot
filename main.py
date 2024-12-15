import os
import logging
from flask import Flask, request, jsonify
from openai import OpenAI
from openai.error import OpenAIError

# Настройка приложения Flask
app = Flask(__name__)

# Настройка OpenAI API
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route("/")
def index():
    return "Webhook is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        payload = request.json
        logger.debug(f"Полученный payload вебхука: {payload}")

        message = payload.get("message", {}).get("text", "")
        chat_id = payload.get("message", {}).get("chat", {}).get("id")

        if message:
            logger.info(f"Сообщение от {chat_id}: {message}")
            response_text = get_chatgpt_response(message)
            send_telegram_message(chat_id, response_text)
        return jsonify({"ok": True})
    except Exception as e:
        logger.error(f"Ошибка в обработке вебхука: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

def get_chatgpt_response(prompt):
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="gpt-4",
        )
        return response.choices[0].message["content"]
    except OpenAIError as e:
        logger.error(f"Ошибка подключения к OpenAI API: {e}")
        return "Произошла ошибка при обработке вашего запроса. Попробуйте позже."

def send_telegram_message(chat_id, text):
    import requests
    TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
    url = f"https://api.telegram.org/bot{TELEGRAM_API_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    response = requests.post(url, json=payload)
    logger.debug(f"Ответ Telegram: {response.json()}")

if __name__ == "__main__":
    PORT = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=PORT)
