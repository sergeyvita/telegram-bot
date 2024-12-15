import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import openai
import aiohttp
import asyncio
from waitress import serve

# Загрузка переменных окружения
load_dotenv()

# Переменные окружения
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# Логи для отладки переменных окружения
print(f"TELEGRAM_BOT_TOKEN: {TELEGRAM_BOT_TOKEN}")
print(f"OPENAI_API_KEY: {OPENAI_API_KEY}")
print(f"WEBHOOK_URL: {WEBHOOK_URL}")

# Проверка наличия всех необходимых переменных
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
    "Добавьте контакты: Ассоциация застройщиков, 8-800-550-23-93, https://t.me/associationdevelopers."
)

@app.route('/', methods=['GET'])
def home():
    """
    Проверка состояния сервиса.
    """
    return "Сервис работает!"

@app.route('/webhook', methods=['POST'])
async def webhook():
    """
    Обработчик вебхуков от Telegram.
    """
    try:
        # Получение данных от Telegram
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
    """
    Генерация ответа с использованием OpenAI GPT.
    """
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",  # Используем GPT-4
            messages=[
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=1500,  # Максимальное количество токенов
            temperature=1.0,  # Степень случайности генерации
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Ошибка OpenAI API: {e}")
        return "Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже."

async def send_message(chat_id, text):
    """
    Асинхронная отправка сообщения в Telegram.
    """
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {"chat_id": chat_id, "text": text}
            async with session.post(url, json=payload) as resp:
                result = await resp.json()
                print(f"Ответ Telegram API: {result}")
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")

def setup_webhook():
    """
    Установка вебхука для Telegram.
    """
    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
        payload = {"url": WEBHOOK_URL}
        response = requests.post(url, json=payload)
        print(f"Установка вебхука: {response.json()}")
    except Exception as e:
        print(f"Ошибка установки вебхука: {e}")

if __name__ == "__main__":
    # Установка вебхука при запуске
    setup_webhook()
    # Запуск приложения через Waitress
    serve(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
