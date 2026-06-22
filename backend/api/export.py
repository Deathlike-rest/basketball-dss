"""Экспорт отчётов (раздел 2.4.1, этап 7; процесс формирования статистического
отчёта, рис. 3–4).

Симметрично импорту из 2.5.3 экспорт реализован в формате CSV: отчёт по составу
команды с балльными показателями (блок A6) и подробный отчёт по игроку
(разложение по атрибутам). CSV пишется с BOM — корректно открывается в Excel.
"""
import csv
import io
from datetime import date

from flask import Blueprint, Response, abort
from flask_login import login_required, current_user

from models import Player, AttributeScore, ROLE_PLAYER
from auth import role_required, STAFF_ROLES
from core.attributes import WEIGHTED_ATTRIBUTES, ATTRIBUTES, name_of, category_of
import services

export_bp = Blueprint("export", __name__, url_prefix="/api/export")


def _csv_response(rows: list[list], filename: str) -> Response:
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")  # ; — чтобы Excel в RU-локали корректно делил колонки
    writer.writerows(rows)
    data = "﻿" + buf.getvalue()  # BOM для Excel
    return Response(
        data,
        mimetype="text/csv",  # Flask сам добавит charset=utf-8
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@export_bp.get("/team.csv")
@role_required(*STAFF_ROLES)
def team_csv():
    """Отчёт по составу: рейтинг и баллы по 21 атрибуту для каждого игрока (блок A6)."""
    header = ["Игрок", "Позиция", "R_P", "R*", "M_IQ", "M_S", "M_L"]
    header += [name_of(code) for code in WEIGHTED_ATTRIBUTES]
    rows = [header]

    for o in services.team_overview():
        player = Player.query.get(o["player_id"])
        rating = services.latest_rating(player.id)
        scores = services.latest_scores(player.id)
        row = [
            o["name"], o["position"], o["R_P"], o["R_star"],
            rating.m_iq if rating else 0,
            rating.m_s if rating else 0,
            rating.m_l if rating else 0,
        ]
        row += [scores.get(code, "") for code in WEIGHTED_ATTRIBUTES]
        rows.append(row)

    return _csv_response(rows, f"team_report_{date.today().isoformat()}.csv")


@export_bp.get("/player/<int:player_id>.csv")
@login_required
def player_csv(player_id: int):
    """Подробный отчёт по игроку: разложение по атрибутам с процентилями."""
    # Игрок может выгрузить только свой отчёт; штаб — любой (раздел 2.5.2).
    if current_user.role == ROLE_PLAYER and current_user.player_id != player_id:
        abort(403)
    player = Player.query.get_or_404(player_id)
    rating = services.compute_player_rating(player)
    scores = services.latest_scores(player.id)

    rows = [
        ["Отчёт по игроку", player.full_name],
        ["Позиция", player.primary_position],
        ["Рейтинг R_P", rating["R_P"]],
        ["Рейтинг R*", rating["R_star"]],
        [],
        ["Код", "Атрибут", "Категория", "Балл", "Процентиль"],
    ]
    for code in WEIGHTED_ATTRIBUTES:
        last = (
            AttributeScore.query.filter_by(player_id=player.id, attribute_code=code)
            .order_by(AttributeScore.computed_on.desc())
            .first()
        )
        rows.append([
            code, name_of(code), category_of(code),
            scores.get(code, ""),
            last.percentile if last else "",
        ])

    safe_name = player.full_name.replace(" ", "_")
    return _csv_response(rows, f"player_{safe_name}_{date.today().isoformat()}.csv")
