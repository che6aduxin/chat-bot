import os
import yclients
import httpx
import ujson
from yclients import YClientsAPI

YCLIENTS_API_TOKEN = os.getenv("YCLIENTS_API_TOKEN")
YCLIENTS_COMPANY_ID = os.getenv("YCLIENTS_COMPANY_ID")
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

def book(name, phone, service_id, date_time, staff_id, comment):
    api.book(booking_id=0,
             fullname=name,
             phone=phone,
             email="noemail@noemail.com",
             service_id=service_id,
             date_time=date_time,
             staff_id=staff_id,
             comment=comment)
    print('booked')

# --- Flask + OpenAI function calling ---

# --- Flask + OpenAI function calling ---

import requests
import openai
from flask import Flask, request
import json

# --- Google Apps Script API для работы с памятью и промтами ---
GAS_API_URL = "https://script.google.com/macros/s/AKfycbxL2dDQWi88cURqq_OFJYLd56JKEuZjLJW41aYqguzedchA1jprv8zpm6Tvk-8eyZdI/exec"

def get_system_prompt():
    resp = requests.get(GAS_API_URL, params={"type": "prompt"})
    resp.raise_for_status()
    return resp.json()

def get_knowledge_base():
    resp = requests.get(GAS_API_URL, params={"type": "knowledge"})
    resp.raise_for_status()
    return resp.json()

def get_memory(user_id):
    resp = requests.get(GAS_API_URL, params={"type": "memory", "userId": str(user_id)})
    resp.raise_for_status()
    return resp.json()

def add_memory(user_id, role, content):
    payload = {
        "action": "add",
        "userId": str(user_id),
        "role": role,
        "content": content
    }
    resp = requests.post(GAS_API_URL, json=payload)
    resp.raise_for_status()
    return resp.json()

def update_memory(user_id, memory_array):
    payload = {
        "action": "update",
        "userId": str(user_id),
        "memoryArray": memory_array
    }
    resp = requests.post(GAS_API_URL, json=payload)
    resp.raise_for_status()
    return resp.json()

def generate_gpt_response(history, user_message, system_prompt):
    gpt_messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        gpt_messages.append({"role": msg["role"], "content": msg["content"]})
    gpt_messages.append({"role": "user", "content": user_message})
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=gpt_messages,
        tools=tools,
        tool_choice="none",
        temperature=0.1
    )
    return response.choices[0].message.content

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

tools = [
    {
        "type": "function",
        "function": {
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
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_staff_list",
            "description": (
                "Возвращает словарь со всем персоналом, где ключами являются имена сотрудников, а значаниями являются их id"
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_staff_list_inv",
            "description": (
                "Возвращает словарь со всем персоналом, где ключами являются id сотрудников, а значаниями являются их имена"
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_services_list",
            "description": (
                "Возвращает словарь со всеми услугами, где ключами являются названия услуг, а значаниями являются их id"
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_services_list_inv",
            "description": (
                "Возвращает словарь со всеми услугами, где ключами являются id услуг, а значаниями являются их названия"
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_services_title_list_for_staff",
            "description": (
                "Возвращает список услуг, которые выполняет конкретный работник по id этого работника"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "staff_id": {"type": "string", "description": "id работника, для которого ищется список улуг"}
                },
                "required": ["staff_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_service_info",
            "description": (
                "Возвращает описание услуги по ее id в виде списка, где первым элементом является название услуги, вторым является цена услуги в рублях, а третьим является длительность услуги в минутах"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id": {"type": "string", "description": "id услуги для которой нужно найти название, цену или длительность"}
                },
                "required": ["service_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_available_dates_for_staff_service",
            "description": (
                "Возвращет список дат на которые доступна запись для заданного работника и услуги в формате ГГГГ-ММ-ДД "
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "staff_id": {"type": "string", "description": "id работника"},
                    "service_id": {"type": "string", "description": "id услуги"}
                },
                "required": ["staff_id", "service_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_available_dates_for_service",
            "description": (
                "Возвращет список дат на которые доступна запись для заданной услуги (без указания конкретного работника) в формате ГГГГ-ММ-ДД "
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id": {"type": "string", "description": "id услуги"}
                },
                "required": ["service_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_staff_for_date_service",
            "description": (
                "Возвращает список с id перслонала, доступного в заданную дату и на заданную услугу"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id": {"type": "string", "description": "id услуги"},
                    "date": {"type": "string", "description": "дата в формате ГГГГ-ММ-ДД"}
                },
                "required": ["service_id", "date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_staff_for_date_time_service",
            "description": (
                "Возвращает список с id перслонала, доступного в заданную дату, на заданное время, и на заданную услугу"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id": {"type": "string", "description": "id услуги"},
                    "date": {"type": "string", "description": "дата в формате ГГГГ-ММ-ДД"},
                    "time": {"type": "string", "description": "время в формате ЧЧ:ММ"}
                },
                "required": ["service_id", "date", "time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_available_times_for_staff_service",
            "description": (
                "Возвращает список доступных времен для записи на заданную услугу к заданному работнику"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "staff_id": {"type": "string", "description": "id работника"},
                    "service_id": {"type": "string", "description": "id услуги"},
                    "date": {"type": "string", "description": "дата в формате ГГГГ-ММ-ДД"}
                },
                "required": ["staff_id", "service_id", "date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_available_times_for_service",
            "description": (
                "Возвращает список доступных времен для записи на заданную услугу (без указания конкретного работника)"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id": {"type": "string", "description": "id услуги"},
                    "date": {"type": "string", "description": "дата в формате ГГГГ-ММ-ДД"}
                },
                "required": ["service_id", "date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book",
            "description": (
                "выполняет запись клиента на заданное время, в заданную дату, на заданную услугу и к заданному работнику"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "имя клиента"},
                    "phone": {"type": "string", "description": "номер телефона клиента"},
                    "service_id": {"type": "string", "description": "id услуги"},
                    "date_time": {"type": "string", "description": "дата и время в формате ГГГГ-ММ-ДД'T'ЧЧ:ММ:СС'+3:00'"},
                    "staff_id": {"type": "string", "description": "id работника"},
                    "comment": {"type": "string", "description": "комментарий к записи от клиента, если не указан клиентом, то возвращать в виде аргумента функции 'Запись через Whatsapp'"}
                },
                "required": ["name", "phone", "service_id", "date_time", "staff_id", "comment"]
            }
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

        # --- Долговременная память (GAS) ---
        history = get_memory(phone)
        add_memory(phone, "user", message)


        # --- SYSTEM PROMPT ---
                # --- Системный промт и история из GAS ---
        system_prompt = get_system_prompt()
        gpt_messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            gpt_messages.append({"role": msg["role"], "content": msg["content"]})
        gpt_messages.append({"role": "user", "content": message})

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=gpt_messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.1
        )


        choice = response.choices[0].message
        print("\n--- ОТВЕТ OPENAI ---\n", choice, "\n----------------------\n")

        # Если GPT вызвал функцию бронирования
        if getattr(choice, "function_call", None):
            fn_name = choice.function_call.name
            args = json.loads(choice.function_call.arguments)
            print("Function call:", fn_name, "| Args:", args)

            # 1. Бронирование услуги (book_service)
            if fn_name == "book_service":
                all_services = get_all_services_list()
                all_staff = get_all_staff_list()
                service_id = all_services.get(args['service'])
                staff_id = all_staff.get(args['master'])
                date = args['date']
                time = args['time']
                date_time = f"{date} {time}"

                if not service_id:
                    err_msg = f"❗️Услуга '{args['service']}' не найдена. Доступные: {', '.join(all_services.keys())}"
                    send_message(phone, err_msg)
                    add_memory(phone, "assistant", err_msg)
                    return "OK", 200
                if not staff_id:
                    err_msg = f"❗️Мастер '{args['master']}' не найден. Доступные: {', '.join(all_staff.keys())}"
                    send_message(phone, err_msg)
                    add_memory(phone, "assistant", err_msg)
                    return "OK", 200

                try:
                    book(
                        name=args['master'],
                        phone=phone,
                        service_id=service_id,
                        date_time=date_time,
                        staff_id=staff_id,
                        comment="Запись через WhatsApp"
                    )
                    ok_msg = f"✅ Вы успешно записаны на {args['service']} к мастеру {args['master']} {date} в {time}! Ждём вас в салоне."
                    send_message(phone, ok_msg)
                    add_memory(phone, "assistant", ok_msg)
                except Exception as e:
                    err_msg = f"Ошибка при записи: {e}"
                    send_message(phone, err_msg)
                    add_memory(phone, "assistant", err_msg)
                return "OK", 200

            # 2. get_all_staff_list
            if fn_name == "get_all_staff_list":
                staff = get_all_staff_list()
                msg = "Доступные мастера:\n" + "\n".join(list(staff.keys()))
                send_message(phone, msg)
                add_memory(phone, "assistant", msg)
                return "OK", 200

            # 3. get_all_staff_list_inv
            if fn_name == "get_all_staff_list_inv":
                staff_inv = get_all_staff_list_inv(get_all_staff_list())
                msg = "ID -> Мастер:\n" + "\n".join([f"{k}: {v}" for k, v in staff_inv.items()])
                send_message(phone, msg)
                add_memory(phone, "assistant", msg)
                return "OK", 200

            # 4. get_all_services_list
            if fn_name == "get_all_services_list":
                services = get_all_services_list()
                msg = "Доступные услуги:\n" + "\n".join(list(services.keys()))
                send_message(phone, msg)
                add_memory(phone, "assistant", msg)
                return "OK", 200

            # 5. get_all_services_list_inv
            if fn_name == "get_all_services_list_inv":
                services_inv = get_all_services_list_inv(get_all_services_list())
                msg = "ID -> Услуга:\n" + "\n".join([f"{k}: {v}" for k, v in services_inv.items()])
                send_message(phone, msg)
                add_memory(phone, "assistant", msg)
                return "OK", 200

            # 6. get_services_title_list_for_staff
            if fn_name == "get_services_title_list_for_staff":
                staff_id = args.get("staff_id")
                services = get_services_title_list_for_staff(staff_id)
                msg = f"Мастер {staff_id} выполняет услуги:\n" + ", ".join(services)
                send_message(phone, msg)
                add_memory(phone, "assistant", msg)
                return "OK", 200

            # 7. get_service_info
            if fn_name == "get_service_info":
                service_id = args.get("service_id")
                info = get_service_info(service_id)
                msg = f"Услуга: {info[0]}\nЦена: {info[1]} руб.\nДлительность: {info[2]} мин."
                send_message(phone, msg)
                add_memory(phone, "assistant", msg)
                return "OK", 200

            # 8. get_available_dates_for_staff_service
            if fn_name == "get_available_dates_for_staff_service":
                staff_id = args.get("staff_id")
                service_id = args.get("service_id")
                dates = get_available_dates_for_staff_service(staff_id, service_id)
                if dates:
                    msg = "Свободные даты для мастера: " + ", ".join(dates)
                else:
                    msg = "Нет доступных дат для этого мастера."
                send_message(phone, msg)
                add_memory(phone, "assistant", msg)
                return "OK", 200

            # 9. get_available_dates_for_service
            if fn_name == "get_available_dates_for_service":
                service_id = args.get("service_id")
                dates = get_available_dates_for_service(service_id)
                if dates:
                    msg = "Свободные даты: " + ", ".join(dates)
                else:
                    msg = "Нет доступных дат для этой услуги."
                send_message(phone, msg)
                add_memory(phone, "assistant", msg)
                return "OK", 200

            # 10. get_staff_for_date_service
            if fn_name == "get_staff_for_date_service":
                service_id = args.get("service_id")
                date = args.get("date")
                staff_ids = get_staff_for_date_service(service_id, date)
                msg = f"Доступные мастера на {date}: " + ", ".join(staff_ids)
                send_message(phone, msg)
                add_memory(phone, "assistant", msg)
                return "OK", 200

            # 11. get_staff_for_date_time_service
            if fn_name == "get_staff_for_date_time_service":
                service_id = args.get("service_id")
                date = args.get("date")
                time = args.get("time")
                staff_ids = get_staff_for_date_time_service(service_id, date, time)
                msg = f"Доступные мастера на {date} в {time}: " + ", ".join(staff_ids)
                send_message(phone, msg)
                add_memory(phone, "assistant", msg)
                return "OK", 200

            # 12. get_available_times_for_staff_service
            if fn_name == "get_available_times_for_staff_service":
                staff_id = args.get("staff_id")
                service_id = args.get("service_id")
                date = args.get("date")
                times = get_available_times_for_staff_service(staff_id, service_id, date)
                if times:
                    msg = f"Доступное время у мастера {staff_id} на {date}: " + ", ".join(times)
                else:
                    msg = f"Нет свободного времени у мастера {staff_id} на {date}."
                send_message(phone, msg)
                add_memory(phone, "assistant", msg)
                return "OK", 200

            # 13. get_available_times_for_service
            if fn_name == "get_available_times_for_service":
                service_id = args.get("service_id")
                date = args.get("date")
                times = get_available_times_for_service(service_id, date)
                if times:
                    msg = f"Свободное время на {date}: " + ", ".join(times)
                else:
                    msg = f"Нет свободного времени на {date}."
                send_message(phone, msg)
                add_memory(phone, "assistant", msg)
                return "OK", 200

            # 14. book
            if fn_name == "book":
                name = args.get("name")
                phone_arg = args.get("phone", phone)
                service_id = args.get("service_id")
                date_time = args.get("date_time")
                staff_id = args.get("staff_id")
                comment = args.get("comment", "Запись через WhatsApp")
                book(name, phone_arg, service_id, date_time, staff_id, comment)
                msg = f"✅ Вы успешно записаны на услугу {service_id} к мастеру {staff_id} на {date_time}!"
                send_message(phone, msg)
                add_memory(phone, "assistant", msg)
                return "OK", 200

            # 15. get_knowledge_base
            if fn_name == "get_knowledge_base":
                kb = get_knowledge_base()
                kb_text = "\n".join([f"{item['term']}: {item['explanation']}" for item in kb])
                send_message(phone, kb_text)
                add_memory(phone, "assistant", kb_text)
                return "OK", 200

            # Если не попало никуда
            send_message(phone, "Функция не реализована или параметры не распознаны.")
            add_memory(phone, "assistant", "Функция не реализована или параметры не распознаны.")
            return "OK", 200

        else:
            print("⚠️ GPT не вызвал функцию — fallback в чистый диалог.")
             # fallback на генерацию человеческого ответа, даже если функция не вызвана
            fallback_response = generate_gpt_response(history, message, system_prompt)
            send_message(phone, fallback_response)
            add_memory(phone, "assistant", fallback_response)
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
