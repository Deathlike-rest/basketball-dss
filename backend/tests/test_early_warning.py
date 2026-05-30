"""Тесты подсистемы раннего предупреждения (раздел 2.4.3, сценарий 3)."""
from core import early_warning
from core.attributes import category_of


def test_no_alert_for_stable_series():
    # Стабильный ряд без падения — предупреждения нет.
    assert early_warning.detect_drop([70, 71, 70, 72, 71]) is None


def test_no_alert_for_rising_series():
    assert early_warning.detect_drop([60, 62, 64, 66, 70]) is None


def test_alert_on_sharp_drop():
    # Резкое падение > 1σ относительно скользящего среднего — срабатывание.
    hit = early_warning.detect_drop([72, 71, 73, 70, 58])
    assert hit is not None
    assert hit["drop"] > early_warning.MIN_ABS_DROP
    assert hit["sigma"] > early_warning.DEFAULT_SIGMA


def test_small_drop_below_abs_threshold_ignored():
    # Падение меньше абсолютного порога считается шумом округления.
    assert early_warning.detect_drop([70, 70, 70, 70, 69]) is None


def test_insufficient_history_returns_none():
    assert early_warning.detect_drop([70, 68]) is None


def test_athletic_attributes_get_high_priority():
    # Падение атлетического атрибута (A21 — прыгучесть) помечается приоритетным.
    histories = {"A21": [72, 71, 73, 70, 72, 60]}
    assert category_of("A21") == "Атлетизм"
    alerts = early_warning.scan_player(histories)
    assert len(alerts) == 1
    assert alerts[0]["priority"] == "high"
    assert alerts[0]["attribute"] == "A21"
