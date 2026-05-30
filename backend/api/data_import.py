"""Ввод данных: ручной ввод и импорт CSV (раздел 2.5.3).

Поддерживаются: ручной ввод сырых показателей и экспертных оценок, импорт CSV с
превью перед записью. API для трекинговых систем архитектурно зарезервирован, но
в рамках апробации не используется (раздел 2.5.3).
"""
import csv
import io
from datetime import date, datetime

from flask import Blueprint, jsonify, request
from flask_login import login_required

from models import db, RawStat, Player, ROLE_HEAD_COACH, ROLE_ASSISTANT, ROLE_ANALYST
from auth import role_required
from core.attributes import ATTRIBUTE_INPUTS, input_schema

data_import_bp = Blueprint("data_import", __name__, url_prefix="/api/data")

EXPERT_LEVEL_TO_SCORE = {1: 33, 2: 48, 3: 63, 4: 78, 5: 93}  # центры диапазонов табл. 6

STAFF = (ROLE_HEAD_COACH, ROLE_ASSISTANT, ROLE_ANALYST)


@data_import_bp.get("/schema")
@role_required(*STAFF)
def schema():
    """Схема формы ввода: атрибуты по категориям с метриками и единицами (табл. 1, 5)."""
    return jsonify(input_schema())


@data_import_bp.post("/raw/batch")
@role_required(*STAFF)
def add_raw_batch():
    """Пакетное сохранение сырых показателей по атрибутам игрока на одну дату.

    Тело: {player_id, date, values: {код атрибута: значение}}. Метрика и тип
    источника по каждому атрибуту берутся из ATTRIBUTE_INPUTS (таблицы 1, 5).
    """
    data = request.get_json(silent=True) or {}
    player = db.session.get(Player, int(data.get("player_id", 0)))
    if player is None:
        return jsonify({"error": "Игрок не найден"}), 404
    try:
        measured_on = datetime.fromisoformat(data.get("date", date.today().isoformat())).date()
    except ValueError:
        return jsonify({"error": "Некорректная дата"}), 400

    values = data.get("values", {}) or {}
    saved, skipped = 0, 0
    for code, raw in values.items():
        if code not in ATTRIBUTE_INPUTS:
            continue
        if raw is None or raw == "":
            skipped += 1            # незаполненные поля пропускаем
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            return jsonify({"error": f"Некорректное значение по атрибуту {code}"}), 400
        meta = ATTRIBUTE_INPUTS[code]
        db.session.add(RawStat(
            player_id=player.id,
            measured_on=measured_on,
            source_type=meta["source_type"],
            metric=f"{code}: {meta['metric']}",
            value=value,
        ))
        saved += 1

    if saved == 0:
        return jsonify({"error": "Не заполнено ни одного поля"}), 400
    db.session.commit()
    return jsonify({"saved": saved, "skipped": skipped})


@data_import_bp.post("/raw")
@role_required(ROLE_HEAD_COACH, ROLE_ASSISTANT, ROLE_ANALYST)
def add_raw():
    """Ручной ввод одного сырого показателя."""
    data = request.get_json(silent=True) or {}
    try:
        stat = RawStat(
            player_id=int(data["player_id"]),
            measured_on=datetime.fromisoformat(data.get("date", date.today().isoformat())).date(),
            source_type=int(data["source_type"]),
            metric=str(data["metric"]),
            value=float(data["value"]),
        )
    except (KeyError, ValueError) as exc:
        return jsonify({"error": f"Некорректные данные: {exc}"}), 400
    db.session.add(stat)
    db.session.commit()
    return jsonify({"id": stat.id, "ok": True})


@data_import_bp.post("/import/preview")
@role_required(ROLE_HEAD_COACH, ROLE_ASSISTANT, ROLE_ANALYST)
def import_preview():
    """Превью импорта CSV перед записью в БД (раздел 2.5.3).

    Ожидаемые колонки: player_id, date, source_type, metric, value.
    """
    raw = request.get_data(as_text=True)
    reader = csv.DictReader(io.StringIO(raw))
    rows, errors = [], []
    for i, row in enumerate(reader, start=1):
        try:
            rows.append(
                {
                    "player_id": int(row["player_id"]),
                    "date": row.get("date", date.today().isoformat()),
                    "source_type": int(row["source_type"]),
                    "metric": row["metric"],
                    "value": float(row["value"]),
                }
            )
        except (KeyError, ValueError) as exc:
            errors.append({"line": i, "error": str(exc)})
    return jsonify({"rows": rows, "errors": errors, "valid": len(rows), "invalid": len(errors)})
