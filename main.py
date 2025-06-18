# --- Функции работы с YClients --- (ТВОЙ КОД, ничего не менял)
import os
import yclients
import httpx
import ujson
from yclients import YClientsAPI

YCLIENTS_API_TOKEN = "m49f9dcb59tdy278d53n"
YCLIENTS_COMPANY_ID = "1342302"
YCLIENTS_FORM_ID = "1"
api = YClientsAPI(token=YCLIENTS_API_TOKEN, company_id=YCLIENTS_COMPANY_ID, form_id=YCLIENTS_FORM_ID)

def get_all_staff_list():
    all_staff = api.get_staff()
    print(all_staff)
    all_staff_list = {}
    for elem in all_staff['data']:
        staff_name = elem.get('name')
        staff_id = elem.get('id')
        all_staff_list.update({staff_name: staff_id})
        print(staff_name, staff_id)
    return all_staff_list

def get_all_staff_list_inv(all_staff_list):
    all_staff_list_inv = {value: key for key, value in all_staff_list}
    return all_staff_list_inv

def get_all_services_list():
    services = api.get_services()
    print(services)
    all_services_list = {}
    services_data = services['data']
    for elem in services_data['services']:
        service_title = elem.get('title')
        service_id = elem.get('id')
        all_services_list.update({service_title: service_id})
        print(service_title, service_id)
    return all_services_list

def get_all_services_list_inv(all_services_list):
    all_services_list_inv = {value: key for key, value in all_services_list}
    return all_services_list_inv

def get_services_title_list_for_staff(staff_id):
    services = api.get_services(staff_id=staff_id)
    print(services)
    services = services['data'].get('services')
    services_title_list_for_staff = []
    for elem in services:
        services_title_list_for_staff.append(elem.get('title'))
    print(services_title_list_for_staff)
    return services_title_list_for_staff

def get_service_info(service_id):
    info = api.get_service_info(service_id)
    service_info = []
    title = info['data'].get('title')
    service_info.append(title)
    price = info['data'].get('price_min')
    service_info.append(price)
    duration = int(info['data'].get('duration'))/60
    service_info.append(duration)
    return service_info

def get_available_dates_for_staff_service(staff_id, service_id):
    available_dates = api.get_available_days(staff_id=staff_id, service_id=service_id)
    print(available_dates)
    available_dates = available_dates['data'].get('booking_dates')
    print(available_dates)
    return available_dates

def get_available_dates_for_service(service_id):
    available_dates = api.get_available_days(service_id=service_id)
    print(available_dates)
    available_dates = available_dates['data'].get('booking_dates')
    print(available_dates)
    return available_dates

def get_staff_for_date_service(service_id, date):
    all_staff_id_list_inv = get_all_staff_list_inv(get_all_staff_list())
    staff_id_list = []
    for key in all_staff_id_list_inv:
        available_for_staff = get_available_dates_for_staff_service(key, service_id)
        available_for_staff = available_for_staff['data'].get('booking_dates')
        if date in available_for_staff:
            staff_id_list.append(key)
    return staff_id_list

def get_staff_for_date_time_service(service_id, date, time):
    all_staff_id_list_inv = get_all_staff_list_inv(get_all_staff_list())
    staff_id_list = []
    for key in all_staff_id_list_inv:
        available_time_for_staff = get_available_times_for_staff_service(key, service_id, date)
        if time in available_time_for_staff:
            staff_id_list.append(key)
    return staff_id_list

def get_available_times_for_staff_service(staff_id, service_id, date):
    time_slots = api.get_available_times(staff_id=staff_id, service_id=service_id, day=date)
    print(time_slots)
    available_time = [time_slots['data'].get('time') for elem in time_slots['data']]
    return available_time

def get_available_times_for_service(service_id, date):
    staff = get_staff_for_date_service(service_id, date)
    available_times = []
    for elem in staff:
        time_slots = api.get_available_times(staff_id=elem, service_id=service_id, day=date)
        times = [time_slots['data'].get('time') for elem in time_slots['data']]
        for _ in times:
            if _ not in available_times:
                available_times.append(_)
    return available_times

def book(name, phone, email, service_id, date_time, staff_id, comment):
    api.book(booking_id=0,
             fullname=name,
             phone=phone,
             email=email,
             service_id=service_id,
             date_time=date_time,
             staff_id=staff_id,
             comment=comment)
    print('booked')

# --- Flask + OpenAI function calling ---

import requests
import openai
from flask import Flask, request
import json

# Если используешь переменные окружения для ключей, можешь так:
# GREEN_API_ID = os.getenv("GREEN_API_ID")
# GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
# OPENAI_API_TOKEN = os.getenv("OPENAI_API_TOKEN")
# client = openai.OpenAI(api_key=OPENAI_API_TOKEN)

# Для теста — впиши ключ вручную или используй окружение:
GREEN_API_ID = os.getenv("GREEN_API_ID")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
OPENAI_API_TOKEN = os.getenv("OPENAI_API_TOKEN") # <-- замени на свой

client = openai.OpenAI(api_key=OPENAI_API_TOKEN)
app = Flask(__name__)

functions = [
    {
        "name": "book_service",
        "description": (
            "Бронирование услуги в салоне красоты. "
            "Если сообщение пользователя содержит услугу, мастера, дату (ДД.ММ.ГГГГ) и время (ЧЧ:ММ), ВСЕГДА вызывай функцию. "
            "Если чего-то не хватает — спроси только это. Не отвечай текстом, если все параметры есть."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "service": {"type": "string", "description": "Название услуги, например 'Массаж лица'"},
                "master": {"type": "string", "description": "Имя мастера, например 'Андрей'"},
                "date": {"type": "string", "description": "Дата в формате ДД.ММ.ГГГГ"},
                "time": {"type": "string", "description": "Время в формате ЧЧ:ММ"}
            },
            "required": ["service", "master", "date", "time"]
        }
    }
]

def send_message(phone, text):
    url = f"https://api.green-api.com/waInstance{GREEN_API_ID}/sendMessage/{GREEN_API_TOKEN}"
    payload = {
        "chatId": f"{phone}@c.us",
        "message": text
    }
    response = requests.post(url, json=payload)
    print(f"Green API ответ: {response.status_code} - {response.text}")

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        print("Webhook:", data)

        if data.get("typeWebhook") != "incomingMessageReceived":
            return "Ignored", 200

        messageData = data['messageData']
        typeMessage = messageData.get('typeMessage')

        if typeMessage == "textMessage":
            message = messageData['textMessageData']['textMessage']
        elif typeMessage == "extendedTextMessage":
            message = messageData['extendedTextMessageData']['text']
        else:
            message = ""
            print("Неизвестный тип сообщения!")

        phone = data['senderData']['chatId'].replace("@c.us", "")

        print(f"Входящее сообщение: '{message}' от {phone}")

        # --- SYSTEM PROMPT ---
        system_prompt = (
            "Ты виртуальный ассистент салона красоты. "
            "Если пользователь написал услугу, мастера, дату (ДД.ММ.ГГГГ), время (ЧЧ:ММ) — "
            "ВСЕГДА вызывай функцию book_service и не отвечай текстом! "
            "Если чего-то не хватает, вежливо спроси только недостающие детали."
        )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            functions=functions,
            function_call="auto",
            temperature=0.1
        )

        choice = response.choices[0].message
        print("\n--- ОТВЕТ OPENAI ---\n", choice, "\n----------------------\n")

        # Если GPT вызвал функцию бронирования
        if getattr(choice, "function_call", None):
            args = json.loads(choice.function_call.arguments)
            print("Function call args:", args)

            # Используем твои готовые функции для поиска id услуги и мастера
            all_services = get_all_services_list()
            all_staff = get_all_staff_list()
            print("all_services:", all_services)
            print("all_staff:", all_staff)

            service_id = all_services.get(args['service'])
            staff_id = all_staff.get(args['master'])
            date = args['date']
            time = args['time']
            date_time = f"{date} {time}"

            if not service_id:
                err_msg = f"❗️Услуга '{args['service']}' не найдена. Доступные: {', '.join(all_services.keys())}"
                print(err_msg)
                send_message(phone, err_msg)
                return "OK", 200
            if not staff_id:
                err_msg = f"❗️Мастер '{args['master']}' не найден. Доступные: {', '.join(all_staff.keys())}"
                print(err_msg)
                send_message(phone, err_msg)
                return "OK", 200

            try:
                book(
                    name=args['master'],
                    phone=phone,
                    email="noemail@email.com",
                    service_id=service_id,
                    date_time=date_time,
                    staff_id=staff_id,
                    comment="Запись через WhatsApp"
                )
                ok_msg = f"✅ Вы успешно записаны на {args['service']} к мастеру {args['master']} {date} в {time}! Ждём вас в салоне."
                print(ok_msg)
                send_message(phone, ok_msg)
            except Exception as e:
                print("Ошибка при бронировании:", e)
                send_message(phone, f"Ошибка при записи: {e}")

            return "OK", 200

        else:
            print("⚠️ GPT не вызвал функцию бронирования! Полный ответ:", choice)
            if choice.content:
                send_message(phone, "Пожалуйста, укажите услугу, мастера, дату и время в формате: Услуга, Мастер, ДД.ММ.ГГГГ, ЧЧ:ММ.\nGPT ответ: " + choice.content)
            else:
                send_message(phone, "Бот не смог распознать все параметры. Проверьте формат сообщения.")
            return "OK", 200

    except Exception as e:
        print("Ошибка в webhook:", e)
        send_message(phone, "Произошла ошибка на сервере, попробуйте позже.")
    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "Бот работает!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
