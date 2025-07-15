import openai
from openai.types.chat.chat_completion import Choice
from pathlib import Path
import json
from app.config import Config
from app.logger import setup_logger

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data"
TOOLS_PATH = DATA_PATH / "tools.json"
PROMPT_PATH = DATA_PATH / "prompt.txt"
with open(TOOLS_PATH, "r", encoding='utf-8') as fn: tools = json.load(fn)
client = openai.OpenAI(api_key=Config.OPENAI_API_TOKEN)
logger = setup_logger("OpenAI")

def get_system_prompt(name: str, phone: str) -> str:
	with open(PROMPT_PATH, "r", encoding="utf-8") as prompt:
		text = prompt.read()
	return text + f"\nИмя клиента: {name}\nТелефон клиента: {phone.replace("@c.us", "")}"

def generate_gpt_response(history: list[dict], name: str, phone: str) -> Choice:
	system_message = {"role": "developer", "content": get_system_prompt(name, phone)}
	if not history or history[0] != system_message: history.insert(0, system_message)
	response = client.chat.completions.create(
		model="gpt-4o",
		messages=history, # type: ignore
		tools=tools,
		tool_choice="auto",
		temperature=0.1
	)
	logger.info(response)
	return response.choices[0]

# TODO: Пофиксить эту ошибку: либо фул очищать историю (легко), либо пробовать ответить на недостающие тулколсы (сложно)
# openai.BadRequestError: Error code: 400 - {'error': {'message': "An assistant message with 'tool_calls' must be followed by tool messages responding to each 'tool_call_id'. The following tool_call_ids did not have response messages: call_GGvLl4teD1eL3xUASYZyVK8O", 'type': 'invalid_request_error', 'param': 'messages.[19].role', 'code': None}}