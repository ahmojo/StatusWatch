from functools import wraps
from hmac import compare_digest

from flask import (
    Blueprint,
    abort,
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

auth_blueprint = Blueprint("auth", __name__)


def login_required(view):
    @wraps(view)
    def protected_view(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return protected_view


@auth_blueprint.route("/login", methods=["GET", "POST"])
def login():
    password = current_app.config["OPERATOR_PASSWORD"]
    if not password or not current_app.config["SECRET_KEY"]:
        abort(503)

    error = None
    if request.method == "POST":
        entered = request.form.get("password", "")
        if compare_digest(entered.encode("utf-8"), password.encode("utf-8")):
            session.clear()
            session["logged_in"] = True
            return redirect(url_for("monitors.index"))
        error = "Das Passwort ist falsch."

    return render_template("login.html", error=error), 401 if error else 200


@auth_blueprint.post("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
