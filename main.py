import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import openai

# Загрузка переменных окружения из .env файла
load_dotenv()

# Переменные окружения :)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# Логи для отладки переменных окружения
print(f"TELEGRAM_BOT_TOKEN: {TELEGRAM_BOT_TOKEN}")
print(f"OPENAI_API_KEY: {OPENAI_API_KEY}")
print(f"WEBHOOK_URL: {WEBHOOK_URL}")

if not TELEGRAM_BOT_TOKEN or not OPENAI_API_KEY or not WEBHOOK_URL:
    raise ValueError("Не удалось загрузить обязательные переменные окружения. Проверьте .env файл или настройки Render.")

# Установка API-ключа OpenAI
openai.api_key = OPENAI_API_KEY

# Создание Flask-приложения
app = Flask(__name__)

# PROMT для OpenAI
PROMPT = (
    "Этот GPT выступает в роли профессионального создателя контента для Телеграм-канала Ассоциации застройщиков. "
    "Он создает максимально продающие посты на темы недвижимости, строительства, законодательства, инвестиций и связанных отраслей. "
    "Контент ориентирован на привлечение внимания, удержание аудитории и стимулирование действий (например, обращения за консультацией или покупки). "
    "GPT учитывает деловой, но не формальный тон и стремится быть доступным, информативным и вовлекающим. "
    "Посты красиво оформляются с использованием эмодзи в стиле \"энергичный и современный\", добавляя динамичности и вовлеченности. "
    "Например: 🏗️ для темы строительства, 🌟 для выделения преимуществ, 📲 для призывов к действию. "
    "Все посты содержат четкие призывы к действию и информацию о контактах. "
    "В конце каждого поста указывается номер телефона Ассоциации застройщиков: 8-800-550-23-93 и название компании \"Ассоциация застройщиков\", "
    "которое также является гиперссылкой, ведущей на Телеграм-канал https://t.me/associationdevelopers."
)

@app.route('/', methods=['GET'])
def home():
    return "Сервис работает!"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        print(f"Получены данные от Telegram: {data}")  # Отладочные логи

        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            user_message = data["message"].get("text", "")

            # Генерация ответа через OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": PROMPT},
                    {"role": "user", "content": user_message},
                ],
            )

            reply = response['choices'][0]['message']['content']
            send_message(chat_id, reply)

        return jsonify({"status": "ok"})
    except Exception as e:
        print(f"Ошибка в обработке вебхука: {e}")  # Отладочные логи
        return jsonify({"status": "error", "message": str(e)}), 500

def send_message(chat_id, text):
    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        response = requests.post(url, json=payload)
        print(f"Ответ Telegram API: {response.json()}")  # Отладочные логи
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")  # Отладочные логи

from waitress import serve

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))