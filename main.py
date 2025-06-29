import os
import yclients
import httpx
import ujson
import datetime
from yclients import YClientsAPI

YCLIENTS_API_TOKEN = os.getenv("YCLIENTS_API_TOKEN")
YCLIENTS_COMPANY_ID = os.getenv("YCLIENTS_COMPANY_ID")
YCLIENTS_FORM_ID = os.getenv("YCLIENTS_APPLICATION_ID")
api = YClientsAPI(token=YCLIENTS_API_TOKEN, company_id=YCLIENTS_COMPANY_ID, form_id=YCLIENTS_FORM_ID)

def get_service_categories():
    url = "https://yclients.com/api/v1/company/606554/service_categories?include=services_count"
    headers = {
        'Content-Type': 'application/json',
        'User-Token': os.getenv("YCLIENTS_API_TOKEN"),  # или Authorization...
        'Company-Id': '606554',
    }
    resp = requests.get(url, headers=headers)
    print("Категории:", resp.json())
    return resp.json()


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
def get_next_weekday(target_weekday):
    # target_weekday: 0=Monday ... 6=Sunday
    today = datetime.date.today()
    days_ahead = target_weekday - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return (today + datetime.timedelta(days=days_ahead)).strftime("%Y-%m-%d")

def normalize_date(date_str):
    # ISO-дату из будущего — возвращаем
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        if dt >= datetime.date.today():
            return date_str
    except Exception:
        pass
    # Обрабатываем русские и английские дни недели
    weekdays_map = {
        "понедельник": 0, "вторник": 1, "среда": 2, "четверг": 3,
        "пятница": 4, "суббота": 5, "воскресенье": 6,
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6,
    }
    low = date_str.strip().lower()
    if low in weekdays_map:
        return get_next_weekday(weekdays_map[low])
    # Если ничего не подошло — сегодняшняя дата
    return datetime.date.today().strftime("%Y-%m-%d")
def get_all_staff_list_inv(all_staff_list):
    # Корректная инверсия: {имя: id} → {id: имя}
    return {v: k for k, v in all_staff_list.items()}

def get_all_services_list(filter_str=None, max_results=15):
    """
    Возвращает словарь услуг: {название: id}.
    Если задан filter_str, то фильтрует услуги по названию.
    По умолчанию ограничивает результат 15 позициями.
    """
    services = api.get_services()
    services_data = services['data']
            
    all_services_list = {}
    
    count = 0
    for elem in services_data['services']:
        title = elem.get('title')
        service_id = elem.get('id')
        # Если фильтр задан — возвращаем только совпадения
        if filter_str:
            if filter_str.lower() in title.lower():
                all_services_list[title] = service_id
                count += 1
        else:
            all_services_list[title] = service_id
            count += 1
        # Ограничение на количество возвращаемых услуг
        if count >= max_results:
            break

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

def get_staff_for_service(service_id):
    staff_for_service_list = {}
    data = api.get_staff(service_id=service_id)
    data = data['data']
    for elem in data:
        staff_for_service_list .update({elem.get('name'): elem.get('id')})
    return staff_for_service_list

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
    all_staff = get_all_staff_list()  # {'Милана': 4052346, ...}
    staff_id_list = []
    for staff_name, staff_id in all_staff.items():
        try:
            available_for_staff = get_available_dates_for_staff_service(staff_id, service_id)
            # available_for_staff — список дат или None
            if isinstance(available_for_staff, list) and date in available_for_staff:
                staff_id_list.append(staff_id)
        except Exception as e:
            print(f"Ошибка получения дат для {staff_name}: {e}")
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
                "Возвращает словарь со всем персоналом, где ключами являются имена сотрудников, а значениями — их id."
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
                "Возвращает словарь со всем персоналом, где ключами являются id сотрудников, а значениями — их имена."
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
                "Возвращает словарь с услугами, где ключ — название услуги, значение — id услуги. "
                "Можно фильтровать услуги по названию с помощью параметра filter_str (например, 'чистка', 'спина'). "
                "Если filter_str не указан, возвращает не более 15 любых услуг для избежания спама."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filter_str": {
                        "type": "string",
                        "description": "Фильтр по названию услуги (например, 'спина', 'чистка'). Можно не указывать."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_services_list_inv",
            "description": (
                "Возвращает словарь со всеми услугами, где ключами являются id услуг, а значениями — их названия."
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
                "Возвращает список услуг, которые выполняет конкретный работник по id этого работника."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "staff_id": {"type": "string", "description": "id работника, для которого ищется список услуг"}
                },
                "required": ["staff_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_staff_for_service",
            "description": (
                "Возвращает словарь с работниками, которые выполняют конкретную услугу по id услуги, где ключами являются имена сотрудников, а значениями — их id."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id": {"type": "string", "description": "id услуги, для которой ищется список сотрудников"}
                },
                "required": ["service_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_service_info",
            "description": (
                "Возвращает описание услуги по ее id в виде списка: [название, цена, длительность (в минутах)]."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id": {"type": "string", "description": "id услуги для которой нужно найти информацию"}
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
                "Возвращает список дат, на которые доступна запись для заданного работника и услуги в формате ГГГГ-ММ-ДД."
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
                "Возвращает список дат, на которые доступна запись для заданной услуги (без указания работника) в формате ГГГГ-ММ-ДД."
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
                "Возвращает список с id персонала, доступного в заданную дату и на заданную услугу."
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
                "Возвращает список с id персонала, доступного в заданную дату, на заданное время, и на заданную услугу."
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
                "Возвращает список доступных времен для записи на заданную услугу к заданному работнику."
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
                "Возвращает список доступных времен для записи на заданную услугу (без указания работника)."
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
                "Выполняет запись клиента на заданное время, в заданную дату, на заданную услугу и к заданному работнику."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Имя клиента"},
                    "phone": {"type": "string", "description": "Номер телефона клиента"},
                    "service_id": {"type": "string", "description": "id услуги"},
                    "date_time": {"type": "string", "description": "Дата и время в формате ГГГГ-ММ-ДД'T'ЧЧ:ММ:СС'+3:00'"},
                    "staff_id": {"type": "string", "description": "id работника"},
                    "comment": {"type": "string", "description": "Комментарий к записи (по умолчанию — 'Запись через Whatsapp')."}
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

                # --- Supply-loop: обработка цепочки tool_calls ---
                # --- Supply-loop: обработка цепочки tool_calls ---
        while True:
            tool_calls = getattr(choice, "tool_calls", None)
            if tool_calls:
                # 1. assistant step: обязательно добавляем assistant с tool_calls!
                tool_calls_for_assistant = [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    }
                    for tool_call in tool_calls
                ]
                gpt_messages.append({
                    "role": "assistant",
                    "tool_calls": tool_calls_for_assistant
                })

                # 2. Добавляем tool-ответы по каждой функции
                for tool_call in tool_calls:
                    fn_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    print("Function call:", fn_name, "| Args:", args)

                    # --- НОРМАЛИЗАЦИЯ ДАТЫ ---
                    if "date" in args:
                        args["date"] = normalize_date(args["date"])

                    result = None
                    try:
                        if fn_name == "book_service":
                            all_services = get_all_services_list()
                            all_staff = get_all_staff_list()
                            service_id = all_services.get(args['service'])
                            staff_id = all_staff.get(args['master'])
                            date = args['date']
                            time = args['time']
                            date_time = f"{date} {time}"
                            if not service_id:
                                result = f"❗️Услуга '{args['service']}' не найдена. Доступные: {', '.join(all_services.keys())}"
                            elif not staff_id:
                                result = f"❗️Мастер '{args['master']}' не найден. Доступные: {', '.join(all_staff.keys())}"
                            else:
                                try:
                                    book(
                                        name=args['master'],
                                        phone=phone,
                                        service_id=service_id,
                                        date_time=date_time,
                                        staff_id=staff_id,
                                        comment="Запись через WhatsApp"
                                    )
                                    result = f"✅ Вы успешно записаны на {args['service']} к мастеру {args['master']} {date} в {time}! Ждём вас в салоне."
                                except Exception as e:
                                    result = f"Ошибка при записи: {e}"
                        elif fn_name == "get_staff_for_service":
                            raw = get_staff_for_service(args.get("service_id"))
                            if isinstance(raw, dict) and raw:
                                names = list(raw.keys())
                                if names:
                                    result = "Эту услугу выполняют:\n" + "\n".join(f"{i+1}. {name}" for i, name in enumerate(names))
                                else:
                                    result = "Нет доступных мастеров для этой услуги."
                            else:
                                result = "Не удалось получить информацию по мастерам для этой услуги."
                        elif fn_name == "get_staff_for_date_service":
                            raw = get_staff_for_date_service(args.get("service_id"), args.get("date"))
                            if isinstance(raw, list) and raw:
                                all_staff_names = get_all_staff_list_inv(get_all_staff_list())
                                staff_names = [all_staff_names.get(staff_id, f"ID {staff_id}") for staff_id in raw]
                                if staff_names:
                                    result = "В этот день доступны мастера:\n" + "\n".join(f"{i+1}. {name}" for i, name in enumerate(staff_names))
                                else:
                                    result = "На эту дату нет доступных мастеров."
                            else:
                                result = "Не удалось получить информацию по мастерам."
                        elif fn_name == "get_available_times_for_staff_service":
                            raw = get_available_times_for_staff_service(args.get("staff_id"), args.get("service_id"), args.get("date"))
                            if isinstance(raw, list):
                                if raw:
                                    result = "Доступные времена записи:\n" + "\n".join(raw)
                                else:
                                    result = "Нет доступных времён на эту дату."
                            else:
                                result = "Не удалось получить времена записи."
                        # ---- остальные функции без изменений, либо аналогичная обработка ----
                        elif fn_name == "get_all_staff_list":
                            result = get_all_staff_list()
                        elif fn_name == "get_all_staff_list_inv":
                            result = get_all_staff_list_inv(get_all_staff_list())
                        elif fn_name == "get_all_services_list":
                            filter_str = args.get("filter_str")
                            result = get_all_services_list(filter_str=filter_str)
                            if not result:
                                result = "❗️Не найдено ни одной услуги по вашему запросу. Попробуйте уточнить название."
                        elif fn_name == "get_all_services_list_inv":
                            result = get_all_services_list_inv(get_all_services_list())
                        elif fn_name == "get_services_title_list_for_staff":
                            result = get_services_title_list_for_staff(args.get("staff_id"))
                        elif fn_name == "get_service_info":
                            result = get_service_info(args.get("service_id"))
                        elif fn_name == "get_available_dates_for_staff_service":
                            result = get_available_dates_for_staff_service(args.get("staff_id"), args.get("service_id"))
                        elif fn_name == "get_available_dates_for_service":
                            result = get_available_dates_for_service(args.get("service_id"))
                        elif fn_name == "get_staff_for_date_time_service":
                            result = get_staff_for_date_time_service(args.get("service_id"), args.get("date"), args.get("time"))
                        elif fn_name == "get_available_times_for_service":
                            result = get_available_times_for_service(args.get("service_id"), args.get("date"))
                        elif fn_name == "book":
                            book(args.get("name"), args.get("phone", phone), args.get("service_id"), args.get("date_time"),
                                 args.get("staff_id"), args.get("comment", "Запись через WhatsApp"))
                            result = f"✅ Вы успешно записаны на услугу {args.get('service_id')} к мастеру {args.get('staff_id')} на {args.get('date_time')}!"
                        elif fn_name == "get_knowledge_base":
                            kb = get_knowledge_base()
                            result = "\n".join([f"{item['term']}: {item['explanation']}" for item in kb])
                        else:
                            result = "Функция не реализована или параметры не распознаны."
                    except Exception as e:
                        result = f"Ошибка при вызове функции: {e}"

                    gpt_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })

                # 3. Новый запрос к GPT (вся supply-chain)
                response2 = client.chat.completions.create(
                    model="gpt-4o",
                    messages=gpt_messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.1
                )
                choice = response2.choices[0].message
                continue
            else:
                # Нет tool_calls: выдаём финальный текст пользователю
                final_answer = choice.content or "Нет ответа"
                send_message(phone, final_answer)
                add_memory(phone, "assistant", final_answer)
                return "OK", 200







        else:
            print("⚠️ GPT не вызвал функцию — fallback в чистый диалог.")
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
