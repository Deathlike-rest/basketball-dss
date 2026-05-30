"""Тесты матрицы весов и интегрального рейтинга (разделы 2.2.4, 2.2.5)."""
import pytest

from core import rating, weights
from core.attributes import POSITIONS, WEIGHTED_ATTRIBUTES


def test_weight_columns_sum_to_one():
    # Сумма весов по каждой позиции = 1,000 (раздел 2.2.4).
    for pos in POSITIONS:
        assert abs(weights.column_sum(pos) - 1.0) < 1e-9


def test_all_attributes_present_in_matrix():
    assert len(WEIGHTED_ATTRIBUTES) == 21
    for code in WEIGHTED_ATTRIBUTES:
        assert set(weights.WEIGHT_MATRIX[code].keys()) == set(POSITIONS)


def test_uniform_scores_give_same_rating():
    # При нормировке весов одинаковые баллы дают тот же рейтинг (Σw = 1).
    scores = {c: 70 for c in WEIGHTED_ATTRIBUTES}
    for pos in POSITIONS:
        assert rating.integral_rating(scores, pos) == 70.0


def test_rating_within_scale():
    scores = {c: 25 for c in WEIGHTED_ATTRIBUTES}
    assert rating.integral_rating(scores, "PG") == 25.0
    scores = {c: 99 for c in WEIGHTED_ATTRIBUTES}
    assert rating.integral_rating(scores, "C") == 99.0


def test_modifiers_clamped_to_99():
    # R* не превышает 99 (раздел 2.2.5).
    assert rating.apply_modifiers(98, m_iq=2, m_s=2, m_l=1) == 99.0
    assert rating.apply_modifiers(60, m_iq=2, m_s=2, m_l=1) == 65.0


def test_modifier_range_validation():
    with pytest.raises(ValueError):
        rating.apply_modifiers(60, m_iq=3)      # вне диапазона [-2; 2]
    with pytest.raises(ValueError):
        rating.apply_modifiers(60, m_s=-1)      # вне диапазона [0; 2]
    with pytest.raises(ValueError):
        rating.apply_modifiers(60, m_l=2)       # вне диапазона [0; 1]


def test_missing_attribute_renormalizes_weights():
    # При отсутствии данных по атрибуту веса оставшихся пересчитываются (раздел 2.3.4).
    full = {c: 80 for c in WEIGHTED_ATTRIBUTES}
    partial = {c: 80 for c in WEIGHTED_ATTRIBUTES if c != "A5"}
    assert rating.integral_rating(partial, "PG") == rating.integral_rating(full, "PG") == 80.0


def test_position_vector_has_five_positions():
    scores = {c: 60 for c in WEIGHTED_ATTRIBUTES}
    vec = rating.position_vector(scores)
    assert set(vec.keys()) == set(POSITIONS)


def test_empty_scores_raise():
    with pytest.raises(ValueError):
        rating.integral_rating({}, "PG")
