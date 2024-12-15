import os
import logging
from flask import Flask, request, jsonify
import openai
import asyncio
import requests

# Настройка логгера
logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Инициализация Flask
app = Flask(__name__)

# Установите токены и ключи
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "<ВАШ_ТЕЛЕГРАМ_ТОКЕН>")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "<ВАШ_API_KEY>")
openai.api_key = OPENAI_API_KEY

TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

PROMPT = (
    "Этот GPT выступает в роли профессионального создателя контента для Телеграм-канала Ассоциации застройщиков. "
    "Он создает максимально продающие посты на темы недвижимости, строительства, законодательства, инвестиций и связанных отраслей. "
    "Контент ориентирован на привлечение внимания, удержание аудитории и стимулирование действий (например, обращения за консультацией или покупки). "
    "GPT учитывает деловой, но не формальный тон и стремится быть доступным, информативным и вовлекающим. Посты красиво оформляются с использованием "
    "эмодзи в стиле 'энергичный и современный', добавляя динамичности и вовлеченности. Например: 🏗️ для темы строительства, 🌟 для выделения преимуществ, 📲 для призывов к действию. "
    "Все посты содержат четкие призывы к действию и информацию о контактах. В конце каждого поста указывается номер телефона Ассоциации застройщиков: "
    "8-800-550-23-93 и название компании «Ассоциация застройщиков», которое также является гиперссылкой, ведущей на Телеграм-канал https://t.me/associationdevelopers."
)

async def get_chatgpt_response(prompt):
    """Функция для получения ответа от OpenAI Chat API"""
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1500,
            temperature=1.0,
        )
        return response["choices"][0]["message"]["content"].strip()
    except openai.error.OpenAIError as e:
        logger.error("Ошибка вызова OpenAI API:", exc_info=True)
        return "Извините, произошла ошибка при обработке вашего запроса."

def send_message(chat_id, text):
    """Отправить сообщение в Telegram"""
    try:
        url = f"{TELEGRAM_URL}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        response = requests.post(url, json=payload)
        logger.info("Ответ Telegram: %s", response.json())
        return response.json()
    except Exception as e:
        logger.error("Ошибка отправки сообщения в Telegram:", exc_info=True)

@app.route("/webhook", methods=["POST"])
async def webhook():
    """Основной обработчик вебхука Telegram"""
    try:
        data = request.json
        logger.debug("Полученный полезная нагрузка вебхука: %s", data)

        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "")

            logger.info("Сообщение от %s: %s", chat_id, text)

            # Получить ответ от OpenAI
            response = await get_chatgpt_response(text)

            # Отправить ответ обратно в Telegram
            send_message(chat_id, response)

        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error("Ошибка обработки вебхука:", exc_info=True)
        return jsonify({"status": "error"}), 500

@app.route("/", methods=["GET"])
def index():
    """Маршрут проверки доступности сервиса"""
    logger.info("Проверочный маршрут '/' успешно вызван.")
    return "Сервис работает!", 200

if __name__ == "__main__":
    logger.info("Тестирование подключения к OpenAI API...")
    try:
        # Пробное подключение к OpenAI
        asyncio.run(openai.Model.alist())
        logger.info("Успешное подключение к OpenAI API")
    except Exception as e:
        logger.error("Ошибка подключения к OpenAI API:", exc_info=True)

    # Запуск приложения
    app.run(host="0.0.0.0", port=8080)
