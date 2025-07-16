from flask import Blueprint, request
from app.logger import setup_logger
from app.database import memory
from app.services import openai_service
import json
from app.services.yclients_api import YClientsAPI
from app.config import Config
from app.services.openai_service import generate_gpt_response
from app.services.green_api import send_message

webhook_bp = Blueprint("webhook", __name__)
logger = setup_logger("Webhook")
yclients_api = YClientsAPI(Config.YCLIENTS_API_TOKEN, Config.YCLIENTS_COMPANY_ID)

@webhook_bp.route("/webhook", methods=["POST"])
def webhook():
	try:
		data = request.get_json()
		logger.info(f"Входящий запрос: {data}")

		if data.get("typeWebhook") != "incomingMessageReceived": return "Ignored", 200
		messageData = data["messageData"]
		typeMessage = messageData.get("typeMessage")

		if typeMessage == "textMessage": message = messageData["textMessageData"]["textMessage"]
		elif typeMessage == "extendedTextMessage": message = messageData["extendedTextMessageData"]["text"]
		else:
			logger.warning(f"Неизвестный тип сообщения: {messageData}")
			return "Ignored", 200

		phone = data["senderData"]["chatId"]
		name = data["senderData"]["chatName"]
		logger.info(f'Входящее сообщение: "{message}" от {phone}')

		history = memory.get_memory(phone)
		history.append({"role": "user", "content": message})
		choice = openai_service.generate_gpt_response(history, name, phone)
		history.append(choice.message.model_dump())
		# logger.info(f"Ответ GPT: {choice}") дублируется в openai_service.py

		while choice.finish_reason == "tool_calls":
			for tool_call in choice.message.tool_calls: # type: ignore
				func_name = tool_call.function.name
				args = json.loads(tool_call.function.arguments)

				result = yclients_api.call(func_name, args)
				logger.info(f"Ответ YClients: {result}")
				history.append({
					"role": "tool",
					"tool_call_id": tool_call.id,
					"content": str(result)
				})
			choice = generate_gpt_response(history, name, phone)
			history.append(choice.message.model_dump())
		send_message(phone, choice.message.content) # type: ignore
		memory.update_memory(phone, history)
		return "OK", 200

	except Exception as e:
		logger.exception("Ошибка в webhook:")
		send_message(phone, "Произошла ошибка на сервере, попробуйте позже.") # type: ignore
		return "OK", 200