from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from app.logger import setup_logger
from app.database import memory
from app.config import Config
from pathlib import Path
import os

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

    return render_template("admin.html", text=current_text)

@admin_bp.route("/admin/users", methods=["GET"])
def users():
    if not session.get("logged_in"):
        return redirect(url_for("admin.login"))


    selected = request.args.get("phone")
    messages = None

    return render_template("users.html", phones=[1,2,3], messages=messages, selected=selected)