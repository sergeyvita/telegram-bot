from flask import Flask, request, jsonify
import requests
import openai
import os
import traceback

# Настройки API ключей
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Переменная BOT_TOKEN не установлена.")

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("Переменная OPENAI_API_KEY не установлена.")

# Telegram API URL
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Flask приложение
app = Flask(__name__)

@app.route('/')
def home():
    return "Сервер работает!", 200  # Проверочный маршрут для теста

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        print("Полученные данные от Telegram:", data)

        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "").strip()
            print(f"Сообщение от {chat_id}: {text}")

            if text == "/start":
                send_message(chat_id, "Добро пожаловать! Напишите мне что-нибудь, и я помогу создать пост для Telegram.")
            elif text == "/help":
                send_message(chat_id, "Список команд:\n/start - начать работу\n/help - помощь\nНапишите сообщение, чтобы я его обработал.")
            else:
                response = get_chatgpt_response(text)
                send_message(chat_id, response)

        return "OK", 200

    except Exception as e:
        print("Ошибка в обработке запроса:", traceback.format_exc())
        return "Internal Server Error", 500


def send_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload)
        print("Ответ Telegram:", response.json())
    except Exception as e:
        print("Ошибка отправки сообщения:", e)


def get_chatgpt_response(prompt):
    try:
        assistant_instructions = (
            "Ты — профессиональный создатель контента для Телеграм-канала Ассоциации застройщиков. "
            "Создавай структурированные, продающие посты с использованием эмодзи на темы недвижимости, строительства, "
            "законодательства и инвестиций. В конце каждого поста добавляй: \"Звоните \ud83d\udcf2 8-800-550-23-93 или переходите по ссылке: [Ассоциация застройщиков](https://t.me/associationdevelopers).\""
        )

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Используйте актуальную модель
            messages=[
                {"role": "system", "content": assistant_instructions},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1500,
            temperature=1.0,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("Ошибка вызова OpenAI API:", traceback.format_exc())
        return "Извините, произошла ошибка при обработке вашего запроса."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Порт по умолчанию
    app.run(host="0.0.0.0", port=port)
