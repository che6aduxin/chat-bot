from flask import Flask, request
import requests
import os
import openai

app = Flask(__name__)

# 📦 Переменные окружения (устанавливаются в Railway)
GREEN_API_ID = os.getenv("GREEN_API_ID")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
OPENAI_API_TOKEN = os.getenv("OPENAI_API_TOKEN")

openai.api_key = OPENAI_API_TOKEN

def find_book_request_in_message(user_message):
     try:
        prompt = "Если в данном сообщении есть желаение записаться на какую-то услугу, напиши, какую услугу хочет клиент, от какого мастера, когда и во сколько, в формате строки \" Услуга; Мастер; Дата; Время \", а если в данном сообщении отсутствуют какие то из этих параметров, то вставляй \"NA\" в строку на месте отсутствуюзего параметра" + user_message
        response = openai.responses.create(
            model="gpt-4o",
            input=[
                {prompt}
            ]    
        )
        return response.output_text
    except Exception as e:
        print("❌ Ошибка при запросе к ChatGPT:", e)
        return "error"

# 📤 Отправка сообщения
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
        response = openai.responses.create(
            model="gpt-4o",
            input=[
                {"role": "system", "content": "Ты вежливый и дружелюбный администратор салона красоты. Помогаешь записаться, уточняешь детали, отвечаешь естественно."},
                {"role": "user", "content": user_message}
            ]
        )
#        return response.choices[0].message["content"].strip()
        return response.output_text
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
        
        if data.get("typeWebhook") != "incomingMessageReceived":
            print("🔃 Это не входящее сообщение, пропускаем.")
            return "Ignored", 200
        
        message = data['messageData']['textMessageData']['textMessage']
        phone = data['senderData']['chatId'].replace("@c.us", "")

        print(find_book_request_in_message(message))

        reply = ask_chatgpt(message)
        send_message(phone, reply)

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

