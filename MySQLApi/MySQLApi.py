import mysql.connector as mysql
import json


class Database:
	def __init__(self, user: str, password: str):
		config = {
			"user": user,
			"password": password,
		}
		self.pool = mysql.pooling.MySQLConnectionPool(
			pool_name="main_pool", pool_size=5, pool_reset_session=True, **config)


	def create_database(self, database_name: str):
		with self.pool.get_connection() as connection:
			with connection.cursor() as cursor:
				cursor.execute(f"CREATE DATABASE {database_name}")
