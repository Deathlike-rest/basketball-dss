"""Сценарий 3 — лента раннего предупреждения (раздел 2.4.3).

Доступна тренерскому штабу. Срабатывания вычисляются по динамике атрибутов
«на лету»; статусы (подтверждено / частично / ложная тревога) штаб проставляет
ретроспективно (раздел 3.5).
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required

from models import db, Alert
from auth import role_required, STAFF_ROLES
import services

alerts_bp = Blueprint("alerts", __name__, url_prefix="/api/alerts")


@alerts_bp.get("/feed")
@role_required(*STAFF_ROLES)
def feed():
    """Лента предупреждений по всей команде (динамический расчёт)."""
    return jsonify(services.all_alerts())


@alerts_bp.post("/<int:alert_id>/status")
@role_required(*STAFF_ROLES)
def set_status(alert_id: int):
    """Ретроспективная оценка предупреждения (раздел 3.5)."""
    alert = Alert.query.get_or_404(alert_id)
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in {"new", "confirmed", "partial", "false_alarm"}:
        return jsonify({"error": "Недопустимый статус"}), 400
    alert.status = status
    db.session.commit()
    return jsonify({"id": alert.id, "status": alert.status})
