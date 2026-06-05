from datetime import datetime, timezone

from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from werkzeug.security import check_password_hash, generate_password_hash

from app.models.schemas import REQUIRED_FIELDS, ROLES


def _utcnow():
    return datetime.now(timezone.utc)


def _str_id(value):
    return str(value) if value else None


def _to_object_id(value):
    return ObjectId(value) if value and not isinstance(value, ObjectId) else value


def _clean_subjects(payload):
    subjects = payload.get("subjects") or []
    if isinstance(subjects, str):
        parsed = []
        for row in subjects.splitlines():
            if not row.strip():
                continue
            parts = [part.strip() for part in row.split("|")]
            if len(parts) != 4:
                continue
            parsed.append(
                {
                    "subject_number": parts[0],
                    "subject_name": parts[1],
                    "sem": int(parts[2]),
                    "branch": parts[3].upper(),
                }
            )
        subjects = parsed

    clean = []
    for subject in subjects:
        if not subject.get("subject_number") or not subject.get("subject_name"):
            continue
        clean.append(
            {
                "subject_number": subject["subject_number"].strip().upper(),
                "subject_name": subject["subject_name"].strip(),
                "sem": int(subject.get("sem", payload.get("sem", 1))),
                "branch": (subject.get("branch") or payload.get("branch", "")).strip().upper(),
            }
        )
    if not clean and payload.get("subject_number") and payload.get("subject_name"):
        clean.append(
            {
                "subject_number": payload["subject_number"].strip().upper(),
                "subject_name": payload["subject_name"].strip(),
                "sem": int(payload.get("sem", 1)),
                "branch": payload.get("branch", "").strip().upper(),
            }
        )
    return clean


def _clean_branches(payload):
    branches = payload.get("branches")
    if isinstance(branches, str):
        branches = [item.strip().upper() for item in branches.split(",") if item.strip()]
    elif isinstance(branches, list):
        branches = [str(item).strip().upper() for item in branches if str(item).strip()]
    else:
        branches = []

    if payload.get("branch"):
        single = payload["branch"].strip().upper()
        if single and single not in branches:
            branches.append(single)
    return sorted(set(branches))


def validate_registration(role, payload):
    if role not in ROLES:
        return "Invalid role."

    for field in REQUIRED_FIELDS[role]:
        if not str(payload.get(field, "")).strip():
            return f"{field.replace('_', ' ').title()} is required."

    if role == "student":
        try:
            int(payload["sem"])
        except (ValueError, TypeError):
            return "Semester must be numeric."

    if role == "faculty":
        try:
            int(payload["number_of_subjects"])
        except (ValueError, TypeError):
            return "Number of subjects must be numeric."

    return None


def create_user(db, role, payload):
    error = validate_registration(role, payload)
    if error:
        return None, error

    email = payload.get("email", "").strip().lower() or None
    enrollment_no = payload.get("enrollment_no", "").strip().upper() or None

    if role == "student":
        login_id = enrollment_no
    else:
        login_id = email

    user_doc = {
        "role": role,
        "login_id": login_id,
        "email": email,
        "password_hash": generate_password_hash(payload["password"]),
        "first_name": payload.get("first_name", "").strip(),
        "last_name": payload.get("last_name", "").strip(),
        "college_name": payload.get("college_name", "").strip(),
        "created_at": _utcnow(),
        "updated_at": _utcnow(),
    }

    try:
        user_id = db.users.insert_one(user_doc).inserted_id
    except DuplicateKeyError:
        return None, "Account already exists for this identifier/email."

    base_profile = {
        "user_id": user_id,
        "created_at": _utcnow(),
        "updated_at": _utcnow(),
    }

    if role == "student":
        db.student_profiles.insert_one(
            {
                **base_profile,
                "enrollment_no": enrollment_no,
                "branch": payload["branch"].strip().upper(),
                "sem": int(payload["sem"]),
            }
        )
    elif role == "faculty":
        branches = _clean_branches(payload)
        subjects = _clean_subjects(payload)
        db.faculty_profiles.insert_one(
            {
                **base_profile,
                "number_of_subjects": int(payload["number_of_subjects"]),
                "branches": branches,
                "subjects": subjects,
            }
        )
        if branches:
            db.branch_access.insert_many(
                [
                    {
                        "faculty_user_id": user_id,
                        "branch": branch,
                        "created_at": _utcnow(),
                    }
                    for branch in branches
                ]
            )
        for subject in subjects:
            db.subjects.update_one(
                {
                    "subject_number": subject["subject_number"],
                    "branch": subject["branch"],
                    "sem": subject["sem"],
                },
                {"$setOnInsert": {"subject_name": subject["subject_name"], "created_at": _utcnow()}},
                upsert=True,
            )
    elif role == "hod":
        db.hod_profiles.insert_one(
            {
                **base_profile,
                "branch": payload["branch"].strip().upper(),
            }
        )
    elif role == "principal":
        db.principal_profiles.insert_one(base_profile)
    elif role == "admin":
        db.admin_profiles.insert_one(base_profile)

    return _str_id(user_id), None


def authenticate_user(db, role, identifier, password):
    if role == "student":
        login_id = identifier.strip().upper()
    else:
        normalized = identifier.strip()
        login_id = normalized.lower() if "@" in normalized else normalized

    user = db.users.find_one({"role": role, "login_id": login_id})
    if not user or not check_password_hash(user["password_hash"], password):
        return None

    return serialize_user(user)


def get_user_by_id(db, user_id):
    user = db.users.find_one({"_id": _to_object_id(user_id)})
    return serialize_user(user) if user else None


def serialize_user(user_doc):
    if not user_doc:
        return None
    return {
        "id": _str_id(user_doc["_id"]),
        "role": user_doc["role"],
        "email": user_doc.get("email"),
        "login_id": user_doc.get("login_id"),
        "first_name": user_doc.get("first_name", ""),
        "last_name": user_doc.get("last_name", ""),
        "college_name": user_doc.get("college_name", ""),
    }


def get_profile(db, role, user_id):
    collection = {
        "student": db.student_profiles,
        "faculty": db.faculty_profiles,
        "hod": db.hod_profiles,
        "principal": db.principal_profiles,
        "admin": db.admin_profiles,
    }[role]
    profile = collection.find_one({"user_id": _to_object_id(user_id)})
    if profile:
        profile["id"] = _str_id(profile.pop("_id"))
        profile["user_id"] = _str_id(profile["user_id"])
    return profile


def list_students_by_branch_sem(db, branch, sem):
    branch = branch.strip().upper()
    sem = int(sem)
    pipeline = [
        {"$match": {"branch": branch, "sem": sem}},
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "_id",
                "as": "user",
            }
        },
        {"$unwind": "$user"},
        {
            "$project": {
                "_id": 0,
                "user_id": {"$toString": "$user_id"},
                "enrollment_no": 1,
                "first_name": "$user.first_name",
                "last_name": "$user.last_name",
                "branch": 1,
                "sem": 1,
            }
        },
    ]
    return list(db.student_profiles.aggregate(pipeline))


def _subject_name_map(db, branch, sem):
    records = db.subjects.find({"branch": branch, "sem": sem}, {"_id": 0, "subject_number": 1, "subject_name": 1})
    return {item["subject_number"]: item["subject_name"] for item in records}


def get_student_progress(db, student_user_id, sem):
    sem = int(sem)
    student_user_id = _to_object_id(student_user_id)
    student = db.student_profiles.find_one({"user_id": student_user_id})
    if not student:
        return {"rows": [], "total": 0, "percentage": 0.0}

    branch = student["branch"]
    marks = list(db.marks.find({"student_user_id": student_user_id, "branch": branch, "sem": sem}))
    subject_map = _subject_name_map(db, branch, sem)

    rows = []
    total = 0
    max_total = 0
    for mark in marks:
        subject_total = int(mark.get("pa1", 0)) + int(mark.get("pa2", 0)) + int(mark.get("practical", 0)) + int(mark.get("gtu", 0))
        rows.append(
            {
                "subject_number": mark["subject_number"],
                "subject_name": subject_map.get(mark["subject_number"], "Unknown Subject"),
                "pa1": int(mark.get("pa1", 0)),
                "pa2": int(mark.get("pa2", 0)),
                "practical": int(mark.get("practical", 0)),
                "gtu": int(mark.get("gtu", 0)),
                "total": subject_total,
            }
        )
        total += subject_total
        max_total += 100

    percentage = round((total / max_total) * 100, 2) if max_total else 0.0
    return {"rows": rows, "total": total, "percentage": percentage}


def upsert_mark(db, faculty_user_id, student_user_id, branch, sem, subject_number, scores):
    branch = branch.strip().upper()
    subject_number = subject_number.strip().upper()
    sem = int(sem)
    student_user_id = _to_object_id(student_user_id)

    payload = {
        "student_user_id": student_user_id,
        "branch": branch,
        "sem": sem,
        "subject_number": subject_number,
        "pa1": max(0, min(25, int(scores.get("pa1", 0)))),
        "pa2": max(0, min(25, int(scores.get("pa2", 0)))),
        "practical": max(0, min(25, int(scores.get("practical", 0)))),
        "gtu": max(0, min(25, int(scores.get("gtu", 0)))),
        "updated_by": _to_object_id(faculty_user_id),
        "updated_at": _utcnow(),
    }

    db.marks.update_one(
        {
            "student_user_id": student_user_id,
            "branch": branch,
            "sem": sem,
            "subject_number": subject_number,
        },
        {
            "$set": payload,
            "$setOnInsert": {"created_at": _utcnow()},
        },
        upsert=True,
    )


def get_class_marks(db, branch, sem, subject_number):
    students = list_students_by_branch_sem(db, branch, sem)
    marks = list(
        db.marks.find(
            {
                "branch": branch.strip().upper(),
                "sem": int(sem),
                "subject_number": subject_number.strip().upper(),
            }
        )
    )
    marks_by_student = {str(item["student_user_id"]): item for item in marks}
    rows = []
    for student in students:
        mark = marks_by_student.get(student["user_id"], {})
        rows.append(
            {
                **student,
                "pa1": int(mark.get("pa1", 0)),
                "pa2": int(mark.get("pa2", 0)),
                "practical": int(mark.get("practical", 0)),
                "gtu": int(mark.get("gtu", 0)),
            }
        )
    return rows


def aggregate_branch_progress(db, branch, sem):
    branch = branch.strip().upper()
    sem = int(sem)
    students = list_students_by_branch_sem(db, branch, sem)

    chart = []
    for student in students:
        progress = get_student_progress(db, student["user_id"], sem)
        chart.append(
            {
                "name": f"{student['first_name']} {student['last_name']}",
                "percentage": progress["percentage"],
            }
        )
    return chart


def aggregate_all_branch_progress(db, sem):
    sem = int(sem)
    branches = db.student_profiles.distinct("branch", {"sem": sem})

    data = []
    for branch in sorted(branches):
        branch_students = list_students_by_branch_sem(db, branch, sem)
        if not branch_students:
            continue
        percentages = [get_student_progress(db, student["user_id"], sem)["percentage"] for student in branch_students]
        average = round(sum(percentages) / len(percentages), 2) if percentages else 0.0
        data.append({"branch": branch, "average_percentage": average})
    return data


def list_users(db):
    users = []
    for user in db.users.find({}, {"password_hash": 0}).sort("created_at", -1):
        user["id"] = _str_id(user.pop("_id"))
        users.append(user)
    return users


def list_subjects(db):
    subjects = []
    for subject in db.subjects.find({}).sort([("branch", 1), ("sem", 1), ("subject_number", 1)]):
        subject["id"] = _str_id(subject.pop("_id"))
        subjects.append(subject)
    return subjects


def upsert_subject(db, payload):
    db.subjects.update_one(
        {
            "subject_number": payload["subject_number"].strip().upper(),
            "branch": payload["branch"].strip().upper(),
            "sem": int(payload["sem"]),
        },
        {
            "$set": {
                "subject_name": payload["subject_name"].strip(),
                "updated_at": _utcnow(),
            },
            "$setOnInsert": {"created_at": _utcnow()},
        },
        upsert=True,
    )


def upsert_branch_access(db, faculty_user_id, branches):
    faculty_user_id = _to_object_id(faculty_user_id)
    db.branch_access.delete_many({"faculty_user_id": faculty_user_id})
    clean = [branch.strip().upper() for branch in branches if branch.strip()]
    if clean:
        db.branch_access.insert_many(
            [{"faculty_user_id": faculty_user_id, "branch": branch, "created_at": _utcnow()} for branch in sorted(set(clean))]
        )

    db.faculty_profiles.update_one(
        {"user_id": faculty_user_id},
        {
            "$set": {
                "branches": sorted(set(clean)),
                "updated_at": _utcnow(),
            }
        },
    )
