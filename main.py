from flask import Flask, request
import requests
import os
import openai

app = Flask(__name__)

# 📦 Переменные окружения
GREEN_API_ID = os.getenv("GREEN_API_ID")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

# 📤 Отправка сообщения через Green API
def send_message(phone, text):
    url = f"https://api.green-api.com/waInstance{GREEN_API_ID}/sendMessage/{GREEN_API_TOKEN}"
    payload = {
        "chatId": f"{phone}@c.us",
        "message": text
    }
    response = requests.post(url, json=payload)
    print(f"Ответ от Green API: {response.status_code} - {response.text}")

# 🤖 Получение ответа от ChatGPT
def ask_chatgpt(user_message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Ты вежливый и дружелюбный администратор салона красоты. Помогаешь записаться, уточняешь детали, отвечаешь естественно."},
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        print("❌ Ошибка при запросе к ChatGPT:", e)
        return "Извините, в Москве большие проблемы со связью, смогу вас проконсультировать чуть позже. Не могу открыть наше расписание"

# 📥 Обработка входящих сообщений
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        print("\n🟡 Webhook сработал!")
        print("🔍 JSON:", data)

        message = data['messageData']['textMessageData']['textMessage']
        phone = data['senderData']['chatId'].replace("@c.us", "")

        # Получаем ответ от ChatGPT
        reply = ask_chatgpt(message)
        send_message(phone, reply)

    except Exception as e:
        print("❌ Ошибка в webhook:", e)

    return "OK", 200

# 🔍 Проверка работы сервера
@app.route("/", methods=["GET"])
def home():
    return "Бот с ChatGPT работает на Railway!", 200

# 🚀 Запуск приложения
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

