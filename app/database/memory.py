import mysql.connector as mysql
import json
from app.config import Config
from app.logger import setup_logger

db_config = {
	"user": Config.DB_USERNAME,
	"password": Config.DB_PASSWORD,
	"host": Config.DB_HOST,
	"port": Config.DB_PORT,
	"database": Config.DB_NAME
}

pool = mysql.pooling.MySQLConnectionPool(
	pool_name="main_pool",
	pool_size=5,
	pool_reset_session=True,
	**db_config
)

logger = setup_logger("Memory")

def get_memory(phone: str) -> list:
	logger.info(f"Получена история от {phone}")
	with pool.get_connection() as connection:
		if not connection.is_connected():
			connection.reconnect()

		with connection.cursor() as cursor:
			cursor.execute("select messages from users where phone = %s", (phone,))
			result = cursor.fetchone()
		if result and result[0]:
			try:
				return json.loads(result[0])
			except json.JSONDecodeError:
				logger.warning("messages повреждены, возвращаем []")
				return list()
		return list()


def update_memory(phone: str, messages: list) -> None:
	logger.info(f"Обновление истории у {phone}")
	if len(messages) > Config.DB_MAX_MESSAGES: messages = messages[Config.DB_MAX_MESSAGES // 5:]

	with pool.get_connection() as connection:
		if not connection.is_connected():
			connection.reconnect()

		with connection.cursor() as cursor:
			messages_str = json.dumps(messages)
			cursor.execute("REPLACE INTO users(phone, messages) VALUES (%s, %s)", (phone, messages_str))
			connection.commit()