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

# ===== "Память" на пользователя (простая, volatile, можно улучшить на базе или redis)
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

def book(name, phone, email, service_id, date_time, staff_id, commen_

