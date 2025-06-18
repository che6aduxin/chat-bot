from flask import Flask, request
import requests
import os
import openai
from yclients import YClientsAPI

app = Flask(__name__)

# Переменные окружения
GREEN_API_ID = os.getenv("GREEN_API_ID")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
OPENAI_API_TOKEN = os.getenv("OPENAI_API_TOKEN")
YCLIENTS_API_TOKEN = os.getenv("YCLIENTS_API_TOKEN")
YCLIENTS_COMPANY_ID = os.getenv("YCLIENTS_COMPANY_ID")

openai.api_key = OPENAI_API_TOKEN

api = YClientsAPI(token=YCLIENTS_API_TOKEN, company_id=YCLIENTS_COMPANY_ID)

# ------- YCLIENTS ФУНКЦИИ (копируй из своего файла сюда) -------
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

# ------- NLP/AI функции -------
def find_booking_intent(user_message):
    prompt = (
        "Ты администратор салона красоты. "
        "Если пользователь хочет записаться, выдели услугу, мастера, дату и время. "
        "Ответь строго в формате: 'услуга:...; мастер:...; дата:...; время:...'. Если чего-то нет — укажи NA.\n"
        f"Сообщение: {user_message}"
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Ты выявляешь намерения клиента и вытаскиваешь из сообщения услугу, мастера, дату и время."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print("Ошибка ChatGPT:", e)
        return None

def send_message(phone, text):
    url = f"https://api.green-api.com/waInstance{GREEN_API_ID}/sendMessage/{GREEN_API_TOKEN}"
    payload = {
        "chatId": f"{phone}@c.us",
        "message": text
    }
    response = requests.post(url, json=payload)
    print(f"Green API ответ: {response.status_code} - {response.text}")

# ------- Webhook -------
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        print("Webhook:", data)

        if data.get("typeWebhook") != "incomingMessageReceived":
            return "Ignored", 200

        message = data['messageData']['textMessageData']['textMessage']
        phone = data['senderData']['chatId'].replace("@c.us", "")

        intent = find_booking_intent(message)
        print("INTENT:", intent)

        # Пример: "услуга: стрижка; мастер: Иван; дата: 2025-06-18; время: 18:00"
        parsed = {"услуга": "NA", "мастер": "NA", "дата": "NA", "время": "NA"}
        try:
            for part in intent.split(";"):
                key, value = part.strip().split(":", 1)
                parsed[key.strip()] = value.strip()
        except Exception as e:
            print("Парсинг намерения не удался:", e)

        # Если чего-то не хватает — спросить
        if "NA" in parsed.values():
            missing = [k for k, v in parsed.items() if v == "NA"]
            reply = f"Пожалуйста, уточните: {', '.join(missing)}."
            send_message(phone, reply)
            return "OK", 200

        # Подбираем id услуги и мастера по названиям
        all_services = get_all_services_list()
        service_id = all_services.get(parsed["услуга"])
        all_staff = get_all_staff_list()
        staff_id = all_staff.get(parsed["мастер"])

        if not service_id or not staff_id:
            send_message(phone, "Не удалось найти услугу или мастера. Проверьте, пожалуйста, правильность написания.")
            return "OK", 200

        # Формируем дату и время
        date_time = f"{parsed['дата']} {parsed['время']}"
        try:
            book(parsed["мастер"], phone, "noemail@email.com", service_id, date_time, staff_id, "auto-book")
            reply = "Вы успешно записаны! Ждём вас в нашем салоне."
        except Exception as e:
            reply = f"Произошла ошибка при записи: {e}"

        send_message(phone, reply)
        return "OK", 200

    except Exception as e:
        print("Ошибка в webhook:", e)
    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "Бот работает!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

