"""Сценарий 1 — формирование стартовой пятёрки (раздел 2.4.3).

Система ранжирует доступных игроков по R*_P на их основной позиции и предлагает по
одному игроку с максимальным рейтингом на каждую из пяти позиций, плюс две
альтернативы. Окончательное решение остаётся за тренером.
"""
from __future__ import annotations

from .attributes import POSITIONS

ALTERNATIVES = 2


def suggest_lineup(players: list[dict]) -> dict[str, dict]:
    """Предложение стартовой пятёрки.

    players — список словарей вида {id, name, position, R_star}. Для каждой из пяти
    позиций возвращается основной кандидат (top) и список альтернатив.
    """
    suggestion: dict[str, dict] = {}
    for pos in POSITIONS:
        candidates = sorted(
            (p for p in players if p["position"] == pos),
            key=lambda p: p["R_star"],
            reverse=True,
        )
        if not candidates:
            suggestion[pos] = {"starter": None, "alternatives": []}
            continue
        starter = candidates[0]
        alternatives = candidates[1 : 1 + ALTERNATIVES]
        # Чем меньше разрыв между основным и альтернативой, тем менее однозначен выбор.
        margin = (
            round(starter["R_star"] - alternatives[0]["R_star"], 1)
            if alternatives
            else None
        )
        suggestion[pos] = {
            "starter": starter,
            "alternatives": alternatives,
            "margin": margin,
        }
    return suggestion
