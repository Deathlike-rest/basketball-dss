"""Аутентификация и авторизация (раздел 2.5.4 диссертации).

Аутентификация по паре «логин/пароль» с хэшированием bcrypt. Авторизация на
основе ролей: права проверяются на каждом запросе декоратором @role_required.
"""
from functools import wraps

import bcrypt
from flask import Blueprint, jsonify, request
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from models import User, db, ROLE_HEAD_COACH, ROLE_ASSISTANT, ROLE_ANALYST

login_manager = LoginManager()
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({"error": "Требуется аутентификация"}), 401


def hash_password(plain: str) -> bytes:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt())


def verify_password(plain: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed)


def role_required(*roles: str):
    """Доступ к эндпоинту только для пользователей с одной из перечисленных ролей."""
    def decorator(fn):
        @wraps(fn)
        @login_required
        def wrapper(*args, **kwargs):
            if current_user.role not in roles:
                return jsonify({"error": "Недостаточно прав"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# Роли, входящие в тренерский штаб (видят данные всех игроков).
STAFF_ROLES = (ROLE_HEAD_COACH, ROLE_ASSISTANT, ROLE_ANALYST)


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    user = User.query.filter_by(login=data.get("login", "")).first()
    if user is None or not verify_password(data.get("password", ""), user.password_hash):
        return jsonify({"error": "Неверный логин или пароль"}), 401
    login_user(user)
    return jsonify(_user_payload(user))


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"ok": True})


@auth_bp.get("/me")
@login_required
def me():
    return jsonify(_user_payload(current_user))


def _user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "login": user.login,
        "full_name": user.full_name,
        "role": user.role,
        "player_id": user.player_id,
    }
