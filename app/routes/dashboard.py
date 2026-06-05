import json

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from app.db import get_db
from app.routes.utils import login_required, role_required
from app.services.user_service import (
    aggregate_all_branch_progress,
    aggregate_branch_progress,
    get_class_marks,
    get_profile,
    get_student_progress,
    list_students_by_branch_sem,
    upsert_mark,
)

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def _safe_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@dashboard_bp.route("/")
@login_required
def home():
    role = session["role"]
    target = {
        "student": "dashboard.student",
        "faculty": "dashboard.faculty",
        "hod": "dashboard.hod",
        "principal": "dashboard.principal",
        "admin": "admin.dashboard",
    }[role]
    return redirect(url_for(target))


@dashboard_bp.route("/student")
@login_required
@role_required("student")
def student():
    db = get_db(current_app)
    profile = get_profile(db, "student", session["user_id"])
    sem = _safe_int(request.args.get("sem"), profile["sem"])
    progress = get_student_progress(db, session["user_id"], sem)
    labels = [item["subject_name"] for item in progress["rows"]]
    values = [item["total"] for item in progress["rows"]]

    return render_template(
        "dashboards/student.html",
        profile=profile,
        sem=sem,
        rows=progress["rows"],
        total=progress["total"],
        percentage=progress["percentage"],
        chart_labels=json.dumps(labels),
        chart_values=json.dumps(values),
    )


@dashboard_bp.route("/faculty", methods=["GET", "POST"])
@login_required
@role_required("faculty")
def faculty():
    db = get_db(current_app)
    profile = get_profile(db, "faculty", session["user_id"])

    selected_branch = request.values.get("branch") or (profile.get("branches") or [""])[0]
    selected_sem = _safe_int(request.values.get("sem"), 1)
    selected_subject = request.values.get("subject") or ((profile.get("subjects") or [{}])[0].get("subject_number", ""))

    if request.method == "POST" and request.form.get("student_user_id"):
        upsert_mark(
            db,
            session["user_id"],
            request.form["student_user_id"],
            selected_branch,
            selected_sem,
            selected_subject,
            {
                "pa1": request.form.get("pa1", 0),
                "pa2": request.form.get("pa2", 0),
                "practical": request.form.get("practical", 0),
                "gtu": request.form.get("gtu", 0),
            },
        )
        flash("Marks updated.", "success")
        return redirect(
            url_for(
                "dashboard.faculty",
                branch=selected_branch,
                sem=selected_sem,
                subject=selected_subject,
            )
        )

    rows = []
    if selected_branch and selected_subject:
        rows = get_class_marks(db, selected_branch, selected_sem, selected_subject)

    return render_template(
        "dashboards/faculty.html",
        profile=profile,
        branches=profile.get("branches", []),
        subjects=profile.get("subjects", []),
        selected_branch=selected_branch,
        selected_sem=selected_sem,
        selected_subject=selected_subject,
        rows=rows,
    )


@dashboard_bp.route("/hod")
@login_required
@role_required("hod")
def hod():
    db = get_db(current_app)
    profile = get_profile(db, "hod", session["user_id"])
    sem = _safe_int(request.args.get("sem"), 1)

    students = list_students_by_branch_sem(db, profile["branch"], sem)
    chart = aggregate_branch_progress(db, profile["branch"], sem)

    return render_template(
        "dashboards/hod.html",
        profile=profile,
        sem=sem,
        students=students,
        chart_labels=json.dumps([item["name"] for item in chart]),
        chart_values=json.dumps([item["percentage"] for item in chart]),
    )


@dashboard_bp.route("/principal")
@login_required
@role_required("principal")
def principal():
    sem = _safe_int(request.args.get("sem"), 1)
    chart = aggregate_all_branch_progress(get_db(current_app), sem)

    return render_template(
        "dashboards/principal.html",
        sem=sem,
        chart_labels=json.dumps([item["branch"] for item in chart]),
        chart_values=json.dumps([item["average_percentage"] for item in chart]),
        chart=chart,
    )
