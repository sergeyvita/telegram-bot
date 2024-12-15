from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import openai
import requests

# Загрузка переменных окружения из .env файла
load_dotenv()

# Переменные окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Проверка обязательных переменных
if not TELEGRAM_BOT_TOKEN or not OPENAI_API_KEY or not WEBHOOK_URL:
    raise ValueError("Не удалось загрузить обязательные переменные окружения. Проверьте .env файл или настройки Render.")

# Установка API ключа OpenAI
openai.api_key = OPENAI_API_KEY

# Инициализация Flask приложения
app = Flask(__name__)

# PROMT для генерации контента
PROMPT = (
    "Этот GPT выступает в роли профессионального создателя контента для Телеграм-канала Ассоциации застройщиков. "
    "Он создает максимально продающие посты на темы недвижимости, строительства, законодательства, инвестиций и связанных отраслей. "
    "Контент ориентирован на привлечение внимания, удержание аудитории и стимулирование действий (например, обращения за консультацией или покупки). "
    "GPT учитывает деловой, но не формальный тон и стремится быть доступным, информативным и вовлекающим. "
    "Посты красиво оформляются с использованием эмодзи в стиле 'энергичный и современный', добавляя динамичности и вовлеченности. "
    "Например: \ud83c\udf07 для темы строительства, \u2728 для выделения преимуществ, \ud83d\udcf2 для призывов к действию. "
    "Все посты содержат четкие призывы к действию и информацию о контактах. В конце каждого поста указывается номер телефона "
    "Ассоциации застройщиков: 8-800-550-23-93 и название компании \"Ассоциация застройщиков\", которое также является гиперссылкой, ведущей на Телеграм-канал https://t.me/associationdevelopers."
)

# Маршрут для проверки
@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "OK", "message": "Бот работает"}), 200

# Маршрут для обработки вебхуков Telegram
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({"status": "ignored"}), 200

    message = data["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    if text:
        # Генерация ответа с помощью OpenAI
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": PROMPT},
                    {"role": "user", "content": text},
                ],
                max_tokens=500,
                temperature=0.7,
            )

            reply = response["choices"][0]["message"]["content"]
        except Exception as e:
            reply = f"Произошла ошибка при обработке запроса: {str(e)}"

        # Отправка ответа пользователю в Telegram
        send_message(chat_id, reply)

    return jsonify({"status": "handled"}), 200

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")

# Установка вебхука при запуске приложения
def set_webhook():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
    payload = {"url": WEBHOOK_URL}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Вебхук успешно установлен")
        else:
            print(f"Ошибка установки вебхука: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Ошибка подключения к Telegram API: {e}")

if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=8080)