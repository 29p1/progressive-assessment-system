from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from app.db import get_db
from app.models.schemas import ROLES
from app.services.user_service import authenticate_user, create_user

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    role = (request.values.get("role") or "student").lower()
    if role not in ROLES:
        role = "student"

    if request.method == "POST":
        user_id, error = create_user(get_db(current_app), role, request.form.to_dict())
        if error:
            flash(error, "danger")
        else:
            flash("Registration successful. Please login.", "success")
            return redirect(url_for("auth.login", role=role))

    return render_template("auth/register.html", role=role, roles=sorted(ROLES))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    role = (request.values.get("role") or "student").lower()
    if role not in ROLES:
        role = "student"

    if request.method == "POST":
        identifier = request.form.get("identifier", "")
        password = request.form.get("password", "")
        user = authenticate_user(get_db(current_app), role, identifier, password)
        if not user:
            flash("Invalid credentials.", "danger")
        else:
            session.clear()
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard.home"))

    return render_template("auth/login.html", role=role, roles=sorted(ROLES))


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("landing"))
