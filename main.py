from flask import Flask, request
import requests
import os
import openai
import yclients
from yclients import YClientsAPI

app = Flask(__name__)

# 📦 Переменные окружения (устанавливаются в Railway)
GREEN_API_ID = os.getenv("GREEN_API_ID")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
OPENAI_API_TOKEN = os.getenv("OPENAI_API_TOKEN")

YCLIENTS_API_TOKEN = os.getenv("YCLIENTS_API_TOKEN")
YCLIENTS_COMPANY_ID = ""
YCLIENTS_FORM_ID = ""

openai.api_key = OPENAI_API_TOKEN

api = YClientsAPI(token=YCLIENTS_API_TOKEN, company_id=YCLIENTS_COMPANY_ID, form_id=YCLIENTS_FORM_ID, debug=TRUE)


def get_booking_dates(staff_id, service_id):
     booking_days = api.get_available_days(staff_id=staff_id, service_id=service_id)
     print(booking_days)
     day = booking_days['data'].get('booking_dates')
     return day


def get_booking_times(staff_id, service_id, day):
     time_slots = api.get_available_times(staff_id=staff_id, service_id=service_id, day=day)
     print(time_slots)
     date_time = time_slots['data'].get('time')
     return date_time


def book(name, phone, email, service_id, date_time, staff_id, comment):
     booked, message = api.book(booking_id=0, 
     fullname=name, 
     phone=phone, 
     email=email, 
     service_id=service_id, 
     date_time=date_time, 
     staff_id=staff_id, 
     comment=comment)
     return "Booked"

def get_staff_info():
     all_staff = api.get_staff()
     print(all_staff)
     staff_id = all_staff['data'].get('id')
     return staff_id


def get_services_info(staff_id):
     services = api.get_services(staff_id=staff_id)
     print(services)
     service_id = services['data']['services'].get('id')
     return service_id


def find_book_request_in_message(user_message):
     try:
        prompt = str("Если в данном сообщении есть желаение записаться на какую-то услугу, напиши, какую услугу хочет клиент, от какого мастера, когда и во сколько, в формате строки \" Услуга; Мастер; Дата; Время \", а если в данном сообщении отсутствуют какие то из этих параметров, то вставляй \"NA\" в строку на месте отсутствуюзего параметра" + user_message)
        response = openai.responses.create(
            model="gpt-4o",
            input=prompt    
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

