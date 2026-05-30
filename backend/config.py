"""Конфигурация приложения.

По умолчанию используется PostgreSQL (раздел 2.5.1 диссертации). Для локального
запуска без Docker можно переопределить DATABASE_URL на SQLite.
"""
import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")

    # PostgreSQL 14 — основная СУБД по разделу 2.5.1.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://dss:dss@localhost:5432/basketball_dss",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Параметры методики (глава 2). Вынесены в конфиг, чтобы не «зашивать» магические
    # числа в код и при необходимости менять без правки алгоритмов.
    SCALE_MIN = 25          # нижняя граница шкалы (раздел 2.2.3)
    SCALE_MAX = 99          # верхняя граница шкалы
    SCORE_INTERCEPT = 25    # A = 25 + 0.74 * p  (раздел 2.2.6)
    SCORE_SLOPE = 0.74
    REF_SAMPLE_MIN = 30     # минимальный размер референтной выборки (раздел 2.2.6)
    EARLY_WARNING_SIGMA = 1.0  # порог раннего предупреждения, σ (раздел 2.4.3)
    EARLY_WARNING_WINDOW = 4   # число предыдущих периодов для скользящего среднего
