import logging
import os
import traceback
from flask import Flask, request
import requests
import openai

# Настройка базового логирования
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

# Проверка и настройка API ключей
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logging.error("Переменная BOT_TOKEN не установлена.")
    raise ValueError("Переменная BOT_TOKEN не установлена.")
else:
    logging.info("Переменная BOT_TOKEN успешно загружена.")

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    logging.error("Переменная OPENAI_API_KEY не установлена.")
    raise ValueError("Переменная OPENAI_API_KEY не установлена.")
else:
    logging.info("Переменная OPENAI_API_KEY успешно загружена.")

# Telegram API URL
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Flask приложение
app = Flask(__name__)

@app.route('/')
def home():
    logging.info("Проверочный маршрут '/' успешно вызван.")
    return "Сервер работает!", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        logging.debug(f"Полученный payload вебхука: {data}")

        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "").strip()
            logging.info(f"Сообщение от {chat_id}: {text}")

            if text == "/start":
                send_message(chat_id, "Добро пожаловать! Напишите мне что-нибудь, и я помогу создать пост для Telegram.")
            elif text == "/help":
                send_message(chat_id, "Список команд:\n/start - начать работу\n/help - помощь\nНапишите сообщение, чтобы я его обработал.")
            else:
                response = get_chatgpt_response(text)
                send_message(chat_id, response)

        return "OK", 200

    except Exception as e:
        logging.exception("Ошибка в обработке запроса вебхука:")
        return "Internal Server Error", 500

def send_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        logging.debug(f"Отправка сообщения в Telegram: {payload}")
        response = requests.post(url, json=payload)
        logging.debug(f"Ответ Telegram: {response.json()}")
    except Exception as e:
        logging.exception("Ошибка при отправке сообщения в Telegram:")

def get_chatgpt_response(prompt):
    try:
        assistant_instructions = (
            "Ты — профессиональный создатель контента для Телеграм-канала Ассоциации застройщиков. "
            "Создавай структурированные, продающие посты с использованием эмодзи на темы недвижимости, строительства, "
            "законодательства и инвестиций. В конце каждого поста добавляй: \"Звоните \ud83d\udcf2 8-800-550-23-93 или переходите по ссылке: [Ассоциация застройщиков](https://t.me/associationdevelopers).\""
        )

        messages = [
            {"role": "system", "content": assistant_instructions},
            {"role": "user", "content": prompt},
        ]

        logging.debug(f"Отправляемые сообщения в OpenAI: {messages}")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            max_tokens=1500,
            temperature=1.0,
        )
        result = response["choices"][0]["message"]["content"].strip()
        logging.debug(f"Ответ OpenAI: {result}")
        return result

    except Exception as e:
        logging.exception("Ошибка вызова OpenAI API:")
        return "Извините, произошла ошибка при обработке вашего запроса."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Порт по умолчанию
    logging.info(f"Запуск приложения на порту {port}")
    app.run(host="0.0.0.0", port=port)
