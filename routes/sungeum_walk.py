from flask import Blueprint, jsonify, request, send_from_directory, session

from database.sungeum_walk import leaderboard, start_game, submit_score


sungeum_walk_bp = Blueprint("sungeum_walk", __name__)


@sungeum_walk_bp.get("/sungeum-walk/")
def game():
    return send_from_directory("prototypes/sungeum-walk", "index.html")


@sungeum_walk_bp.get("/sungeum-walk/<path:filename>")
def asset(filename):
    return send_from_directory("prototypes/sungeum-walk", filename)


@sungeum_walk_bp.get("/api/sungeum-walk/leaderboard")
def daily_leaderboard():
    return jsonify(ok=True, logged_in=bool(session.get("user_id")), **leaderboard(session.get("user_id")))


@sungeum_walk_bp.post("/api/sungeum-walk/start")
def game_start():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify(ok=True, logged_in=False, token=None, **leaderboard()), 200
    return jsonify(ok=True, logged_in=True, token=start_game(user_id), **leaderboard(user_id))


@sungeum_walk_bp.post("/api/sungeum-walk/submit")
def game_submit():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify(ok=False, error="login_required"), 401
    payload = request.get_json(silent=True) or {}
    try:
        result = submit_score(user_id, payload.get("token"), payload.get("score", -1))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="invalid_score"), 400
    return jsonify(ok=True, **result)
