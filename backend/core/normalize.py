"""Нормализация сырых данных в шкалу 25–99 (раздел 2.2.6 диссертации).

Процедура состоит из трёх шагов:
  Шаг 1 — процентиль p(x) относительно референтной выборки.
  Шаг 2 — линейный перевод A = 25 + 0,74·p(x).
  Шаг 3 — контекстные правки (соперники, USG, тренд), результат зажимается в [25; 99].
"""
from __future__ import annotations

import numpy as np

SCALE_MIN = 25
SCALE_MAX = 99
INTERCEPT = 25.0
SLOPE = 0.74
REF_SAMPLE_MIN = 30


def clamp(value: float) -> float:
    return max(SCALE_MIN, min(SCALE_MAX, value))


def percentile(value: float, reference: list[float] | np.ndarray) -> float:
    """Шаг 1. Доля игроков выборки с показателем меньше или равным value, в [0; 100].

    Соответствует определению из 2.2.6: «какой процент игроков выборки имеет
    показатель меньше или равный показателю оцениваемого игрока».
    """
    ref = np.asarray(reference, dtype=float)
    if ref.size == 0:
        raise ValueError("Референтная выборка пуста")
    return float(np.mean(ref <= value) * 100.0)


def to_score(p: float) -> int:
    """Шаг 2. Линейный перевод процентиля в балл: A = 25 + 0,74·p(x).

    Контрольные точки из диссертации: p=50 -> 62, p=95 -> 95, p=5 -> 29.
    """
    return int(round(clamp(INTERCEPT + SLOPE * p)))


def is_indicative(reference: list[float] | np.ndarray) -> bool:
    """Выборка меньше 30 игроков -> оценка маркируется как ориентировочная."""
    return len(reference) < REF_SAMPLE_MIN


def apply_context_corrections(
    score: float,
    *,
    opponent_factor: float = 1.0,
    usage_delta: float = 0.0,
    trend_delta: float = 0.0,
) -> int:
    """Шаг 3. Последовательные контекстные правки (раздел 2.2.6).

    opponent_factor — поправка на качество соперников (1,00–1,05 против верхней
        половины таблицы, 0,95–1,00 против нижней).
    usage_delta — поправка на использование USG (низкое USG при высокой
        эффективности даёт бонус, и наоборот). Передаётся в баллах.
    trend_delta — поправка на тренд по последним 10 играм относительно сезонного:
        стабильный рост до +3, стабильное падение до −3.
    Все правки идут последовательно, итог зажимается в диапазон [25; 99].
    """
    corrected = score * opponent_factor
    corrected = corrected + usage_delta
    corrected = corrected + max(-3.0, min(3.0, trend_delta))
    return int(round(clamp(corrected)))


def normalize_attribute(
    value: float,
    reference: list[float] | np.ndarray,
    *,
    opponent_factor: float = 1.0,
    usage_delta: float = 0.0,
    trend_delta: float = 0.0,
) -> dict:
    """Полная процедура: сырое значение -> балл 25–99 со всеми поправками.

    Возвращает словарь с промежуточными результатами — это нужно карточке игрока
    (вкладка «Данные»), где показываются процентиль и итоговый балл.
    """
    p = percentile(value, reference)
    base = to_score(p)
    final = apply_context_corrections(
        base,
        opponent_factor=opponent_factor,
        usage_delta=usage_delta,
        trend_delta=trend_delta,
    )
    return {
        "percentile": round(p, 1),
        "base_score": base,
        "score": final,
        "is_indicative": is_indicative(reference),
    }
