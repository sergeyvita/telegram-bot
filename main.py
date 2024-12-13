from flask import Flask, request, jsonify
import requests
import openai
import os
import traceback

# Настройки API ключей
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Токен Telegram Bot
if not BOT_TOKEN:
    raise ValueError("Переменная BOT_TOKEN не установлена.")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # API ключ OpenAI
if not OPENAI_API_KEY:
    raise ValueError("Переменная OPENAI_API_KEY не установлена.")
openai.api_key = OPENAI_API_KEY

# Инициализация Flask приложения
app = Flask(__name__)

# Главная страница для проверки сервера
@app.route('/')
def home():
    return "Сервер работает!", 200

# Роут для обработки Webhook
@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        return "Webhook is set", 200  # Ответ для проверки вебхука Telegram

    try:
        print("POST запрос на /webhook")
        data = request.json
        if not data:
            print("Ошибка: JSON-данные отсутствуют")
            return jsonify({"error": "Invalid request data"}), 400

        print(f"Полученные данные: {data}")

        message = data.get("message")
        if not message:
            print("Ошибка: ключ 'message' отсутствует")
            return jsonify({"error": "Invalid message format"}), 400

        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip()
        print(f"Сообщение от пользователя {chat_id}: {text}")

        if text == "/start":
            send_message(chat_id, "Добро пожаловать! Бот работает корректно.")
        elif text == "/help":
            send_message(chat_id, "Список команд: /start, /help")
        else:
            response = get_chatgpt_response(text)
            send_message(chat_id, response)

        return jsonify({"status": "success"}), 200
    except Exception as e:
        print("Ошибка в обработке запроса:", traceback.format_exc())
        return jsonify({"error": "Internal Server Error"}), 500

# Функция отправки сообщений в Telegram
def send_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload)
        print(f"Ответ Telegram: {response.json()}")
    except Exception as e:
        print("Ошибка отправки сообщения в Telegram:", traceback.format_exc())

# Функция для работы с OpenAI API
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

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            max_tokens=1500,
            temperature=1.0,
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("Ошибка вызова OpenAI API:", traceback.format_exc())
        return "Извините, произошла ошибка при обработке вашего запроса."

# Запуск Flask приложения
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Порт по умолчанию для Render
    app.run(host="0.0.0.0", port=port)