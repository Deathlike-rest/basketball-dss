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


# --- Импорт матчевого протокола (box score), раздел 2.5.3 ---
# Колонки строки протокола игры (тип 1 — официальная матчевая статистика, 2.3.1).
BOX_FIELDS = ["minutes", "pts", "fgm", "fga", "tpm", "tpa", "ftm", "fta",
              "oreb", "dreb", "ast", "tov", "stl", "blk", "pf"]
# Сопоставление колонок с именами показателей, под которыми они кладутся в БД.
METRIC_NAMES = {
    "minutes": "MIN", "pts": "PTS", "fgm": "FGM", "fga": "FGA", "tpm": "3PM",
    "tpa": "3PA", "ftm": "FTM", "fta": "FTA", "oreb": "OREB", "dreb": "DREB",
    "ast": "AST", "tov": "TOV", "stl": "STL", "blk": "BLK", "pf": "PF",
}
# Счётные показатели, которых не может быть при нуле сыгранных минут (валидация 2.4.1).
_COUNTING = ["pts", "oreb", "dreb", "ast", "stl", "blk", "fga", "fta", "tov"]


def _parse_match_csv(raw: str) -> list[dict]:
    """Разбор CSV-протокола игры: сопоставление игроков по id/имени и валидация.

    Возвращает список строк с computed-показателями, статусом сопоставления и
    списком ошибок. Запись в БД здесь не производится — только разбор.
    """
    reader = csv.DictReader(io.StringIO(raw))
    rows = []
    for i, raw_row in enumerate(reader, start=1):
        r = {(k or "").strip().lower(): (v or "").strip() for k, v in raw_row.items()}
        entry: dict = {"line": i, "errors": []}

        # Автосопоставление игрока: сначала по player_id, затем по ФИО.
        player = None
        pid = r.get("player_id")
        if pid:
            try:
                player = db.session.get(Player, int(pid))
            except ValueError:
                entry["errors"].append("player_id не число")
        if player is None and r.get("player_name"):
            player = Player.query.filter_by(full_name=r["player_name"]).first()
        if player is None:
            entry["errors"].append("игрок не найден")
        entry["player_id"] = player.id if player else None
        entry["player_name"] = player.full_name if player else (r.get("player_name") or pid or "—")

        # Разбор числовых полей box score.
        vals: dict[str, float] = {}
        for f in BOX_FIELDS:
            s = r.get(f, "")
            if s == "":
                vals[f] = 0.0
                continue
            try:
                x = float(s.replace(",", "."))
                if x < 0:
                    entry["errors"].append(f"{METRIC_NAMES[f]} < 0")
                vals[f] = x
            except ValueError:
                entry["errors"].append(f"{METRIC_NAMES[f]}: не число")
                vals[f] = 0.0

        # Проверки согласованности (этап 2 алгоритма, раздел 2.4.1).
        if vals["fgm"] > vals["fga"]:
            entry["errors"].append("реализованных бросков больше, чем попыток (FGM > FGA)")
        if vals["tpm"] > vals["tpa"]:
            entry["errors"].append("3PM > 3PA")
        if vals["ftm"] > vals["fta"]:
            entry["errors"].append("FTM > FTA")
        if vals["tpm"] > vals["fgm"]:
            entry["errors"].append("трёхочковых больше, чем всех попаданий (3PM > FGM)")
        if vals["minutes"] == 0 and any(vals[f] > 0 for f in _COUNTING):
            entry["errors"].append("0 минут на площадке, но есть статистика")

        entry["stats"] = vals
        entry["fg_pct"] = round(vals["fgm"] / vals["fga"] * 100, 1) if vals["fga"] else None
        entry["tp_pct"] = round(vals["tpm"] / vals["tpa"] * 100, 1) if vals["tpa"] else None
        entry["ft_pct"] = round(vals["ftm"] / vals["fta"] * 100, 1) if vals["fta"] else None
        entry["valid"] = player is not None and not entry["errors"]
        rows.append(entry)
    return rows


def _summary(rows: list[dict]) -> dict:
    valid = sum(1 for r in rows if r["valid"])
    return {"total": len(rows), "valid": valid, "invalid": len(rows) - valid}


@data_import_bp.post("/import/match/preview")
@role_required(*STAFF)
def match_preview():
    """Превью импорта матчевого протокола перед записью в БД (раздел 2.5.3)."""
    rows = _parse_match_csv(request.get_data(as_text=True))
    return jsonify({"rows": rows, "summary": _summary(rows)})


@data_import_bp.post("/import/match/commit")
@role_required(*STAFF)
def match_commit():
    """Запись матчевого протокола: по каждому сопоставленному игроку — сырые
    показатели игры (source_type=1) с датой матча. Невалидные строки пропускаются.

    Тело: {date, opponent, csv}.
    """
    data = request.get_json(silent=True) or {}
    try:
        match_date = datetime.fromisoformat(
            data.get("date", date.today().isoformat())
        ).date()
    except ValueError:
        return jsonify({"error": "Некорректная дата матча"}), 400

    rows = _parse_match_csv(data.get("csv", ""))
    saved_players, saved_metrics = 0, 0
    for row in rows:
        if not row["valid"]:
            continue
        for f in BOX_FIELDS:
            db.session.add(RawStat(
                player_id=row["player_id"],
                measured_on=match_date,
                source_type=1,  # официальная матчевая статистика
                metric=METRIC_NAMES[f],
                value=row["stats"][f],
            ))
            saved_metrics += 1
        saved_players += 1

    if saved_players == 0:
        return jsonify({"error": "Нет валидных строк для импорта", "summary": _summary(rows)}), 400
    db.session.commit()
    return jsonify({
        "saved_players": saved_players,
        "saved_metrics": saved_metrics,
        "summary": _summary(rows),
    })
