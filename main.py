from flask import Flask, request
import requests
import os

app = Flask(__name__)

# 📦 Переменные окружения (устанавливаются в Railway)
GREEN_API_ID = os.getenv("GREEN_API_ID")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")

# 📤 Отправка сообщения
def send_message(phone, text):
    url = f"https://api.green-api.com/waInstance{GREEN_API_ID}/sendMessage/{GREEN_API_TOKEN}"
    payload = {
        "chatId": f"{phone}@c.us",
        "message": text
    }
    response = requests.post(url, json=payload)
    print(f"Ответ от Green API: {response.status_code} - {response.text}")

# 📥 Обработка входящих сообщений
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        print("\n🟡 Webhook сработал!")
        print("🔍 JSON:", data)

        message = data['messageData']['textMessageData']['textMessage']
        phone = data['senderData']['chatId'].replace("@c.us", "")

        # 🤖 Простейшая логика ответа
        if "привет" in message.lower():
            send_message(phone, "Здравствуйте! Чем могу помочь?")
        elif "записаться" in message.lower():
            send_message(phone, "Укажите услугу и удобное время, пожалуйста.")
        else:
            send_message(phone, "Извините, я вас не понял. Напишите 'записаться' или 'привет'.")
    except Exception as e:
        print("❌ Ошибка в webhook:", e)
    return "OK", 200

# 🔍 Проверка работы сервера
@app.route("/", methods=["GET"])
def home():
    return "Бот работает на Railway!", 200

# 🚀 Запуск приложения
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

