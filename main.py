import os
import logging
import asyncio
from flask import Flask, request, jsonify
import openai
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация Flask
app = Flask(__name__)

# Настройки токенов и ключей
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    logger.error("Необходимо задать TELEGRAM_TOKEN и OPENAI_API_KEY в переменных окружения.")
    exit(1)

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/"
openai.api_key = OPENAI_API_KEY

# Функция отправки сообщений в Telegram
def send_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        logger.error(f"Ошибка отправки сообщения: {response.text}")

# Асинхронная функция для обработки запросов к OpenAI API
async def get_chatgpt_response(prompt):
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Этот GPT помогает отвечать на запросы."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        logger.error(f"Ошибка взаимодействия с OpenAI API: {e}")
        return "Извините, произошла ошибка при обработке вашего запроса."

# Маршрут для проверки работоспособности
@app.route("/", methods=["GET"])
def index():
    return "Бот работает!", 200

# Маршрут для обработки вебхуков Telegram
@app.route("/webhook", methods=["POST"])
async def webhook():
    try:
        data = request.json
        logger.info(f"Получен запрос: {data}")

        if "message" not in data:
            return jsonify({"status": "error", "message": "Invalid payload"}), 400

        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text:
            response_text = await get_chatgpt_response(text)
            send_message(chat_id, response_text)

        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

# Точка входа
if __name__ == "__main__":
    # Проверка подключения к OpenAI API
    try:
        asyncio.run(
            openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[{"role": "system", "content": "Проверка подключения к OpenAI API"}],
                max_tokens=5,
            )
        )
        logger.info("Успешно подключено к OpenAI API.")
    except Exception as e:
        logger.error(f"Ошибка подключения к OpenAI API: {e}")

    # Запуск Flask с waitress
    from waitress import serve
    serve(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))