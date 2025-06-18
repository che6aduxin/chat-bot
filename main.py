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

# YClients API — обязательно form_id (любая строка, напр. "1")
api = YClientsAPI(
    token=YCLIENTS_API_TOKEN,
    company_id=YCLIENTS_COMPANY_ID,
    form_id="1"
)

# Простая "память" на пользователя (для прототипа)
user_context = {}

# ------- YCLIENTS ФУНКЦИИ -------
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
    # Сначала ищем полное совпадение:
    if user_input in services_dict:
        return services_dict[user_input]
    # Потом ищем по вхождению (регистр игнорируем)
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

# ------- NLP/AI функции -------
def find_booking_intent(ctx, user_message):
    prompt = (
        f"Ты администратор салона красоты. Клиент уже сообщил: {ctx}. "
        "Сейчас он пишет: " + user_message +
        "\nВыдели, есть ли новая информация по услуге, мастеру, дате или времени. "
        "Ответь в формате: 'услуга:...; мастер:...; дата:...; время:...'. Если чего-то нет — укажи NA."
        "\nЕсли клиент просит показать список услуг или интересуется их наличием, напиши: 'показать_услуги'."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Ты администратор салона. Анализируешь реплики клиента и определяешь заполненные поля (услуга, мастер, дата, время)."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print("Ошибка ChatGPT:", e)
        return None

def ask_for_next_field(ctx, field):
    # Можно сделать вопросы более вариативными через ChatGPT — пока базовые
    questions = {
        "услуга": "Какую услугу вы хотите?",
        "мастер": "К какому мастеру вы хотите записаться?",
        "дата": "На какую дату хотите записаться?",
        "время": "Во сколько вам удобно прийти?"
    }
    return questions.get(field, "Поясните, пожалуйста!")

def send_message(phone, text):
    url = f"https://api.green-api.com/waInstance{GREEN_API_ID}/sendMessage/{GREEN_API_TOKEN}"
    payload = {
        "chatId": f"{phone}@c.us",
        "message": text
    }
    response = requests.post(url, json=payload)
    print(f"Green API ответ: {response.status_code} - {response.text}")

def update_context_from_message(ctx, message):
    """Обновляем контекст из текста сообщения клиента через ChatGPT"""
    intent = find_booking_intent(ctx, message)
    print("Booking intent:", intent)  # ЛОГИРОВАНИЕ!
    if intent and "показать_услуги" in intent:
        ctx["show_services"] = True
        return
    try:
        for part in intent.split(";"):
            if ":" in part:
                key, value = part.strip().split(":", 1)
                key = key.strip()
                value = value.strip()
                if value and value != "NA":
                    ctx[key] = value
    except Exception as e:
        print("Парсинг намерения не удался:", e)

# ------- Webhook -------
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

        # Контекст пользователя
        if phone not in user_context:
            user_context[phone] = {"услуга": None, "мастер": None, "дата": None, "время": None}
        ctx = user_context[phone]

        # Обновляем контекст по текущему сообщению
        ctx["show_services"] = False
        update_context_from_message(ctx, message)

        # Если человек спросил про услуги — показать список и выйти из функции
        if ctx.get("show_services"):
            all_services = get_all_services_list()
            send_message(phone, "Вот наши услуги: " + ", ".join(all_services.keys()))
            ctx["show_services"] = False  # сбрасываем флаг
            return "OK", 200

        # Проверяем, чего не хватает
        missing = [k for k, v in ctx.items() if not v and k != "show_services"]
        if missing:
            # Запрашиваем только следующее недостающее поле (шаг за шагом)
            next_field = missing[0]
            reply = ask_for_next_field(ctx, next_field)
            send_message(phone, reply)
            return "OK", 200
        else:
            # Все поля заполнены — подтверждаем и бронируем
            reply = f"Вы хотите {ctx['услуга']} у {ctx['мастер']} {ctx['дата']} в {ctx['время']} — всё верно?"
            send_message(phone, reply)
            # Здесь можно ждать подтверждения или сразу бронировать
            # Если бронируем сразу:
            all_services = get_all_services_list()
            service_id = find_service_id(ctx["услуга"], all_services)
            all_staff = get_all_staff_list()
            staff_id = all_staff.get(ctx["мастер"])
            date_time = f"{ctx['дата']} {ctx['время']}"
            if not service_id:
                send_message(phone, f"Не могу найти услугу '{ctx['услуга']}'. Вот список доступных: {', '.join(all_services.keys())}")
                return "OK", 200
            if not staff_id:
                send_message(phone, f"Не могу найти мастера '{ctx['мастер']}'. Вот кто доступен: {', '.join(all_staff.keys())}")
                return "OK", 200
            try:
                book(ctx["мастер"], phone, "noemail@email.com", service_id, date_time, staff_id, "auto-book")
                send_message(phone, "Вы успешно записаны! Ждём вас в нашем салоне.")
                # После записи — очищаем контекст пользователя
                user_context[phone] = {"услуга": None, "мастер": None, "дата": None, "время": None}
            except Exception as e:
                send_message(phone, f"Произошла ошибка при записи: {e}")
            return "OK", 200

    except Exception as e:
        print("Ошибка в webhook:", e)
    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "Бот работает!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

