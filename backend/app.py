"""Точка входа Flask-приложения (фабрика приложения).

Трёхуровневая архитектура (раздел 2.5.1): клиент (Vue) — сервер приложения
(Flask, этот слой) — база данных (PostgreSQL). Здесь регистрируются blueprints
с бизнес-логикой и алгоритмическими компонентами из core/.
"""
from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from models import db
from auth import login_manager, auth_bp


def create_app(config_object: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    login_manager.init_app(app)
    # Куки сессии между фронтом (Vite) и API.
    CORS(app, supports_credentials=True, origins=["http://localhost:5173", "http://localhost:8080"])

    app.register_blueprint(auth_bp)

    from api.players import players_bp
    from api.ratings import ratings_bp
    from api.lineup import lineup_bp
    from api.recommendations import recommendations_bp
    from api.alerts import alerts_bp
    from api.data_import import data_import_bp
    from api.export import export_bp

    for bp in (players_bp, ratings_bp, lineup_bp, recommendations_bp, alerts_bp, data_import_bp, export_bp):
        app.register_blueprint(bp)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    return app


app = create_app()


if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
