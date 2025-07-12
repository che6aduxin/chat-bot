import json
import requests

class YClientsAPI:
	def __init__(self, bearer_token, user_token, company_id):
		self.API_TOKEN_BEARER = bearer_token
		self.API_TOKEN_USER = user_token
		self.COMPANY_ID = company_id
		self.HEADERS = {
			'Content-Type': 'application/json',
			"Accept": "application/vnd.yclients.v2+json",
			"Authorization": f"Bearer {self.API_TOKEN_BEARER}, User {self.API_TOKEN_USER}"
		}
		self.URL = "https://api.yclients.com/api/v1"

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
		if service_ids: params["service_ids"] = service_ids
		resp = requests.get(url, headers=self.HEADERS, params=params)
		return resp.json()["data"]

	def get_service_info(self, service_id: int, staff_id: int = 0, category_id: int = 0):
		url = f"{self.URL}/company/{self.COMPANY_ID}/services/{service_id}"
		params = {
			"staff_id": staff_id,
			"category_id": category_id
		}
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