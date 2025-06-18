from flask import Flask, request
import requests
import os
import openai
from yclients import YClientsAPI

app = Flask(__name__)

# --- Переменные окружения ---
GREEN_API_ID = os.getenv("GREEN_API_ID")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
OPENAI_API_TOKEN = os.getenv("OPENAI_API_TOKEN")
YCLIENTS_API_TOKEN = os.getenv("YCLIENTS_API_TOKEN")
YCLIENTS_COMPANY_ID = os.getenv("YCLIENTS_COMPANY_ID")
YCLIENTS_FORM_ID = os.getenv("YCLIENTS_FORM_ID")

openai.api_key = OPENAI_API_TOKEN

yclients_api = YClientsAPI(token=YCLIENTS_API_TOKEN, company_id=YCLIENTS_COMPANY_ID, form_id=YCLIENTS_FORM_ID)

# --- Получить все услуги и мастеров заранее (можно кэшировать) ---
def get_all_staff():
    staff_list = {}
    staff_data = yclients_api.get_staff()
    for s in staff_data['data']:
        staff_list[s['name'].lower()] = s['id']
    return staff_list

def get_all_services():
    service_list = {}
    services_data = yclients_api.get_services()
    for s in services_data['data']['services']:
        service_list[s['title'].lower()] = s['id']
    return service_list

# --- Извлечь параметры записи из сообщения с помощью GPT ---
def parse_booking_request(user_message):
    prompt = (
        "Выдели из сообщения параметры записи в формате: "
        "'Услуга; Мастер; Дата (гггг-мм-дд); Время (чч:мм)'. "
        "Если параметра нет, напиши 'NA'. Пример: 'Маникюр; Мария; 2024-06-25; 15:00'.\n"
        f"Сообщение: {user_message}"
    )
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}]
    )
    parsed = response.choices[0].message.content.strip()
    return [s.strip() for s in parsed.split(';')]

# --- Записать клиента через YCLIENTS ---
def book_client(name, phone, service_id, date, time, staff_id, comment=""):
    date_time = f"{date} {time}"
    result = yclients_api.book(
        booking_id=0,
        fullname=name,
        phone=phone,
        email="",
        service_id=service_id,
        date_time=date_time,
        staff_id=staff_id,
        comment=comment
    )
    return result

# --- Отправить сообщение клиенту ---
def send_message(phone, text):
    url = f"https://api.green-api.com/waInstance{GREEN_API_ID}/sendMessage/{GREEN_API_TOKEN}"
    payload = {
        "chatId": f"{phone}@c.us",
        "message": text
    }
    requests.post(url, json=payload)

# --- Основной webhook ---
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if data.get("typeWebhook") != "incomingMessageReceived":
        return "Ignored", 200
    message = data['messageData']['textMessageData']['textMessage']
    phone = data['senderData']['chatId'].replace("@c.us", "")

    # --- Парсим intent с помощью GPT ---
    service, staff, date, time = parse_booking_request(message)
    print(f"GPT params: {service}, {staff}, {date}, {time}")

    all_services = get_all_services()
    all_staff = get_all_staff()
    errors = []

    # --- Проверяем и уточняем параметры ---
    if service.lower() not in all_services:
        errors.append("услугу")
    if staff.lower() not in all_staff:
        errors.append("мастера")
    if date == "NA" or time == "NA":
        errors.append("дату/время")

    if errors:
        send_message(phone, f"Пожалуйста, уточните: {'; '.join(errors)}")
        return "OK", 200

    # --- Если всё есть, делаем запись ---
    service_id = all_services[service.lower()]
    staff_id = all_staff[staff.lower()]
    result = book_client(
        name="Клиент WhatsApp",  # Можно доработать!
        phone=phone,
        service_id=service_id,
        date=date,
        time=time,
        staff_id=staff_id
    )
    send_message(phone, f"Вы успешно записаны на {service} к мастеру {staff} {date} в {time}!")

    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "Бот работает!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
