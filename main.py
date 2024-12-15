import os
import logging
import asyncio
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import openai
import requests

# Загрузка переменных окружения
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Убедитесь, что эти переменные не равны None
if not TELEGRAM_BOT_TOKEN or not OPENAI_API_KEY or not WEBHOOK_URL:
    raise ValueError("Переменные окружения не загружены. Проверьте .env файл.")

# Инициализация бота и Flask приложения
app = Flask(__name__)
openai.api_key = OPENAI_API_KEY

PROMPT = (
    "Этот GPT выступает в роли профессионального создателя контента для Телеграм-канала Ассоциации застройщиков. "
    "Он создает максимально продающие посты на темы недвижимости, строительства, законодательства, инвестиций и связанных отраслей. "
    "Контент ориентирован на привлечение внимания, удержание аудитории и стимулирование действий (например, обращения за консультацией или покупки). "
    "GPT учитывает деловой, но не формальный тон и стремится быть доступным, информативным и вовлекающим. Посты красиво оформляются с использованием эмодзи в стиле 'энергичный и современный', "
    "добавляя динамичности и вовлеченности. Например: \ud83c\udfdf\ufe0f для темы строительства, \ud83c\udf1f для выделения преимуществ, \ud83d\udcf2 для призывов к действию. "
    "Все посты содержат четкие призывы к действию и информацию о контактах. В конце каждого поста указывается номер телефона Ассоциации застройщиков: 8-800-550-23-93 и название компании "
    "'Ассоциация застройщиков', которое также является гиперссылкой, ведущей на Телеграм-канал https://t.me/associationdevelopers."
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/", methods=["GET"])
def index():
    return "Телеграм-бот работает!"

@app.route("/webhook", methods=["POST"])
async def telegram_webhook():
    try:
        data = request.get_json()
        logger.info(f"Получено сообщение: {data}")

        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "")

            if text:
                response = await generate_content(text)
                send_message(chat_id, response)

        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error(f"Ошибка в обработке вебхука: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

async def generate_content(user_input):
    prompt = f"{PROMPT}\nПользовательский запрос: {user_input}"

    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[{"role": "system", "content": PROMPT}, {"role": "user", "content": user_input}],
            max_tokens=500,
            temperature=0.7,
        )
        return response.choices[0].message["content"]
    except Exception as e:
        logger.error(f"Ошибка в OpenAI API: {e}")
        return "Извините, произошла ошибка при генерации ответа. Попробуйте позже."

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            logger.error(f"Ошибка отправки сообщения: {response.text}")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))