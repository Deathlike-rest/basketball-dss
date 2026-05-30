"""Наполнение БД демонстрационными данными команды апробации (раздел 3.2).

Состав: 14 игроков (4 PG, 3 SG, 3 SF, 2 PF, 2 C), возраст 18–23. За сезон АСБ
(октябрь–апрель) фиксируется история баллов атрибутов по семи контрольным точкам.
Воспроизведены два документированных кейса:
  * разыгрывающий второго года: рейтинг 64 -> 72, защита периметра 47 -> 61,
    трёхочковый 52 -> 65 (раздел 3.6);
  * тяжёлый форвард: падение прыгучести перед плей-офф -> срабатывание раннего
    предупреждения (раздел 3.5).
"""
from __future__ import annotations

import json
import random
from datetime import date

from app import create_app
from models import (
    db,
    User,
    Player,
    PlayerMeasurement,
    Attribute,
    WeightVersion,
    Weight,
    AttributeScore,
    ReferenceSample,
    Rating,
    ROLE_HEAD_COACH,
    ROLE_ASSISTANT,
    ROLE_ANALYST,
    ROLE_PLAYER,
)
from auth import hash_password
from core.attributes import ATTRIBUTES, WEIGHTED_ATTRIBUTES, POSITIONS
from core.weights import WEIGHT_MATRIX
from core import rating as rating_core

random.seed(42)

# Семь контрольных точек сезона (раздел 3.2: тесты каждые 2–3 недели).
PERIODS = [
    date(2024, 10, 1),
    date(2024, 11, 1),
    date(2024, 12, 1),
    date(2025, 1, 15),
    date(2025, 2, 15),
    date(2025, 3, 15),
    date(2025, 4, 1),
]

# Базовые профили 14 игроков: код атрибута -> стартовый балл (первая контрольная точка).
# Профили подобраны позиционно: у PG сильны созидание и броски, у C — завершение/защита/подбор.


def _profile(position: str, level: float) -> dict[str, float]:
    """Стартовый профиль игрока: базовый уровень + позиционный акцент + шум.

    Акцент аддитивный и почти нулевой в среднем по взвешенной сумме, поэтому
    интегральный рейтинг остаётся близок к заданному level: сигнатурные для позиции
    атрибуты (с большим весом) чуть выше, второстепенные — чуть ниже.
    """
    w_mean = sum(WEIGHT_MATRIX[c][position] for c in WEIGHTED_ATTRIBUTES) / len(WEIGHTED_ATTRIBUTES)
    base = {}
    for code in WEIGHTED_ATTRIBUTES:
        w = WEIGHT_MATRIX[code][position]
        accent = (w - w_mean) * 110.0
        base[code] = round(min(95, max(30, level + accent + random.uniform(-3, 3))))
    return base


def _drift(start: dict[str, float], period_idx: int, n_periods: int,
           season_gain: float = 1.4) -> dict[str, float]:
    """Плавный сезонный прирост с малым шумом.

    По умолчанию ~+1,4 балла за сезон (естественный прирост у не прорабатываемых
    атрибутов, раздел 3.6). Для прогрессирующего игрока gain выше.
    """
    frac = period_idx / (n_periods - 1)
    out = {}
    for code, v in start.items():
        out[code] = round(min(99, max(25, v + season_gain * frac + random.uniform(-0.6, 0.6))))
    return out


def seed():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        # --- Справочник атрибутов ---
        for code, (cat, name, descr) in ATTRIBUTES.items():
            db.session.add(Attribute(code=code, category=cat, name=name, description=descr))

        # --- Версия весов + матрица (таблица 3) ---
        wv = WeightVersion(version=1, valid_from=date(2024, 9, 1), author="Методика v1.0",
                           note="Стартовая матрица (таблица 3)")
        db.session.add(wv)
        db.session.flush()
        for code in WEIGHTED_ATTRIBUTES:
            for pos in POSITIONS:
                db.session.add(Weight(version_id=wv.id, attribute_code=code,
                                      position=pos, weight=WEIGHT_MATRIX[code][pos]))

        # --- Референтные выборки (уровень 3 — АСБ), по 40 значений на (атрибут, позиция) ---
        for code in WEIGHTED_ATTRIBUTES:
            for pos in POSITIONS:
                values = [round(random.gauss(60, 12), 1) for _ in range(40)]
                db.session.add(ReferenceSample(
                    attribute_code=code, position=pos, level=3,
                    league="АСБ", season="2024/2025", values_json=json.dumps(values)))

        # --- 14 игроков ---
        roster = [
            ("Соколов Артём",   "PG", 21, 63, {"M_IQ": 1, "M_S": 0, "M_L": 1}, "improver"),
            ("Морозов Илья",    "PG", 22, 71, {"M_IQ": 2, "M_S": 1, "M_L": 1}, None),
            ("Кузнецов Денис",  "PG", 19, 58, {"M_IQ": 0, "M_S": 0, "M_L": 0}, None),
            ("Лебедев Никита",  "PG", 18, 54, {"M_IQ": 0, "M_S": 0, "M_L": 0}, None),
            ("Волков Максим",   "SG", 23, 74, {"M_IQ": 1, "M_S": 2, "M_L": 0}, None),
            ("Зайцев Роман",    "SG", 20, 66, {"M_IQ": 1, "M_S": 0, "M_L": 0}, None),
            ("Новиков Павел",   "SG", 19, 60, {"M_IQ": 0, "M_S": 0, "M_L": 0}, None),
            ("Орлов Сергей",    "SF", 22, 72, {"M_IQ": 1, "M_S": 1, "M_L": 1}, None),
            ("Васильев Кирилл", "SF", 21, 67, {"M_IQ": 1, "M_S": 0, "M_L": 0}, None),
            ("Попов Глеб",      "SF", 18, 56, {"M_IQ": 0, "M_S": 0, "M_L": 0}, None),
            ("Семёнов Антон",   "PF", 23, 70, {"M_IQ": 1, "M_S": 0, "M_L": 1}, "injury"),
            ("Фёдоров Юрий",    "PF", 20, 63, {"M_IQ": 0, "M_S": 0, "M_L": 0}, None),
            ("Богданов Егор",   "C",  22, 73, {"M_IQ": 1, "M_S": 1, "M_L": 1}, None),
            ("Михайлов Тимур",  "C",  19, 61, {"M_IQ": 0, "M_S": 0, "M_L": 0}, None),
        ]

        first_pg_id = None
        for full_name, pos, age, level, mods, special in roster:
            player = Player(
                full_name=full_name,
                birth_date=date(2025 - age, 5, 15),
                primary_position=pos,
                team="Студенческая сборная (АСБ)",
                consent_signed=True,
            )
            db.session.add(player)
            db.session.flush()
            if pos == "PG" and first_pg_id is None:
                first_pg_id = player.id

            db.session.add(PlayerMeasurement(
                player_id=player.id, measured_on=PERIODS[0],
                height_cm={"PG": 188, "SG": 193, "SF": 198, "PF": 203, "C": 208}[pos],
                weight_kg={"PG": 82, "SG": 88, "SF": 94, "PF": 100, "C": 106}[pos],
                wingspan_cm={"PG": 192, "SG": 198, "SF": 205, "PF": 210, "C": 216}[pos]))

            start = _profile(pos, level)
            # Документированные кейсы (разделы 3.5, 3.6).
            if special == "improver":
                start["A12"] = 47   # защита периметра
                start["A6"] = 52    # трёхочковый

            n = len(PERIODS)
            season_gain = 8.0 if special == "improver" else 1.4
            for idx, period in enumerate(PERIODS):
                scores = _drift(start, idx, n, season_gain)
                if special == "improver":
                    frac = idx / (n - 1)
                    scores["A12"] = round(47 + (61 - 47) * frac)   # 47 -> 61
                    scores["A6"] = round(52 + (65 - 52) * frac)    # 52 -> 65
                if special == "injury" and idx == n - 1:
                    # Перед плей-офф резкое падение прыгучести и скорости (раздел 3.5).
                    scores["A21"] = round(scores["A21"] * 0.86)    # -14%
                    scores["A18"] = round(scores["A18"] * 0.90)

                for code, sc in scores.items():
                    db.session.add(AttributeScore(
                        player_id=player.id, attribute_code=code, computed_on=period,
                        score=sc, percentile=round((sc - 25) / 0.74, 1), is_indicative=False))

                r_p = rating_core.integral_rating(scores, pos)
                r_star = rating_core.apply_modifiers(r_p, mods["M_IQ"], mods["M_S"], mods["M_L"])
                db.session.add(Rating(
                    player_id=player.id, computed_on=period, position=pos,
                    r_p=r_p, r_star=r_star,
                    m_iq=mods["M_IQ"], m_s=mods["M_S"], m_l=mods["M_L"],
                    weight_version_id=wv.id))

        # --- Экспертное ранжирование для проверки согласованности (раздел 3.3) ---
        # Системный порядок по финальному R*, затем «экспертный» — как зашумлённая
        # его версия (опытный тренер ранжирует близко к системе, но не идентично).
        db.session.flush()
        finals = {}
        for player in Player.query.all():
            last = (Rating.query.filter_by(player_id=player.id)
                    .order_by(Rating.computed_on.desc()).first())
            finals[player.id] = last.r_star if last else 0
        noisy = {pid: r + random.gauss(0, 5.5) for pid, r in finals.items()}
        expert_order = sorted(finals.keys(), key=lambda pid: noisy[pid], reverse=True)
        for rank, pid in enumerate(expert_order, start=1):
            db.session.get(Player, pid).expert_rank = rank

        # --- Пользователи (раздел 2.5.2) ---
        db.session.add_all([
            User(login="coach", password_hash=hash_password("coach123"),
                 full_name="Главный тренер", role=ROLE_HEAD_COACH),
            User(login="assist", password_hash=hash_password("assist123"),
                 full_name="Ассистент тренера", role=ROLE_ASSISTANT),
            User(login="analyst", password_hash=hash_password("analyst123"),
                 full_name="Аналитик", role=ROLE_ANALYST),
            User(login="player1", password_hash=hash_password("player123"),
                 full_name="Соколов Артём", role=ROLE_PLAYER, player_id=first_pg_id),
        ])

        db.session.commit()
        print(f"Seed готов: {Player.query.count()} игроков, "
              f"{AttributeScore.query.count()} балльных значений, "
              f"{Rating.query.count()} рейтингов, {User.query.count()} пользователей.")


if __name__ == "__main__":
    seed()
