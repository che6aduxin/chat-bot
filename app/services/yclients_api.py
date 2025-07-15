import json
import requests
from typing import Any
from app.logger import setup_logger

logger = setup_logger("YClients API")

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

	def get_service_categories(self, staff_id: int = 0, datetime: str = "", service_ids: list = list()) -> list:
		# Получить все категории услуг
		url = f"{self.URL}/book_services/{self.COMPANY_ID}"
		params = {
			"staff_id": staff_id,
			"datetime": datetime
		}
		if service_ids: params["service_ids"] = service_ids
		resp = requests.get(url, headers=self.HEADERS, params=params)
		return resp.json()["data"]["category"]

	def get_services_list(self, staff_id: int = 0, datetime: str = "", service_ids: list[int] = list()) -> list:
		# Получить список услуг
		url = f"{self.URL}/book_services/{self.COMPANY_ID}"
		params = {
			"staff_id": staff_id,
			"datetime": datetime
		}
		if service_ids: params["service_ids"] = service_ids
		resp = requests.get(url, headers=self.HEADERS, params=params)
		return resp.json()["data"]["services"]

	def get_staff_list(self, service_ids: list[int] = list(), datetime: str = "") -> list:
		# Получить список сотрудников
		url = f"{self.URL}/book_staff/{self.COMPANY_ID}"
		params = {
			"datetime": datetime
		}
		if service_ids: params["service_ids"] = service_ids # type: ignore
		resp = requests.get(url, headers=self.HEADERS, params=params)
		return resp.json()["data"]

	def get_available_dates(self, staff_id: int = 0, service_ids: list[int] = list(), date: str = "", date_from: str = "", date_to: str = ""):
		url = f"{self.URL}/book_dates/{self.COMPANY_ID}"
		params = {
			"staff_id": staff_id,
			"date": date,
			"date_from": date_from,
			"date_to": date_to
		}
		if service_ids: params["service_ids"] = service_ids
		resp = requests.get(url, headers=self.HEADERS, params=params)
		return resp.json()["data"]

	def get_available_times(self, date: str, staff_id: int = 0, service_ids: list[int] = list()):
		url = f"{self.URL}/book_times/{self.COMPANY_ID}/{staff_id}/{date}"
		params = {}
		if service_ids: params["service_ids"] = service_ids
		resp = requests.get(url, headers=self.HEADERS, params=params)
		return resp.json()["data"]

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
		response = requests.post(url, json=payload, headers=self.HEADERS)
		return response.json()

	# TODO: добавить функцию для получения записей клиента