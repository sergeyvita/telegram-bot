import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import openai
import aiohttp
import asyncio

# Загрузка переменных окружения
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# Логи переменных окружения
print(f"TELEGRAM_BOT_TOKEN: {TELEGRAM_BOT_TOKEN}")
print(f"OPENAI_API_KEY: {OPENAI_API_KEY}")
print(f"WEBHOOK_URL: {WEBHOOK_URL}")

if not TELEGRAM_BOT_TOKEN or not OPENAI_API_KEY or not WEBHOOK_URL:
    raise ValueError("Не удалось загрузить обязательные переменные окружения. Проверьте .env файл или настройки Render.")

# Установка API-ключа OpenAI
openai.api_key = OPENAI_API_KEY

# Создание Flask-приложения
app = Flask(__name__)

# PROMPT для OpenAI
PROMPT = (
    "Этот GPT выступает в роли профессионального создателя контента для Телеграм-канала Ассоциации застройщиков. "
    "Он создает максимально продающие посты на темы недвижимости, строительства, законодательства, инвестиций и связанных отраслей. "
    "Контент ориентирован на привлечение внимания, удержание аудитории и стимулирование действий. "
    "Посты красиво оформляются с использованием эмодзи и содержат четкие призывы к действию. "
)

@app.route('/', methods=['GET'])
def home():
    return "Сервис работает!"

@app.route('/webhook', methods=['POST'])
async def webhook():
    try:
        data = request.get_json()
        print(f"Получены данные от Telegram: {data}")
        if not data:
            return jsonify({"status": "no data"}), 400

        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            user_message = data["message"].get("text", "")
            print(f"Chat ID: {chat_id}, Message: {user_message}")

            # Асинхронное взаимодействие с OpenAI
            response = await generate_openai_response(user_message)
            await send_message(chat_id, response)

        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print(f"Ошибка обработки вебхука: {e}")
        return jsonify({"error": str(e)}), 500

async def generate_openai_response(user_message):
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": user_message},
            ],
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Ошибка OpenAI API: {e}")
        return "Произошла ошибка при обработке запроса."

async def send_message(chat_id, text):
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {"chat_id": chat_id, "text": text}
            async with session.post(url, json=payload) as resp:
                result = await resp.json()
                print(f"Ответ Telegram API: {result}")
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")

from waitress import serve

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
