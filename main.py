from flask import Flask, request
import requests
import openai
import os
import traceback
import logging
import sys

# Настройки API ключей
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Переменная BOT_TOKEN не установлена.")

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("Переменная OPENAI_API_KEY не установлена.")

# Telegram API URL
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Flask приложение
app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)

@app.route('/')
def home():
    return "Сервер работает!", 200  # Проверочный маршрут для теста

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        app.logger.debug("Полученные данные от Telegram: %s", data)

        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "").strip()
            app.logger.debug(f"Сообщение от {chat_id}: {text}")

            if text == "/start":
                send_message(chat_id, "Добро пожаловать! Напишите мне что-нибудь, и я помогу создать пост для Telegram.")
            elif text == "/help":
                send_message(chat_id, "Список команд:\n/start - начать работу\n/help - помощь\nНапишите сообщение, чтобы я его обработал.")
            else:
                response = get_chatgpt_response(text)
                send_message(chat_id, response)

        return "OK", 200

    except Exception as e:
        app.logger.error("Ошибка в обработке запроса: %s", traceback.format_exc())
        return "Internal Server Error", 500

def send_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload)
        app.logger.debug("Ответ Telegram: %s", response.json())
    except Exception as e:
        app.logger.error("Ошибка отправки сообщения: %s", e)

def get_chatgpt_response(prompt):
    try:
        assistant_instructions = (
            "Ты — профессиональный создатель контента для Телеграм-канала Ассоциации застройщиков. "
            "Создавай структурированные, продающие посты с использованием эмодзи на темы недвижимости, строительства, "
            "законодательства и инвестиций. В конце каждого поста добавляй: \"Звоните 📲 8-800-550-23-93 или переходите по ссылке: [Ассоциация застройщиков](https://t.me/associationdevelopers).\""
        )

        response = openai.ChatCompletion.chat(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": assistant_instructions},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1500,
            temperature=1.0,
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        app.logger.error("Ошибка вызова OpenAI API: %s", traceback.format_exc())
        return f"Извините, произошла ошибка: {str(e)}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Порт по умолчанию
    app.run(host="0.0.0.0", port=port)