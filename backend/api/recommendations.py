"""Сценарий 2 — индивидуальные рекомендации по тренировке (раздел 2.4.3)."""
from flask import Blueprint, jsonify, abort
from flask_login import login_required, current_user

from models import Player, ROLE_PLAYER
import services

recommendations_bp = Blueprint("recommendations", __name__, url_prefix="/api/recommendations")


@recommendations_bp.get("/player/<int:player_id>")
@login_required
def for_player(player_id: int):
    # Игрок видит свои рекомендации; штаб — любые.
    if current_user.role == ROLE_PLAYER and current_user.player_id != player_id:
        abort(403)
    player = Player.query.get_or_404(player_id)
    return jsonify(services.player_recommendations(player))
