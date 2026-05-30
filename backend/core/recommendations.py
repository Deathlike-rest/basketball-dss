"""Сценарий 2 — индивидуальные рекомендации по тренировке (раздел 2.4.3).

Для игрока строится профиль по 21 атрибуту. Атрибуты, оцененные ниже среднего по
его позиции в данной команде, помечаются; по ним из справочника упражнений
формируется список из 3–5 приоритетных направлений индивидуальной работы.
"""
from __future__ import annotations

from statistics import mean

from .attributes import WEIGHTED_ATTRIBUTES, name_of, category_of
from .exercises import exercises_for

MAX_PRIORITIES = 5


def team_position_averages(
    team_scores: list[dict[str, float]],
) -> dict[str, float]:
    """Средние баллы по каждому атрибуту среди игроков одной позиции в команде."""
    averages: dict[str, float] = {}
    for code in WEIGHTED_ATTRIBUTES:
        values = [s[code] for s in team_scores if code in s and s[code] is not None]
        if values:
            averages[code] = mean(values)
    return averages


def recommend(
    player_scores: dict[str, float],
    position_averages: dict[str, float],
    *,
    max_items: int = MAX_PRIORITIES,
) -> list[dict]:
    """Список приоритетных направлений работы, отсортированный по отставанию.

    Берутся атрибуты, по которым балл игрока ниже среднего по позиции в команде;
    сортировка по величине отставания (сначала самые проблемные); не более max_items.
    """
    gaps = []
    for code in WEIGHTED_ATTRIBUTES:
        avg = position_averages.get(code)
        player = player_scores.get(code)
        if avg is None or player is None:
            continue
        if player < avg:
            gaps.append(
                {
                    "attribute": code,
                    "name": name_of(code),
                    "category": category_of(code),
                    "score": round(player, 1),
                    "team_avg": round(avg, 1),
                    "gap": round(avg - player, 1),
                    "exercises": exercises_for(code),
                }
            )
    gaps.sort(key=lambda x: x["gap"], reverse=True)
    return gaps[:max_items]
