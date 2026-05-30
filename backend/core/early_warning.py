"""Сценарий 3 — раннее предупреждение (раздел 2.4.3).

Система отслеживает динамику атрибутов и сигнализирует при резком падении балла,
особенно атлетических. Алгоритм: значение за последний период сравнивается со
скользящим средним за предыдущие 3–4 периода; порог срабатывания — снижение более
чем на одно стандартное отклонение.
"""
from __future__ import annotations

import numpy as np

from .attributes import category_of, name_of

DEFAULT_WINDOW = 4
DEFAULT_SIGMA = 1.0
MIN_ABS_DROP = 2.0   # минимальное абсолютное падение, чтобы отсечь шум округления баллов
ATHLETIC = "Атлетизм"


def detect_drop(
    history: list[float],
    *,
    window: int = DEFAULT_WINDOW,
    sigma_threshold: float = DEFAULT_SIGMA,
) -> dict | None:
    """Проверка одного временного ряда баллов атрибута на резкое падение.

    history — упорядоченный по времени список баллов; последний элемент — текущий
    период. Возвращает описание срабатывания либо None.
    """
    if len(history) < window + 1:
        return None

    previous = np.asarray(history[-(window + 1):-1], dtype=float)
    current = float(history[-1])
    baseline = float(np.mean(previous))
    std = float(np.std(previous, ddof=0))

    drop = baseline - current
    # Падение меньше порога абсолютного спада считаем шумом (округление баллов до целого).
    if drop < MIN_ABS_DROP:
        return None
    if std == 0:
        # Без разброса любое падение формально превышает 0σ; ориентируемся на абсолютный спад.
        triggered = True
        sigma = float("inf")
    else:
        sigma = drop / std
        triggered = sigma > sigma_threshold

    if not triggered:
        return None
    return {
        "baseline": round(baseline, 1),
        "current": round(current, 1),
        "drop": round(drop, 1),
        "sigma": round(sigma, 2) if std != 0 else None,
    }


def scan_player(
    attribute_histories: dict[str, list[float]],
    *,
    window: int = DEFAULT_WINDOW,
    sigma_threshold: float = DEFAULT_SIGMA,
) -> list[dict]:
    """Проверка всех атрибутов игрока. Возвращает список предупреждений.

    Атлетические атрибуты помечаются повышенным приоритетом: их резкое снижение
    часто служит ранним индикатором усталости или скрытой травмы.
    """
    alerts = []
    for code, history in attribute_histories.items():
        hit = detect_drop(history, window=window, sigma_threshold=sigma_threshold)
        if hit is None:
            continue
        is_athletic = category_of(code) == ATHLETIC
        alerts.append(
            {
                "attribute": code,
                "name": name_of(code),
                "category": category_of(code),
                "priority": "high" if is_athletic else "normal",
                **hit,
            }
        )
    # Сначала атлетические (high), затем по величине падения.
    alerts.sort(key=lambda a: (a["priority"] != "high", -a["drop"]))
    return alerts
