from flask import Flask, request
import requests
import openai
import os
import logging
import traceback

# Настройки Telegram Bot и OpenAI API
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Переменная BOT_TOKEN не установлена.")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("Переменная OPENAI_API_KEY не установлена.")

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("main")

app = Flask(__name__)

@app.route('/')
def home():
    logger.info("Проверочный маршрут '/' успешно вызван.")
    return "Сервер работает!", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        logger.debug(f"Полученный payload вебхука: {data}")

        if not data or "message" not in data:
            logger.warning("Нет данных в запросе или отсутствует ключ 'message'.")
            return "No data received", 400

        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").strip()
        logger.info(f"Сообщение от {chat_id}: {text}")

        if text == "/start":
            send_message(
                chat_id,
                "Добро пожаловать! Напишите мне что-нибудь, и я помогу создать пост для Telegram."
            )
        elif text == "/help":
            send_message(
                chat_id,
                "Список команд:\n/start - начать работу\n/help - помощь\nЛюбое другое сообщение будет обработано."
            )
        else:
            response = get_chatgpt_response(text)
            send_message(chat_id, response)

        return "OK", 200
    except Exception as e:
        logger.error("Ошибка в обработке запроса:", exc_info=True)
        return "Internal Server Error", 500

def send_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        logger.debug(f"Отправка сообщения в Telegram: {payload}")
        response = requests.post(url, json=payload)
        logger.debug(f"Ответ Telegram: {response.json()}")
    except Exception as e:
        logger.error("Ошибка отправки сообщения в Telegram:", exc_info=True)

def get_chatgpt_response(prompt):
    try:
        assistant_instructions = (
            "Ты — профессиональный создатель контента для Телеграм-канала Ассоциации застройщиков. "
            "Создавай структурированные, продающие посты с использованием эмодзи на темы недвижимости, строительства, "
            "законодательства и инвестиций. В конце каждого поста добавляй: \"Звоните 📲 8-800-550-23-93 или переходите по ссылке: "
            "[Ассоциация застройщиков](https://t.me/associationdevelopers).\""
        )

        messages = [
            {"role": "system", "content": assistant_instructions},
            {"role": "user", "content": prompt},
        ]

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            max_tokens=1500,
            temperature=1.0,
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error("Ошибка вызова OpenAI API:", exc_info=True)
        return "Извините, произошла ошибка при обработке вашего запроса."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Запуск приложения на порту {port}")
    app.run(host="0.0.0.0", port=port)
