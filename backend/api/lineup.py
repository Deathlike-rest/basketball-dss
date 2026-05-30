"""Сценарий 1 — стартовая пятёрка (раздел 2.4.3).

Предложение состава доступно штабу; утвердить пятёрку на матч может только
главный тренер (раздел 2.5.2).
"""
import json
from datetime import date, datetime

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from models import db, Lineup, ROLE_HEAD_COACH
from auth import role_required
import services

lineup_bp = Blueprint("lineup", __name__, url_prefix="/api/lineup")


@lineup_bp.get("/suggestion")
@login_required
def suggestion():
    return jsonify(services.suggested_lineup())


@lineup_bp.post("/approve")
@role_required(ROLE_HEAD_COACH)
def approve():
    """Утверждение стартовой пятёрки на матч (фиксируется для анализа по разделу 3.4)."""
    data = request.get_json(silent=True) or {}
    player_ids = data.get("player_ids", [])
    if len(player_ids) != 5:
        return jsonify({"error": "Стартовая пятёрка должна содержать 5 игроков"}), 400

    match_date = data.get("match_date")
    lineup = Lineup(
        match_date=datetime.fromisoformat(match_date).date() if match_date else date.today(),
        opponent=data.get("opponent"),
        approved_by=current_user.id,
        matches_system_suggestion=bool(data.get("matches_system_suggestion", True)),
        player_ids_json=json.dumps(player_ids),
    )
    db.session.add(lineup)
    db.session.commit()
    return jsonify({"id": lineup.id, "ok": True})


@lineup_bp.get("/history")
@login_required
def history():
    rows = Lineup.query.order_by(Lineup.match_date.desc()).all()
    return jsonify(
        [
            {
                "id": r.id,
                "match_date": r.match_date.isoformat(),
                "opponent": r.opponent,
                "matches_system_suggestion": r.matches_system_suggestion,
                "result_win": r.result_win,
                "point_diff": r.point_diff,
                "player_ids": json.loads(r.player_ids_json) if r.player_ids_json else [],
            }
            for r in rows
        ]
    )
