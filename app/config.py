import os
from dotenv import load_dotenv
from pathlib import Path

DOTENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=DOTENV_PATH)

class Config:
	GREEN_API_ID = os.getenv("GREEN_API_ID")
	GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")

	OPENAI_API_TOKEN = os.getenv("OPENAI_API_TOKEN")

	YCLIENTS_APPLICATION_ID = os.getenv("YCLIENTS_APPLICATION_ID")
	YCLIENTS_API_TOKEN = os.getenv("YCLIENTS_API_TOKEN")
	YCLIENTS_COMPANY_ID = os.getenv("YCLIENTS_COMPANY_ID")

	FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
	ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
	ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

	DB_USERNAME = os.getenv("DB_USERNAME")
	DB_PASSWORD = os.getenv("DB_PASSWORD")
	DB_HOST = os.getenv("DB_HOST")
	DB_PORT = os.getenv("DB_PORT")
	DB_NAME = os.getenv("DB_NAME")
	DB_MAX_MESSAGES = int(os.getenv("DB_MAX_MESSAGES", "100"))