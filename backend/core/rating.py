"""Математическая модель интегрального рейтинга (раздел 2.2.5 диссертации).

R_P = Σ A_i · w_(i,P)  — взвешенная сумма 21 атрибута; Σw = 1, поэтому R_P ∈ [25; 99].
R*_P = R_P + M_IQ + M_S + M_L,  R*_P ≤ 99 — скорректированный рейтинг с модификаторами.
"""
from __future__ import annotations

from .attributes import WEIGHTED_ATTRIBUTES, POSITIONS
from .weights import WEIGHT_MATRIX

SCALE_MAX = 99

# Допустимые диапазоны модификаторов (раздел 2.2.5).
MOD_IQ_RANGE = (-2, 2)   # баскетбольный интеллект
MOD_S_RANGE = (0, 2)     # специальные навыки
MOD_L_RANGE = (0, 1)     # лидерские качества


def integral_rating(scores: dict[str, float], position: str) -> float:
    """R_P для позиции P как взвешенная сумма атрибутов.

    scores — словарь {код атрибута: балл 25–99}. Если по части атрибутов данных
    нет (атрибут отсутствует в scores), он исключается, а веса оставшихся
    нормируются заново (правило из раздела 2.3.4: «расчёт проводится без него с
    пересчётом весов»).
    """
    if position not in POSITIONS:
        raise ValueError(f"Неизвестная позиция: {position}")

    present = [code for code in WEIGHTED_ATTRIBUTES if code in scores and scores[code] is not None]
    if not present:
        raise ValueError("Нет ни одного балла для расчёта рейтинга")

    weight_sum = sum(WEIGHT_MATRIX[code][position] for code in present)
    total = 0.0
    for code in present:
        w = WEIGHT_MATRIX[code][position] / weight_sum  # пересчёт весов
        total += scores[code] * w
    # Рейтинг читается по той же целочисленной шкале, что и отдельный атрибут (раздел 2.2.5).
    return int(round(total))


def position_vector(scores: dict[str, float]) -> dict[str, float]:
    """Вектор позиционных рейтингов R = (R_PG, R_SG, R_SF, R_PF, R_C).

    Под универсальность игрока: основная позиция даёт профильный рейтинг, остальные
    показывают пригодность к другим ролям (раздел 2.2.5).
    """
    return {pos: integral_rating(scores, pos) for pos in POSITIONS}


def _check_range(value: int, rng: tuple[int, int], name: str) -> None:
    lo, hi = rng
    if not (lo <= value <= hi):
        raise ValueError(f"Модификатор {name} = {value} вне диапазона [{lo}; {hi}]")


def apply_modifiers(r_p: float, m_iq: int = 0, m_s: int = 0, m_l: int = 0) -> float:
    """R*_P = R_P + M_IQ + M_S + M_L с ограничением R*_P ≤ 99 (раздел 2.2.5)."""
    _check_range(m_iq, MOD_IQ_RANGE, "M_IQ")
    _check_range(m_s, MOD_S_RANGE, "M_S")
    _check_range(m_l, MOD_L_RANGE, "M_L")
    return int(round(min(SCALE_MAX, r_p + m_iq + m_s + m_l)))


def full_rating(
    scores: dict[str, float],
    position: str,
    m_iq: int = 0,
    m_s: int = 0,
    m_l: int = 0,
) -> dict:
    """Полный расчёт: базовый рейтинг, вектор позиций и скорректированный R*."""
    r_p = integral_rating(scores, position)
    return {
        "position": position,
        "R_P": r_p,
        "R_star": apply_modifiers(r_p, m_iq, m_s, m_l),
        "position_vector": position_vector(scores),
        "modifiers": {"M_IQ": m_iq, "M_S": m_s, "M_L": m_l},
    }
