from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from app.db import get_db
from app.routes.utils import login_required, role_required
from app.services.user_service import list_subjects, list_users, upsert_branch_access, upsert_subject

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard", methods=["GET", "POST"])
@login_required
@role_required("admin")
def dashboard():
    db = get_db(current_app)

    if request.method == "POST":
        action = request.form.get("action")
        if action == "add_subject":
            upsert_subject(db, request.form.to_dict())
            flash("Subject saved.", "success")
        elif action == "set_access":
            upsert_branch_access(
                db,
                request.form.get("faculty_user_id"),
                request.form.get("branches", "").split(","),
            )
            flash("Branch access updated.", "success")
        return redirect(url_for("admin.dashboard"))

    users = list_users(db)
    faculty_users = [user for user in users if user["role"] == "faculty"]

    return render_template(
        "admin/dashboard.html",
        users=users,
        faculty_users=faculty_users,
        subjects=list_subjects(db),
    )
