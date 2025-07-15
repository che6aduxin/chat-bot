from app.config import Config
from app.logger import setup_logger
import requests

logger = setup_logger("Green API")

def send_message(phone: str, text: str) -> None:
	url = f"https://api.green-api.com/waInstance{Config.GREEN_API_ID}/sendMessage/{Config.GREEN_API_TOKEN}"
	payload = {
		"chatId": phone,
		"message": text
	}
	headers = {
		"Content-Type": "application/json"
	}

	response = requests.post(url, headers=headers, json=payload)
	logger.info(f"Code: {response.status_code}; Body: {response.json()}")
