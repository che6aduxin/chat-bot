from flask import Flask
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.secret_key = Config.FLASK_SECRET_KEY

    from app.routes.webhook import webhook_bp
    from app.routes.admin import admin_bp
    app.register_blueprint(webhook_bp)
    app.register_blueprint(admin_bp)

    return app
