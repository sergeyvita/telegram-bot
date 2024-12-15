import os
import logging
from flask import Flask, request, jsonify
import requests
import openai

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PORT = int(os.getenv("PORT", 8080))

if not BOT_TOKEN:
    raise ValueError("Переменная BOT_TOKEN не установлена.")
if not OPENAI_API_KEY:
    raise ValueError("Переменная OPENAI_API_KEY не установлена.")

openai.api_key = OPENAI_API_KEY

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Инициализация Flask-приложения
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    logger.info("Проверочный маршрут '/' успешно вызван.")
    return "Сервер работает!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        logger.debug(f"Полученные данные вебхука: {data}")

        if not data or "message" not in data:
            logger.error("Некорректный запрос: отсутствует 'message' в payload.")
            return "Некорректный запрос", 400

        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").strip()
        logger.info(f"Сообщение от {chat_id}: {text}")

        if text == "/start":
            send_message(chat_id, "Добро пожаловать! Напишите мне что-нибудь, и я помогу создать пост для Telegram.")
        elif text == "/help":
            send_message(chat_id, "Список команд:\n/start - начать работу\n/help - помощь\nЛюбое другое сообщение будет обработано.")
        else:
            logger.info(f"Отправка текста '{text}' в OpenAI API.")
            response = get_chatgpt_response(text)
            logger.info(f"Получен ответ от OpenAI: {response}")
            send_message(chat_id, response)

        return "OK", 200
    except Exception as e:
        logger.error("Ошибка в обработке вебхука:", exc_info=True)
        return "Internal Server Error", 500

def send_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        logger.info(f"Отправка сообщения в Telegram: {payload}")
        response = requests.post(url, json=payload)
        logger.info(f"Ответ Telegram: {response.json()}")
    except Exception as e:
        logger.error("Ошибка отправки сообщения:", exc_info=True)

def get_chatgpt_response(prompt):
    try:
        assistant_instructions = (
            "Ты — профессиональный создатель контента для Телеграм-канала Ассоциации застройщиков. "
            "Создавай структурированные, продающие посты с использованием эмодзи на темы недвижимости, строительства, "
            "законодательства и инвестиций. В конце каждого поста добавляй: "
            "\"Звоните \ud83d\udcf2 8-800-550-23-93 или переходите по ссылке: [Ассоциация застройщиков](https://t.me/associationdevelopers).\""
        )

        logger.info(f"Отправка запроса в OpenAI: {prompt}")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": assistant_instructions},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=1.0,
        )
        result = response["choices"][0]["message"]["content"].strip()
        logger.info(f"Ответ от OpenAI: {result}")
        return result
    except openai.error.OpenAIError as e:
        logger.error("Ошибка вызова OpenAI API:", exc_info=True)
        return "Извините, произошла ошибка при обработке вашего запроса."

# Тестовое подключение к OpenAI при запуске сервера
try:
    logger.info("Тестирование подключения к OpenAI API...")
    openai.Model.list()
    logger.info("Успешное подключение к OpenAI API.")
except Exception as e:
    logger.error("Ошибка подключения к OpenAI API:", exc_info=True)

if __name__ == "__main__":
    logger.info(f"Запуск приложения на порту {PORT}")
    app.run(host="0.0.0.0", port=PORT)
