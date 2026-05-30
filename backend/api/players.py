"""Игроки и карточка игрока (раздел 2.5.2).

Карточка игрока — пять вкладок: Профиль, Атрибуты, История, Рекомендации, Данные.
Роль «Игрок» видит только свой профиль; вкладка «Данные» — только для штаба.
"""
from flask import Blueprint, jsonify, abort
from flask_login import current_user, login_required

from models import Player, PlayerMeasurement, AttributeScore, RawStat, ROLE_PLAYER
from auth import STAFF_ROLES
from core.attributes import ATTRIBUTES, name_of, category_of, attributes_by_category, POSITION_NAMES
import services

players_bp = Blueprint("players", __name__, url_prefix="/api/players")


def _ensure_can_view(player_id: int) -> None:
    """Игрок видит только себя; штаб видит всех (раздел 2.5.2)."""
    if current_user.role == ROLE_PLAYER and current_user.player_id != player_id:
        abort(403)


@players_bp.get("")
@login_required
def list_players():
    # Игроку список команды недоступен — только свой профиль.
    if current_user.role == ROLE_PLAYER:
        return jsonify([_brief(Player.query.get_or_404(current_user.player_id))])
    return jsonify([_brief(p) for p in Player.query.order_by(Player.full_name).all()])


@players_bp.get("/<int:player_id>")
@login_required
def get_player(player_id: int):
    _ensure_can_view(player_id)
    player = Player.query.get_or_404(player_id)
    is_staff = current_user.role in STAFF_ROLES
    payload = {
        "profile": _profile(player),
        "attributes": _attributes_tab(player),
        "history": _history_tab(player),
        "recommendations": services.player_recommendations(player),
    }
    if is_staff:
        payload["data"] = _data_tab(player)  # вкладка «Данные» — только штаб
    return jsonify(payload)


def _brief(player: Player) -> dict:
    rating = services.latest_rating(player.id)
    return {
        "id": player.id,
        "full_name": player.full_name,
        "position": player.primary_position,
        "position_name": POSITION_NAMES.get(player.primary_position),
        "R_star": rating.r_star if rating else None,
        "trend": services.rating_trend(player.id),
    }


def _profile(player: Player) -> dict:
    latest_m = (
        PlayerMeasurement.query.filter_by(player_id=player.id)
        .order_by(PlayerMeasurement.measured_on.desc())
        .first()
    )
    return {
        "id": player.id,
        "full_name": player.full_name,
        "birth_date": player.birth_date.isoformat() if player.birth_date else None,
        "primary_position": player.primary_position,
        "position_name": POSITION_NAMES.get(player.primary_position),
        "secondary_positions": player.secondary_positions,
        "team": player.team,
        "height_cm": latest_m.height_cm if latest_m else None,
        "weight_kg": latest_m.weight_kg if latest_m else None,
        "wingspan_cm": latest_m.wingspan_cm if latest_m else None,
        "consent_signed": player.consent_signed,
    }


def _attributes_tab(player: Player) -> dict:
    """Радар по 21 атрибуту + таблица с процентилями, сгруппировано по категориям."""
    scores = services.latest_scores(player.id)
    rows = []
    for code in ATTRIBUTES:
        latest = (
            AttributeScore.query.filter_by(player_id=player.id, attribute_code=code)
            .order_by(AttributeScore.computed_on.desc())
            .first()
        )
        rows.append(
            {
                "code": code,
                "name": name_of(code),
                "category": category_of(code),
                "score": scores.get(code),
                "percentile": latest.percentile if latest else None,
                "is_indicative": latest.is_indicative if latest else None,
            }
        )
    rating = services.compute_player_rating(player)
    return {
        "by_category": attributes_by_category(),
        "rows": rows,
        "rating": rating,
    }


def _history_tab(player: Player) -> dict:
    """Динамика рейтинга и баллов атрибутов за период."""
    from models import Rating

    ratings = (
        Rating.query.filter_by(player_id=player.id)
        .order_by(Rating.computed_on.asc())
        .all()
    )
    return {
        "ratings": [
            {"date": r.computed_on.isoformat(), "R_P": r.r_p, "R_star": r.r_star}
            for r in ratings
        ],
        "attribute_history": services.score_history(player.id),
    }


def _data_tab(player: Player) -> list[dict]:
    """Детальные сырые показатели (только для тренерского штаба)."""
    rows = (
        RawStat.query.filter_by(player_id=player.id)
        .order_by(RawStat.measured_on.desc())
        .all()
    )
    return [
        {
            "date": r.measured_on.isoformat(),
            "source_type": r.source_type,
            "metric": r.metric,
            "value": r.value,
        }
        for r in rows
    ]
