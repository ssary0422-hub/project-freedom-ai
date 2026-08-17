from flask import Blueprint, render_template
from routes.auth import login_required

poster_bp = Blueprint("poster", __name__)

@poster_bp.route("/poster")
@login_required
def poster():
    return render_template("poster.html")
