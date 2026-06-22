"""Сервисный слой: связывает данные из БД с алгоритмическим ядром core/.

Здесь собирается воедино то, что в диссертации описано как этапы 3–7 алгоритма
работы СППР (раздел 2.4.1): из балльных значений атрибутов считаются интегральные
рейтинги, формируются предложения состава, рекомендации и предупреждения.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import date

from models import (
    db,
    Player,
    AttributeScore,
    Rating,
    ReferenceSample,
)
from core import rating as rating_core
from core import normalize as normalize_core
from core.lineup import suggest_lineup
from core.recommendations import recommend, team_position_averages
from core.early_warning import scan_player
from core.attributes import WEIGHTED_ATTRIBUTES


def latest_scores(player_id: int) -> dict[str, float]:
    """Последний по дате балл по каждому атрибуту игрока."""
    rows = (
        AttributeScore.query.filter_by(player_id=player_id)
        .order_by(AttributeScore.computed_on.asc())
        .all()
    )
    scores: dict[str, float] = {}
    for row in rows:  # перезаписываем — остаётся самый поздний
        scores[row.attribute_code] = row.score
    return scores


def score_history(player_id: int) -> dict[str, list[float]]:
    """Хронологический ряд баллов по каждому атрибуту (для динамики и предупреждений)."""
    rows = (
        AttributeScore.query.filter_by(player_id=player_id)
        .order_by(AttributeScore.computed_on.asc())
        .all()
    )
    hist: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        hist[row.attribute_code].append(row.score)
    return dict(hist)


def latest_rating(player_id: int) -> Rating | None:
    return (
        Rating.query.filter_by(player_id=player_id)
        .order_by(Rating.computed_on.desc())
        .first()
    )


def compute_player_rating(player: Player) -> dict:
    """Полный рейтинг игрока на основной позиции + вектор позиций + модификаторы."""
    scores = latest_scores(player.id)
    rating_row = latest_rating(player.id)
    m_iq = rating_row.m_iq if rating_row else 0
    m_s = rating_row.m_s if rating_row else 0
    m_l = rating_row.m_l if rating_row else 0
    result = rating_core.full_rating(scores, player.primary_position, m_iq, m_s, m_l)
    result["player_id"] = player.id
    result["name"] = player.full_name
    return result


def rating_trend(player_id: int) -> str:
    """Стрелка тренда для дашборда: сравнение двух последних рейтингов."""
    rows = (
        Rating.query.filter_by(player_id=player_id)
        .order_by(Rating.computed_on.desc())
        .limit(2)
        .all()
    )
    if len(rows) < 2:
        return "flat"
    if rows[0].r_star > rows[1].r_star:
        return "up"
    if rows[0].r_star < rows[1].r_star:
        return "down"
    return "flat"


def team_overview() -> list[dict]:
    """Список игроков команды с R* и трендом — для экрана тренера (раздел 2.5.2)."""
    overview = []
    for player in Player.query.order_by(Player.full_name).all():
        try:
            r = compute_player_rating(player)
        except ValueError:
            continue
        overview.append(
            {
                "player_id": player.id,
                "name": player.full_name,
                "position": player.primary_position,
                "R_P": r["R_P"],
                "R_star": r["R_star"],
                "M_IQ": r["modifiers"]["M_IQ"],
                "M_S": r["modifiers"]["M_S"],
                "M_L": r["modifiers"]["M_L"],
                "trend": rating_trend(player.id),
            }
        )
    return overview


def suggested_lineup() -> dict:
    players = [
        {
            "id": o["player_id"],
            "name": o["name"],
            "position": o["position"],
            "R_star": o["R_star"],
        }
        for o in team_overview()
    ]
    return suggest_lineup(players)


def player_recommendations(player: Player) -> list[dict]:
    """Сценарий 2: сравнение с одногруппниками по позиции в команде."""
    teammates = [
        p for p in Player.query.filter_by(primary_position=player.primary_position).all()
    ]
    team_scores = [latest_scores(p.id) for p in teammates]
    averages = team_position_averages(team_scores)
    return recommend(latest_scores(player.id), averages)


def player_alerts(player: Player) -> list[dict]:
    """Сценарий 3: сканирование динамики атрибутов игрока."""
    return scan_player(score_history(player.id))


def all_alerts() -> list[dict]:
    """Лента предупреждений по всей команде — для дашборда тренера."""
    feed = []
    for player in Player.query.all():
        for alert in player_alerts(player):
            # alert уже содержит "name" = название атрибута; имя игрока кладём отдельно.
            feed.append({"player_id": player.id, "player_name": player.full_name, **alert})
    feed.sort(key=lambda a: (a["priority"] != "high", -a["drop"]))
    return feed
