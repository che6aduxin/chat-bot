from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from app.logger import setup_logger
from app.database import memory
from app.config import Config
from pathlib import Path
import os
from app.database import memory

admin_bp = Blueprint("admin", __name__)
logger = setup_logger("Admin panel")
PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "prompt.txt"

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
	if request.method == "POST":
		username = request.form.get("username")
		password = request.form.get("password")

		if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
			session["logged_in"] = True
			logger.info("Успешный вход администратора")
			return redirect(url_for("admin.prompt"))
		else:
			logger.warning(f"Неудачная попытка входа: {username}")
			flash("Неверные данные")
	return render_template("login.html")

@admin_bp.route("/admin/prompt", methods=["GET", "POST"])
def prompt():
	if not session.get("logged_in"):
		return redirect(url_for("admin.login"))

	if request.method == "POST":
		new_text = request.form.get("text")
		with open(PROMPT_PATH, "w", encoding="utf-8") as prompt:
			prompt.write(new_text) # type: ignore
		flash("Текст обновлён")
		logger.info("Промпт обновлён администратором")
		return redirect(url_for("admin.prompt"))

	if os.path.exists(PROMPT_PATH):
		with open(PROMPT_PATH, "r", encoding="utf-8") as prompt:
			current_text = prompt.read()
	else:
		current_text = ""

	return render_template("prompt.html", text=current_text)

@admin_bp.route("/admin/users", methods=["GET", "POST"])
def users():
	if not session.get("logged_in"):
		return redirect(url_for("admin.login"))

	phones = memory.get_all_users()
	selected = request.args.get("phone")
	messages = None
	if selected: messages = memory.get_memory(selected)

	if request.method == "POST" and request.form.get("action") == "clear":
		if selected:
			memory.update_memory(selected, [])
			flash(f"История пользователя {selected} очищена")
			logger.info(f"История {selected} очищена")

		return redirect(url_for("admin.users", phone=selected))

	return render_template("users.html", phones=phones, messages=messages, selected=selected)