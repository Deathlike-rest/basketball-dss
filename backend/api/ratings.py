"""Рейтинги и модификаторы (разделы 2.2.5, 2.4).

Изменять значения модификаторов может только тренерский штаб (раздел 2.5.2:
аналитик не имеет права менять модификаторы).
"""
from datetime import date

from flask import Blueprint, jsonify, request
from flask_login import login_required

from models import db, Player, Rating, ROLE_HEAD_COACH, ROLE_ASSISTANT
from auth import role_required
from core import rating as rating_core
import services

ratings_bp = Blueprint("ratings", __name__, url_prefix="/api/ratings")


@ratings_bp.get("/team")
@login_required
def team_ratings():
    """Команда с R* и трендом — для дашборда тренера."""
    return jsonify(services.team_overview())


@ratings_bp.get("/validation")
@login_required
def validation():
    """Согласованность системного рейтинга с экспертной оценкой (раздел 3.3).

    Считает коэффициент ранговой корреляции Спирмена между ранжированием игроков по
    R* и независимым экспертным ранжированием тренерского штаба (из seed).
    """
    from scipy.stats import spearmanr

    rows = [
        (services.latest_rating(p.id), p.expert_rank)
        for p in Player.query.all()
    ]
    pairs = [(r.r_star, er) for r, er in rows if r is not None and er is not None]
    if len(pairs) < 3:
        return jsonify({"error": "Недостаточно данных для корреляции"}), 400

    system_scores = [p[0] for p in pairs]
    expert_ranks = [p[1] for p in pairs]
    # Экспертный ранг: 1 = лучший, поэтому коррелируем с -ранг для согласования направлений.
    rho, pvalue = spearmanr(system_scores, [-er for er in expert_ranks])
    return jsonify({"spearman": round(float(rho), 2), "p_value": float(pvalue), "n": len(pairs)})


@ratings_bp.get("/player/<int:player_id>")
@login_required
def player_rating(player_id: int):
    player = Player.query.get_or_404(player_id)
    return jsonify(services.compute_player_rating(player))


@ratings_bp.post("/player/<int:player_id>/modifiers")
@role_required(ROLE_HEAD_COACH, ROLE_ASSISTANT)
def set_modifiers(player_id: int):
    """Установка модификаторов M_IQ, M_S, M_L и пересчёт R* (раздел 2.2.5).

    Значения хранятся с привязкой к дате — это позволяет отследить, как менялась
    экспертная оценка игрока со временем (раздел 2.4.1, этап 6).
    """
    player = Player.query.get_or_404(player_id)
    data = request.get_json(silent=True) or {}
    m_iq = int(data.get("M_IQ", 0))
    m_s = int(data.get("M_S", 0))
    m_l = int(data.get("M_L", 0))

    scores = services.latest_scores(player.id)
    try:
        r_p = rating_core.integral_rating(scores, player.primary_position)
        r_star = rating_core.apply_modifiers(r_p, m_iq, m_s, m_l)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    rating = Rating(
        player_id=player.id,
        computed_on=date.today(),
        position=player.primary_position,
        r_p=r_p,
        r_star=r_star,
        m_iq=m_iq,
        m_s=m_s,
        m_l=m_l,
    )
    db.session.add(rating)
    db.session.commit()
    return jsonify({"R_P": r_p, "R_star": r_star, "modifiers": {"M_IQ": m_iq, "M_S": m_s, "M_L": m_l}})
