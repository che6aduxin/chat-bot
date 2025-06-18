import os
import requests
import openai
import httpx
import ujson
import yclients
from yclients import YClientsAPI
from flask import Flask, request
import json

# --- Твои функции для работы с Yclients должны быть определены в этом же файле или импортированы! ---

# Сюда скопируй все свои функции из блока, который ты присылал ранее:
# get_all_staff_list(), get_all_services_list(), book(), и т.д.
# Если они в отдельном файле, можно сделать так:
# from your_yclients_functions_file import *

app = Flask(__name__)

GREEN_API_ID = os.getenv("GREEN_API_ID")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
OPENAI_API_TOKEN = os.getenv("OPENAI_API_TOKEN")

client = openai.OpenAI(api_key=OPENAI_API_TOKEN)

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
