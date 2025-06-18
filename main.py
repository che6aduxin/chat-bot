from flask import Flask, request
import requests
import os
import openai
import json
import ujson
import httpx
import yclients
from yclients import YClientsAPI

app = Flask(__name__)

GREEN_API_ID = os.getenv("GREEN_API_ID")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
OPENAI_API_TOKEN = os.getenv("OPENAI_API_TOKEN")
YCLIENTS_API_TOKEN = os.getenv("YCLIENTS_API_TOKEN")
YCLIENTS_COMPANY_ID = os.getenv("YCLIENTS_COMPANY_ID")

client = openai.OpenAI(api_key=OPENAI_API_TOKEN)

api = YClientsAPI(
    token=YCLIENTS_API_TOKEN,
    company_id=YCLIENTS_COMPANY_ID,
    form_id="1"
)

def get_all_staff_list():
    try:
        staff_response = api.get_staff()
        print("YClients staff_response:", staff_response)
        staff_dict = {}
        for elem in staff_response.get('data', []):
            staff_name = elem.get('name')
            staff_id = elem.get('id')
            staff_dict[staff_name] = staff_id
        print("staff_dict:", staff_dict)
        return staff_dict
    except Exception as e:
        print("Ошибка при получении списка мастеров:", e)
        return None

def get_all_services_list():
    try:
        services_response = api.get_services()
        print("YClients services_response:", services_response)
        services_dict = {}
        for elem in services_response.get('data', {}).get('services', []):
            service_title = elem.get('title')
            service_id = elem.get('id')
            services_dict[service_title] = service_id
        print("services_dict:", services_dict)
        return services_dict
    except Exception as e:
        print("Ошибка при получении списка услуг:", e)
        return None

def find_service_id(user_input, services_dict):
    if services_dict is None:
        print("find_service_id: services_dict is None")
        return None
    if user_input in services_dict:
        return services_dict[user_input]
    for name, id_ in services_dict.items():
        if user_input and user_input.lower() in name.lower():
            return id_
    return None

def book(name, phone, email, service_id, date_time, staff_id, comment):
    try:
        res = api.book(
            booking_id=0,
            fullname=name,
            phone=phone,
            email=email,
            service_id=service_id,
            date_time=date_time,
            staff_id=staff_id,
            comment=comment
        )
        print("Результат бронирования:", res)
        return res
    except Exception as e:
        print("Ошибка при бронировании:", e)
        return None

def send_message(phone, text):
    url = f"https://api.green-api.com/waInstance{GREEN_API_ID}/sendMessage/{GREEN_API_TOKEN}"
    payload = {
        "chatId": f"{phone}@c.us",
        "message": text
    }
    response = requests.post(url, json=payload)
    print(f"Green API ответ: {response.status_code} - {response.text}")

# --- Function calling спецификация ---
functions = [
    {
        "name": "book_service",
        "description": (
            "Бронирование услуги в салоне красоты. "
            "ВСЕГДА вызывай функцию, если в сообщении есть все четыре параметра: "
            "услуга, мастер, дата (ДД.ММ.ГГГГ), время (ЧЧ:ММ). "
            "Если не хватает параметров — спроси только их."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "service": {"type": "string", "description": "Название услуги, например 'Массаж'"},
                "master": {"type": "string", "description": "Имя мастера, например 'Андрей'"},
                "date": {"type": "string", "description": "Дата в формате ДД.ММ.ГГГГ, например '19.06.2025'"},
                "time": {"type": "string", "description": "Время в формате ЧЧ:ММ, например '13:00'"}
            },
            "required": ["service", "master", "date", "time"]
        }
    }
]

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

        system_prompt = (
            "Ты виртуальный ассистент салона красоты. "
            "ЕСЛИ в сообщении пользователя есть все параметры (услуга, мастер, дата, время), "
            "ВСЕГДА вызывай функцию book_service, не отвечай текстом! "
            "Если чего-то не хватает — спроси только недостающие поля. "
            "Формат даты: ДД.ММ.ГГГГ. Формат времени: ЧЧ:ММ. "
            "Пример: 'Массаж, Андрей, 19.06.2025, 13:00'"
        )

        print("Отправляем в OpenAI system prompt:", system_prompt)

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
        print("\n--- ПОЛНЫЙ ОТВЕТ OpenAI ---\n", choice, "\n---------------------------\n")

        if getattr(choice, "function_call", None):
            args = json.loads(choice.function_call.arguments)
            print("Function call args:", args)

            all_services = get_all_services_list()
            all_staff = get_all_staff_list()
            print("all_services:", all_services)
            print("all_staff:", all_staff)
            print("args:", args)

            if all_services is None or all_staff is None:
                print("❌ Не удалось получить список услуг или мастеров!")
                send_message(phone, "Ошибка: не удалось получить список услуг или мастеров (None).")
                return "OK", 200

            service_id = find_service_id(args['service'], all_services)
            staff_id = all_staff.get(args['master']) if all_staff else None
            date_time = f"{args['date']} {args['time']}"
            print("service_id:", service_id)
            print("staff_id:", staff_id)

            if not service_id:
                err_msg = f"❗️Услуга '{args['service']}' не найдена. Есть: {', '.join(all_services.keys())}"
                print(err_msg)
                send_message(phone, err_msg)
                return "OK", 200
            if not staff_id:
                err_msg = f"❗️Мастер '{args['master']}' не найден. Доступные: {', '.join(all_staff.keys())}"
                print(err_msg)
                send_message(phone, err_msg)
                return "OK", 200

            booking_result = book(args['master'], phone, "noemail@email.com", service_id, date_time, staff_id, "auto-book")
            if booking_result is not None:
                ok_msg = f"Вы успешно записаны на {args['service']} к мастеру {args['master']} {args['date']} в {args['time']}! Ждём вас в салоне."
                print(ok_msg)
                send_message(phone, ok_msg)
            else:
                print("❌ Ошибка при бронировании!")
                send_message(phone, "Не удалось завершить бронирование.")
            return "OK", 200

        else:
            print("⚠️ GPT не вызвал функцию! Полный ответ:", choice)
            if choice.content:
                send_message(phone, "Бот не смог автоматически распознать все параметры. Пожалуйста, укажите услугу, мастера, дату и время в формате: Услуга, Мастер, ДД.ММ.ГГГГ, ЧЧ:ММ\n\n" + "GPT ответ: " + choice.content)
            else:
                send_message(phone, "Бот не вызвал функцию бронирования. Проверьте формат сообщения и попробуйте ещё раз.")
            return "OK", 200

    except Exception as e:
        print("Ошибка в webhook:", e)
        send_message(phone, "Произошла внутренняя ошибка, попробуйте позже.")
    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "Бот работает!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
