from flask import Flask, request
import requests
import os
import openai
import json
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
    all_staff = api.get_staff()
    staff_dict = {}
    for elem in all_staff['data']:
        staff_name = elem.get('name')
        staff_id = elem.get('id')
        staff_dict[staff_name] = staff_id
    return staff_dict

def get_all_services_list():
    services = api.get_services()
    services_dict = {}
    for elem in services['data']['services']:
        service_title = elem.get('title')
        service_id = elem.get('id')
        services_dict[service_title] = service_id
    return services_dict

def find_service_id(user_input, services_dict):
    if user_input in services_dict:
        return services_dict[user_input]
    for name, id_ in services_dict.items():
        if user_input and user_input.lower() in name.lower():
            return id_
    return None

def book(name, phone, email, service_id, date_time, staff_id, comment):
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
    return res

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
        "description": "Записать пользователя на услугу в салоне красоты",
        "parameters": {
            "type": "object",
            "properties": {
                "service": {"type": "string", "description": "Название услуги"},
                "master": {"type": "string", "description": "Имя мастера"},
                "date": {"type": "string", "description": "Дата (например, 19.06.2025)"},
                "time": {"type": "string", "description": "Время (например, 13:00)"}
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

        # --- Вызываем OpenAI с function calling ---
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Ты вежливый администратор салона красоты. Помоги клиенту записаться на услугу, если он сообщил параметры бронирования — вызови функцию book_service."},
                {"role": "user", "content": message}
            ],
            functions=functions,
            function_call="auto",
            temperature=0.2
        )

        choice = response.choices[0].message
        # Логируем что приходит
        print("Ответ OpenAI:", choice)

        # Если GPT вызвал функцию booking
        if hasattr(choice, "function_call") and choice.function_call:
            args = json.loads(choice.function_call.arguments)
            print("Function call args:", args)

            # Проверяем есть ли такие услуга и мастер в базе
            all_services = get_all_services_list()
            all_staff = get_all_staff_list()
            service_id = find_service_id(args['service'], all_services)
            staff_id = all_staff.get(args['master'])
            date_time = f"{args['date']} {args['time']}"

            if not service_id:
                send_message(phone, f"Не могу найти услугу '{args['service']}'. Вот список доступных: {', '.join(all_services.keys())}")
                return "OK", 200
            if not staff_id:
                send_message(phone, f"Не могу найти мастера '{args['master']}'. Вот кто доступен: {', '.join(all_staff.keys())}")
                return "OK", 200

            try:
                book(args['master'], phone, "noemail@email.com", service_id, date_time, staff_id, "auto-book")
                send_message(phone, f"Вы успешно записаны на {args['service']} к мастеру {args['master']} {args['date']} в {args['time']}! Ждём вас в нашем салоне.")
            except Exception as e:
                send_message(phone, f"Произошла ошибка при записи: {e}")
            return "OK", 200

        # Если GPT не смог извлечь параметры — попроси уточнить
        else:
            if choice.content and "услуга" in choice.content.lower():
                send_message(phone, "Пожалуйста, укажите услугу, мастера, дату и время для записи (можно одним сообщением).")
            else:
                send_message(phone, choice.content or "Поясните, пожалуйста!")
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
