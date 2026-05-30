"""Модель реляционной базы данных (раздел 2.4.2 диссертации).

Семь основных сущностей: игроки, атрибуты, веса, сырые показатели, балльные
значения, референтные выборки, рейтинги. Плюс служебные таблицы: пользователи
(роли), утверждённые стартовые пятёрки (для анализа эффективности по разделу 3.4),
журнал ранних предупреждений и справочник упражнений.
"""
from __future__ import annotations

from datetime import datetime, date

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# --- Роли пользователей (раздел 2.5.2) ---
ROLE_HEAD_COACH = "head_coach"      # Главный тренер — полный доступ + утверждение составов
ROLE_ASSISTANT = "assistant"        # Ассистент — как тренер, но без утверждения составов
ROLE_ANALYST = "analyst"            # Аналитик — статистика и отчёты, ввод матчевых данных
ROLE_PLAYER = "player"              # Игрок — только свой профиль (просмотр)
ROLES = [ROLE_HEAD_COACH, ROLE_ASSISTANT, ROLE_ANALYST, ROLE_PLAYER]


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.LargeBinary, nullable=False)  # bcrypt-хэш (раздел 2.5.4)
    full_name = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(32), nullable=False, default=ROLE_ANALYST)
    # Для роли «Игрок» — связь со своим профилем игрока.
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=True)


# --- 1. Игроки ---
class Player(db.Model):
    __tablename__ = "players"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(128), nullable=False)
    birth_date = db.Column(db.Date)
    primary_position = db.Column(db.String(4), nullable=False)   # PG/SG/SF/PF/C
    secondary_positions = db.Column(db.String(32))               # через запятую
    team = db.Column(db.String(128))
    consent_signed = db.Column(db.Boolean, default=False)        # СОПД (раздел 2.5.4)
    # Независимое экспертное ранжирование тренерским штабом (1 = лучший) — для
    # проверки согласованности системного рейтинга с экспертной оценкой (раздел 3.3).
    expert_rank = db.Column(db.Integer, nullable=True)

    measurements = db.relationship("PlayerMeasurement", backref="player", cascade="all, delete-orphan")
    raw_stats = db.relationship("RawStat", backref="player", cascade="all, delete-orphan")
    attribute_scores = db.relationship("AttributeScore", backref="player", cascade="all, delete-orphan")
    ratings = db.relationship("Rating", backref="player", cascade="all, delete-orphan")


# История антропометрии (рост/вес меняются — хранятся с историей, раздел 2.4.2).
class PlayerMeasurement(db.Model):
    __tablename__ = "player_measurements"
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    measured_on = db.Column(db.Date, default=date.today)
    height_cm = db.Column(db.Float)
    weight_kg = db.Column(db.Float)
    wingspan_cm = db.Column(db.Float)


# --- 2. Атрибуты (статический справочник, наполняется один раз) ---
class Attribute(db.Model):
    __tablename__ = "attributes"
    code = db.Column(db.String(4), primary_key=True)   # A1..A21
    category = db.Column(db.String(32), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256))


# --- 3. Веса (версионируемая матрица, раздел 2.4.2) ---
class WeightVersion(db.Model):
    __tablename__ = "weight_versions"
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.Integer, nullable=False)
    valid_from = db.Column(db.Date, default=date.today)
    author = db.Column(db.String(128))
    note = db.Column(db.String(256))


class Weight(db.Model):
    __tablename__ = "weights"
    id = db.Column(db.Integer, primary_key=True)
    version_id = db.Column(db.Integer, db.ForeignKey("weight_versions.id"), nullable=False)
    attribute_code = db.Column(db.String(4), db.ForeignKey("attributes.code"), nullable=False)
    position = db.Column(db.String(4), nullable=False)
    weight = db.Column(db.Float, nullable=False)


# --- 4. Сырые показатели (одно измерение = один матч/тест/решение) ---
class RawStat(db.Model):
    __tablename__ = "raw_stats"
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    measured_on = db.Column(db.Date, nullable=False)
    source_type = db.Column(db.Integer, nullable=False)   # тип источника 1–6 (раздел 2.3.1)
    metric = db.Column(db.String(64), nullable=False)     # например, "FG%<3m", "sprint20m"
    value = db.Column(db.Float)


# --- 5. Балльные значения атрибутов (результат нормализации) ---
class AttributeScore(db.Model):
    __tablename__ = "attribute_scores"
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    attribute_code = db.Column(db.String(4), db.ForeignKey("attributes.code"), nullable=False)
    computed_on = db.Column(db.Date, nullable=False)
    score = db.Column(db.Float, nullable=False)           # 25–99
    percentile = db.Column(db.Float)
    ref_sample_id = db.Column(db.Integer, db.ForeignKey("reference_samples.id"), nullable=True)
    is_indicative = db.Column(db.Boolean, default=False)  # выборка < 30 игроков


# --- 6. Референтные выборки (массив значений, раздел 2.3.5) ---
class ReferenceSample(db.Model):
    __tablename__ = "reference_samples"
    id = db.Column(db.Integer, primary_key=True)
    attribute_code = db.Column(db.String(4), db.ForeignKey("attributes.code"), nullable=False)
    position = db.Column(db.String(4), nullable=False)
    level = db.Column(db.Integer, nullable=False)         # уровень 1–4 (раздел 2.3.5)
    league = db.Column(db.String(64))
    season = db.Column(db.String(16))
    values_json = db.Column(db.Text, nullable=False)      # JSON-массив сырых значений


# --- 7. Рейтинги (итоговые R_P и R*, с привязкой к версии весов и модификаторам) ---
class Rating(db.Model):
    __tablename__ = "ratings"
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    computed_on = db.Column(db.Date, nullable=False)
    position = db.Column(db.String(4), nullable=False)
    r_p = db.Column(db.Float, nullable=False)
    r_star = db.Column(db.Float, nullable=False)
    m_iq = db.Column(db.Integer, default=0)
    m_s = db.Column(db.Integer, default=0)
    m_l = db.Column(db.Integer, default=0)
    weight_version_id = db.Column(db.Integer, db.ForeignKey("weight_versions.id"))


# --- Служебные ---
class Lineup(db.Model):
    """Утверждённая главным тренером стартовая пятёрка на матч (раздел 3.4)."""
    __tablename__ = "lineups"
    id = db.Column(db.Integer, primary_key=True)
    match_date = db.Column(db.Date, nullable=False)
    opponent = db.Column(db.String(128))
    approved_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    matches_system_suggestion = db.Column(db.Boolean, default=True)
    # Результат для последующего анализа эффективности.
    result_win = db.Column(db.Boolean, nullable=True)
    point_diff = db.Column(db.Integer, nullable=True)
    player_ids_json = db.Column(db.Text)  # JSON список из 5 id игроков


class Alert(db.Model):
    """Журнал срабатываний раннего предупреждения (раздел 2.4.3, сценарий 3)."""
    __tablename__ = "alerts"
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    attribute_code = db.Column(db.String(4), db.ForeignKey("attributes.code"))
    created_on = db.Column(db.Date, default=date.today)
    baseline = db.Column(db.Float)
    current = db.Column(db.Float)
    drop = db.Column(db.Float)
    priority = db.Column(db.String(16), default="normal")
    status = db.Column(db.String(32), default="new")  # new/confirmed/partial/false_alarm
