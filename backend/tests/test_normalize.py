"""Тесты нормализации сырых данных в шкалу 25–99 (раздел 2.2.6)."""
import pytest

from core import normalize


def test_to_score_control_points():
    # Контрольные точки из раздела 2.2.6 и таблицы 4.
    assert normalize.to_score(50) == 62   # медианный игрок позиции
    assert normalize.to_score(95) == 95
    assert normalize.to_score(5) == 29
    assert normalize.to_score(70) == 77   # строка из таблицы 4 (бросок вблизи)


def test_to_score_clamped_to_scale():
    assert normalize.to_score(0) == 25     # нижняя граница шкалы
    assert normalize.to_score(100) == 99   # 25 + 74 = 99, верхняя граница


def test_percentile_basic():
    ref = list(range(1, 11))  # 1..10
    assert normalize.percentile(7, ref) == 70.0
    assert normalize.percentile(10, ref) == 100.0
    assert normalize.percentile(1, ref) == 10.0


def test_percentile_empty_raises():
    with pytest.raises(ValueError):
        normalize.percentile(5, [])


def test_indicative_below_30():
    assert normalize.is_indicative(list(range(29))) is True
    assert normalize.is_indicative(list(range(30))) is False


def test_context_corrections_clamped():
    # Поправки идут последовательно, итог зажат в [25; 99].
    assert normalize.apply_context_corrections(95, opponent_factor=1.05, trend_delta=3) == 99
    assert normalize.apply_context_corrections(26, opponent_factor=0.95, trend_delta=-3) == 25


def test_trend_delta_capped_at_3():
    base = normalize.apply_context_corrections(60, trend_delta=10)
    assert base == 63  # тренд ограничен +3 (раздел 2.2.6)
