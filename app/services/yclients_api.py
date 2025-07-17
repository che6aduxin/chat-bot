import json
import requests
from typing import Any
from app.logger import setup_logger
from pathlib import Path

logger = setup_logger("YClients API")
FAQ_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "faq.txt"

class YClientsAPI:
	def __init__(self, bearer_token, company_id):
		self.API_TOKEN_BEARER = bearer_token
		self.COMPANY_ID = company_id
		self.HEADERS = {
			'Content-Type': 'application/json',
			"Accept": "application/vnd.yclients.v2+json",
			"Authorization": f"Bearer {self.API_TOKEN_BEARER}"
		}
		self.URL = "https://api.yclients.com/api/v1"

	def call(self, func_name: str, args: dict = {}) -> Any:
		# !!! ТОЛЬКО МЕТОДЫ ОБЪЕКТА YCLIENTSAPI !!!
		method = getattr(self, func_name, None)
		if method is None or not callable(method):
			logger.error(f"Не найден метод {func_name}")
			return f'Метод "{func_name}" не найден или не является функцией'

		logger.info(f"Вызов метода {func_name} с аргументами {args}")
		return method(**args)

	def get_knowledge_base(self) -> str:
		with open(FAQ_PATH, "r", encoding="utf-8") as faq:
			return faq.read()

	def get_service_categories(self, staff_id: int = 0, datetime: str = "", service_ids: list[int] = list()) -> tuple[tuple[int, str], ...]:
		# Получить все категории услуг
		url = f"{self.URL}/book_services/{self.COMPANY_ID}"
		params = {
			"staff_id": staff_id,
			"datetime": datetime
		}
		if service_ids: params["service_ids"] = service_ids
		data = requests.get(url, headers=self.HEADERS, params=params).json()
		data = data.get("data", {}).get("category", [])
		return tuple((element["id"], element["title"]) for element in data)

	def get_services_list(self, staff_id: int = 0, datetime: str = "", service_ids: list[int] = list()) -> tuple[dict[str, str | int], ...]:
		# Получить список услуг
		url = f"{self.URL}/book_services/{self.COMPANY_ID}"
		params = {
			"staff_id": staff_id,
			"datetime": datetime
		}
		if service_ids: params["service_ids"] = service_ids
		data = requests.get(url, headers=self.HEADERS, params=params).json()
		data = data.get("data", {}).get("services", [])
		return tuple({
			"id": element["id"],
			"title": element["title"],
			"category_id": element["category_id"],
			"price_min": element["price_min"],
			"price_max": element["price_max"],
			"discount": element["discount"],
			"comment": element["comment"],
			"seance_length": element.get("seance_length")
		} for element in data if element["active"])

	def get_staff_list(self, service_ids: list[int] = list(), datetime: str = "") -> tuple[dict[str, str | int], ...]:
		# Получить список сотрудников
		url = f"{self.URL}/book_staff/{self.COMPANY_ID}"
		params = {
			"datetime": datetime
		}
		if service_ids: params["service_ids"] = service_ids # type: ignore
		data = requests.get(url, headers=self.HEADERS, params=params).json()
		data = data.get("data", [])
		return tuple({
			"id": element["id"],
			"name": element["name"],
			"specialization": element["specialization"],
		} for element in data if element["bookable"])

	def get_available_dates(self, staff_id: int = 0, service_ids: list[int] = list(), date: str = "", date_from: str = "", date_to: str = "") -> tuple[str, ...]:
		url = f"{self.URL}/book_dates/{self.COMPANY_ID}"
		params = {
			"staff_id": staff_id,
			"date": date,
			"date_from": date_from,
			"date_to": date_to
		}
		if service_ids: params["service_ids"] = service_ids
		data = requests.get(url, headers=self.HEADERS, params=params).json()
		data = data.get("data", {}).get("booking_days", {})
		return tuple(f"{month}-{day}" for month, days in data.items() for day in days)


	def get_available_times(self, date: str, staff_id: int = 0, service_ids: list[int] = list()) -> tuple[tuple[str, int], ...]:
		url = f"{self.URL}/book_times/{self.COMPANY_ID}/{staff_id}/{date}"
		params = {}
		if service_ids: params["service_ids"] = service_ids
		data = requests.get(url, headers=self.HEADERS, params=params).json()
		data = data.get("data", [])
		return tuple((element["time"], element["seance_length"]) for element in data)

	def book(self, booking_id: int, fullname: str, phone: str, staff_id: int, date_time: str, email: str = "noemail@noemail.com", service_id: int = 0, comment: str = "") -> dict:
		url = f"https://yclients.com/api/v1/book_record/{self.COMPANY_ID}/"
		payload = {
			"phone": phone,
			"fullname": fullname,
			"email": email,
			"comment": comment,
			"notify_by_email": 0,
			"appointments": [{
				"id": booking_id,
				"services": [int(service_id)],
				"staff_id": int(staff_id or 0),
				"datetime": date_time
			}]
		}
		response = requests.post(url, json=payload, headers=self.HEADERS).json()
		return response["data"]

	# TODO: добавить функцию для получения записей клиента