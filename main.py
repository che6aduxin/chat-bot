import requests
from YClientsAPI import YClientsAPI
import openai
from openai.types.chat.chat_completion import Choice
from flask import Flask, request
import json
import logging
import mysql.connector as mysql
from dotenv import dotenv_values

# Configuration
CONFIG = dotenv_values(".env") # env variables
GREEN_API_ID = CONFIG["GREEN_API_ID"]
GREEN_API_TOKEN = CONFIG["GREEN_API_TOKEN"]
OPENAI_API_TOKEN = CONFIG["OPENAI_API_TOKEN"]
YCLIENTS_APPLICATION_ID = CONFIG["YCLIENTS_APPLICATION_ID"]
YCLIENTS_API_TOKEN = CONFIG["YCLIENTS_API_TOKEN"]
YCLIENTS_COMPANY_ID = CONFIG["YCLIENTS_COMPANY_ID"]
YCLIENTS_API_TOKEN_USER = CONFIG["YCLIENTS_API_TOKEN_USER"]
DB_MAX_MESSAGES = CONFIG["DB_MAX_MESSAGES"]

db_config = {
	"user": CONFIG["DB_USERNAME"],
	"password": CONFIG["DB_PASSWORD"],
	"host": CONFIG["DB_HOST"],
	"port": CONFIG["DB_PORT"],
	"database": CONFIG["DB_NAME"]
}
pool = mysql.pooling.MySQLConnectionPool(pool_name="main_pool", pool_size=5, pool_reset_session=True, **db_config) # 5 connections for db access
with open("tools.json", "r", encoding='utf-8') as fn: tools = json.load(fn) # tools
yclients_api = YClientsAPI(YCLIENTS_API_TOKEN, YCLIENTS_API_TOKEN_USER, YCLIENTS_COMPANY_ID) # yclients class object


logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s [%(levelname)s] %(message)s",
	handlers=[
		logging.FileHandler("bot.log"),
		logging.StreamHandler()
	]
)

assert all((YCLIENTS_API_TOKEN, YCLIENTS_COMPANY_ID, YCLIENTS_APPLICATION_ID, GREEN_API_ID, GREEN_API_TOKEN, OPENAI_API_TOKEN, YCLIENTS_API_TOKEN_USER)) == True, "Can't find env var"
# End of configuration

# System functions
def get_system_prompt() -> str:
	with open("prompt.txt", "r", encoding="utf-8") as prompt:
		text = prompt.read()
	return text

def get_memory(phone: str) -> list:
	with pool.get_connection() as connection:
		if not connection.is_connected():
			connection.reconnect()

		with connection.cursor() as cursor:
			cursor.execute("select messages from users where phone = %s", (phone))
			return cursor.fetchall()


def update_memory(phone: str, messages: list) -> None:
	if len(messages) > int(CONFIG["DB_MAX_MESSAGES"]): messages = messages[int(CONFIG["DB_MAX_MESSAGES"]) // 5:]

	with pool.get_connection() as connection:
		if not connection.is_connected():
			connection.reconnect()

		with connection.cursor() as cursor:
			messages_str = json.dumps(messages)
			cursor.execute("UPDATE users SET messages = %s WHERE phone = %s", (messages_str, phone))
			connection.commit()

def generate_gpt_response(history: list[dict]) -> Choice:
	system_message = {"role": "developer", "content": get_system_prompt()}
	if history[0] != system_message: history.insert(0, system_message)
	response = client.chat.completions.create(
		model="gpt-4o",
		messages=history,
		tools=tools,
		tool_choice="auto",
		temperature=0.1
	)
	return response.choices[0]

def call_function(func_name: str, args: dict = {}):
    # !!! ТОЛЬКО МЕТОДЫ ОБЪЕКТА YCLIENTSAPI !!!
	method = getattr(api, func_name, None)
	if method is None or not callable(method):
		return f"Метод `{func_name}` не найден или не является функцией."
	return method(**args)

client = openai.OpenAI(api_key=OPENAI_API_TOKEN)
app = Flask(__name__)

def send_message(phone, text):
	url = f"https://api.green-api.com/waInstance{GREEN_API_ID}/sendMessage/{GREEN_API_TOKEN}"
	payload = {
		"chatId": f"{phone}",
		"message": text
	}
	response = requests.post(url, json=payload)
	logging.info(f"Green API ответ: {response.status_code} - {response.text}")


@app.route("/webhook", methods=["POST"])
def webhook():
	try:
		data = request.get_json()
		logging.info(f"Webhook: {data}")

		if data.get("typeWebhook") != "incomingMessageReceived": return "Ignored", 200
		messageData = data["messageData"]
		typeMessage = messageData.get("typeMessage")

		if typeMessage == "textMessage": message = messageData["textMessageData"]["textMessage"]
		elif typeMessage == "extendedTextMessage": message = messageData["extendedTextMessageData"]["text"]
		else:
			logging.info(f"Unknown message type: {messageData}")
			return "Ignored", 200

		phone = data["senderData"]["chatId"]
		logging.info(f'Входящее сообщение: "{message}" от {phone}')

		history = get_memory(phone)
		history.append({"role": "user", "content": message})
		choice = generate_gpt_response(history)
		history.append(choice.message)
		logging.info(f"--- ОТВЕТ OPENAI ---\n{choice}\n----------------------")

		if choice.finish_reason == "tool_calls":
			for tool_call in choice.message.tool_calls:
				name = tool_call.function.name
				args = json.loads(tool_call.function.arguments)

				result = call_function(name, args)
				history.append({
					"role": "tool",
					"tool_call_id": tool_call.id,
					"content": str(result)
				})
			choice = generate_gpt_response(history)
		send_message(phone, choice.message.content)
		update_memory(phone, history)
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
