import os
import requests
import yclients
import httpx
import datetime
from yclients import YClientsAPI
import openai
from flask import Flask, request
import json
import logging

logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s [%(levelname)s] %(message)s",
	handlers=[
		logging.FileHandler("bot.log"),
		logging.StreamHandler()
	]
)

GREEN_API_ID = os.getenv("GREEN_API_ID")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
OPENAI_API_TOKEN = os.getenv("OPENAI_API_TOKEN")
YCLIENTS_APPLICATION_ID = os.getenv("YCLIENTS_APPLICATION_ID")
YCLIENTS_API_TOKEN = os.getenv("YCLIENTS_API_TOKEN")
YCLIENTS_COMPANY_ID = os.getenv("YCLIENTS_COMPANY_ID")
YCLIENTS_API_TOKEN_USER = os.getenv("YCLIENTS_API_TOKEN_USER")
assert all((YCLIENTS_API_TOKEN, YCLIENTS_COMPANY_ID, YCLIENTS_APPLICATION_ID, GREEN_API_ID, GREEN_API_TOKEN, OPENAI_API_TOKEN, YCLIENTS_API_TOKEN_USER)) == True, "Can't find env var"

api = YClientsAPI(token=YCLIENTS_API_TOKEN, company_id=YCLIENTS_COMPANY_ID, form_id=YCLIENTS_APPLICATION_ID)


def get_service_categories():
	url = f"https://yclients.com/api/v1/company/{YCLIENTS_COMPANY_ID}/service_categories"
	headers = {
		'Content-Type': 'application/json',
		"Accept": "application/vnd.yclients.v2+json",
		"Authorization": f"Bearer {YCLIENTS_API_TOKEN}, User {YCLIENTS_API_TOKEN_USER}"
	}
	resp = requests.get(url, headers=headers)
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
	return {v: k for k, v in all_services_list.items()}


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
	available_dates = api.get_available_days(
		staff_id=staff_id, service_id=service_id)
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
			available_for_staff = get_available_dates_for_staff_service(
				staff_id, service_id)
			# available_for_staff — список дат или None
			if isinstance(available_for_staff, list) and date in available_for_staff:
				staff_id_list.append(staff_id)
		except Exception as e:
			logging.error(f"Ошибка получения дат для {staff_name}: {e}")
	return staff_id_list


def get_staff_for_date_time_service(service_id, date, time):
	all_staff_id_list_inv = get_all_staff_list_inv(get_all_staff_list())
	staff_id_list = []
	for key in all_staff_id_list_inv:
		available_time_for_staff = get_available_times_for_staff_service(
			key, service_id, date)
		if time in available_time_for_staff:
			staff_id_list.append(key)
	return staff_id_list


def get_available_times_for_staff_service(staff_id, service_id, date):
	time_slots = api.get_available_times(
		staff_id=staff_id, service_id=service_id, day=date)
	print(time_slots)
	slots = time_slots['data']
	# slots = [{'time': '12:00'}, ...]
	available_time = [elem['time'] for elem in slots if 'time' in elem]
	return available_time


def get_available_times_for_service(service_id, date):
	staff = get_staff_for_date_service(service_id, date)
	available_times = []
	for staff_id in staff:
		time_slots = api.get_available_times(
			staff_id=staff_id, service_id=service_id, day=date)
		times = [elem['time'] for elem in time_slots['data'] if 'time' in elem]
		for t in times:
			if t not in available_times:
				available_times.append(t)
	return available_times


def book(name, phone, service_id, date_time, staff_id, comment):
	# Преобразуем дату-время в ISO, если не приходит уже готовым
	# Предполагаем, что date_time = 'YYYY-MM-DD HH:MM'
	if "T" not in date_time:
		dt = datetime.datetime.strptime(date_time, "%Y-%m-%d %H:%M")
		date_time = dt.strftime("%Y-%m-%dT%H:%M:00+03:00")
	api.book(
		booking_id=0,
		fullname=name,
		phone=phone,
		email="noemail@noemail.com",
		service_id=service_id,
		date_time=date_time,
		staff_id=staff_id,
		comment=comment
	)
	print('booked')


# --- Flask + OpenAI function calling ---

# --- Flask + OpenAI function calling ---


# --- Google Apps Script API для работы с памятью и промтами ---
GAS_API_URL = "https://script.google.com/macros/s/AKfycbxL2dDQWi88cURqq_OFJYLd56JKEuZjLJW41aYqguzedchA1jprv8zpm6Tvk-8eyZdI/exec"


def get_system_prompt():
	with open("prompt.txt", "r", encoding="utf-8") as prompt:
		text = prompt.read()
	return text


def get_knowledge_base():
	resp = requests.get(GAS_API_URL, params={"type": "knowledge"})
	resp.raise_for_status()
	return resp.json()


def get_memory(user_id):
	resp = requests.get(GAS_API_URL, params={
						"type": "memory", "userId": str(user_id)})
	try:
		return resp.json()
	except Exception as e:
		logging.error(
			f"GAS get_memory не вернул JSON! Статус: {resp.status_code}, Ответ: {resp.text}")
		# Можно вернуть пустую историю — чтобы бот не падал
		return []


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

client = openai.OpenAI(api_key=OPENAI_API_TOKEN)
app = Flask(__name__)

with open("tools.json", "r", encoding='utf-8') as fn: tools = json.load(fn)


def send_message(phone, text):
	url = f"https://api.green-api.com/waInstance{GREEN_API_ID}/sendMessage/{GREEN_API_TOKEN}"
	payload = {
		"chatId": f"{phone}@c.us",
		"message": text
	}
	response = requests.post(url, json=payload)
	logging.info(f"Green API ответ: {response.status_code} - {response.text}")


@app.route("/webhook", methods=["POST"])
def webhook():
	try:
		data = request.get_json()
		logging.info(f"Webhook: {data}")

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
		logging.info(f"Входящее сообщение: '{message}' от {phone}")

		# --- Долговременная память (GAS) ---
		history = get_memory(phone)
		add_memory(phone, "user", message)

		# --- SYSTEM PROMPT ---
		system_prompt = get_system_prompt()
		gpt_messages = [{"role": "system", "content": system_prompt}]
		for msg in history:
			gpt_messages.append(
				{"role": msg["role"], "content": msg["content"]})
		gpt_messages.append({"role": "user", "content": message})

		response = client.chat.completions.create(
			model="gpt-4o",
			messages=gpt_messages,
			tools=tools,
			tool_choice="auto",
			temperature=0.1
		)

		choice = response.choices[0].message
		logging.info(f"--- ОТВЕТ OPENAI ---\n{choice}\n----------------------")

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
					logging.info(f"Function call: {fn_name} | Args: {args}")

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
									name = history[-1]['content'] if history else "Клиент WhatsApp"
									book(
										name=name,
										phone=phone,
										service_id=service_id,
										date_time=date_time,
										staff_id=staff_id,
										comment="Запись через WhatsApp"
									)
									result = f"✅ Вы успешно записаны на {args['service']} к мастеру {args['master']} {date} в {time}! Ждём вас в салоне."
									logging.info(
										f"Успешная запись: клиент={name}, phone={phone}, service_id={service_id}, staff_id={staff_id}, date_time={date_time}")
								except Exception as e:
									result = f"Ошибка при записи: {e}"
						elif fn_name == "get_staff_for_service":
							raw = get_staff_for_service(args.get("service_id"))
							if isinstance(raw, dict) and raw:
								names = list(raw.keys())
								if names:
									result = "Эту услугу выполняют:\n" + \
										"\n".join(
											f"{i+1}. {name}" for i, name in enumerate(names))
								else:
									result = "Нет доступных мастеров для этой услуги."
							else:
								result = "Не удалось получить информацию по мастерам для этой услуги."
						elif fn_name == "get_staff_for_date_service":
							raw = get_staff_for_date_service(
								args.get("service_id"), args.get("date"))
							if isinstance(raw, list) and raw:
								all_staff_names = get_all_staff_list_inv(
									get_all_staff_list())
								staff_names = [all_staff_names.get(
									staff_id, f"ID {staff_id}") for staff_id in raw]
								if staff_names:
									result = "В этот день доступны мастера:\n" + \
										"\n".join(
											f"{i+1}. {name}" for i, name in enumerate(staff_names))
								else:
									result = "На эту дату нет доступных мастеров."
							else:
								result = "Не удалось получить информацию по мастерам."
						elif fn_name == "get_available_times_for_staff_service":
							raw = get_available_times_for_staff_service(
								args.get("staff_id"), args.get("service_id"), args.get("date"))
							if isinstance(raw, list):
								if raw:
									result = "Доступные времена записи:\n" + \
										"\n".join(raw)
								else:
									result = "Нет доступных времён на эту дату."
							else:
								result = "Не удалось получить времена записи."
						# ---- остальные функции без изменений, либо аналогичная обработка ----
						elif fn_name == "get_all_staff_list":
							result = get_all_staff_list()
						elif fn_name == "get_service_categories":
							result = get_service_categories()
						elif fn_name == "get_all_staff_list_inv":
							result = get_all_staff_list_inv(
								get_all_staff_list())
						elif fn_name == "get_all_services_list":
							filter_str = args.get("filter_str")
							result = get_all_services_list(
								filter_str=filter_str)
							if not result:
								result = "❗️Не найдено ни одной услуги по вашему запросу. Попробуйте уточнить название."
						elif fn_name == "get_all_services_list_inv":
							result = get_all_services_list_inv(
								get_all_services_list())
						elif fn_name == "get_services_title_list_for_staff":
							result = get_services_title_list_for_staff(
								args.get("staff_id"))
						elif fn_name == "get_service_info":
							result = get_service_info(args.get("service_id"))
						elif fn_name == "get_available_dates_for_staff_service":
							result = get_available_dates_for_staff_service(
								args.get("staff_id"), args.get("service_id"))
						elif fn_name == "get_available_dates_for_service":
							result = get_available_dates_for_service(
								args.get("service_id"))
						elif fn_name == "get_staff_for_date_time_service":
							result = get_staff_for_date_time_service(
								args.get("service_id"), args.get("date"), args.get("time"))
						elif fn_name == "get_available_times_for_service":
							result = get_available_times_for_service(
								args.get("service_id"), args.get("date"))
						elif fn_name == "book":
							book(args.get("name"), args.get("phone", phone), args.get("service_id"), args.get("date_time"),
								 args.get("staff_id"), args.get("comment", "Запись через WhatsApp"))
							result = f"✅ Вы успешно записаны на услугу {args.get('service_id')} к мастеру {args.get('staff_id')} на {args.get('date_time')}!"
						elif fn_name == "get_knowledge_base":
							kb = get_knowledge_base()
							result = "\n".join(
								[f"{item['term']}: {item['explanation']}" for item in kb])
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
			fallback_response = generate_gpt_response(
				history, message, system_prompt)
			send_message(phone, fallback_response)
			add_memory(phone, "assistant", fallback_response)
			return "OK", 200

	except Exception as e:
		logging.exception("Ошибка в webhook:")
		send_message(phone, "Произошла ошибка на сервере, попробуйте позже.")
		return "OK", 200


@app.route("/", methods=["GET"])
def home():
	return "Бот работает!", 200


if __name__ == "__main__":
	print(">>> Flask is starting!")
	print("YCLIENTS_API_TOKEN:", YCLIENTS_API_TOKEN)
	print("YCLIENTS_COMPANY_ID:", YCLIENTS_COMPANY_ID)
	print("YCLIENTS_APPLICATION_ID:", YCLIENTS_APPLICATION_ID)
	print("OPENAI_API_TOKEN:", OPENAI_API_TOKEN)
	print("GREEN_API_ID:", GREEN_API_ID)
	print("GREEN_API_TOKEN:", GREEN_API_TOKEN)
	app.run(host="0.0.0.0", port=8000)
