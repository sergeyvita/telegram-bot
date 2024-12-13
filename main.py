from flask import Flask, request, jsonify
from pyngrok import ngrok
import requests
import openai
import os
import traceback

# Настройки Telegram Bot и OpenAI
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Телеграм токен
openai.api_key = os.getenv("OPENAI_API_KEY")  # OpenAI токен
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Flask приложение
app = Flask(__name__)

@app.route('/')
def home():
    return "Сервер работаета через ngrok!", 200

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        return "Webhook is set", 200

    try:
        data = request.json
        print(f"Получены данные: {data}")

        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "").strip()

            if text == "/start":
                send_message(chat_id, "Добро пожаловать! Бот работает через ngrok.")
            elif text == "/help":
                send_message(chat_id, "Список команд:\n/start - начать работу\n/help - помощь.")
            else:
                response = get_chatgpt_response(text)
                send_message(chat_id, response)

        return "OK", 200

    except Exception as e:
        print("Ошибка обработки запроса:", traceback.format_exc())
        return jsonify({"error": "Internal Server Error"}), 500


def send_message(chat_id, text):
    try:
        response = requests.post(
            f"{TELEGRAM_API_URL}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
        )
        print(f"Ответ Telegram: {response.json()}")
    except Exception as e:
        print("Ошибка отправки сообщения:", traceback.format_exc())


def get_chatgpt_response(prompt):
    try:
        messages = [
            {"role": "system", "content": "Ты - профессиональный создатель контента для Telegram."},
            {"role": "user", "content": prompt},
        ]
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            max_tokens=1000,
            temperature=1,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("Ошибка вызова OpenAI:", traceback.format_exc())
        return "Произошла ошибка при обработке запроса."


if __name__ == "__main__":
    # Запуск ngrok
    ngrok_token = os.getenv("NGROK_AUTH_TOKEN", "your_ngrok_auth_token")
    if ngrok_token:
        ngrok.set_auth_token(ngrok_token)
    public_url = ngrok.connect(8080)
    print(f"ngrok URL: {public_url}")

    # Установить Webhook
    webhook_url = f"{public_url}/webhook"
    response = requests.post(f"{TELEGRAM_API_URL}/setWebhook", json={"url": webhook_url})
    print(f"Webhook Telegram установлен: {response.json()}")

    # Запуск Flask
    app.run(host="0.0.0.0", port=8080) 

