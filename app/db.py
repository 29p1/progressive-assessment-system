from pymongo import MongoClient


def init_db(app):
    if app.config.get("MONGO_DB") is not None:
        db = app.config["MONGO_DB"]
    else:
        client = MongoClient(app.config["MONGO_URI"])
        db = client[app.config["MONGO_DB_NAME"]]
        app.extensions["mongo_client"] = client
    app.extensions["mongo_db"] = db

    db.users.create_index("login_id", unique=True)
    db.users.create_index("email", unique=True, sparse=True)
    db.users.create_index([("role", 1), ("created_at", -1)])
    db.student_profiles.create_index("user_id", unique=True)
    db.faculty_profiles.create_index("user_id", unique=True)
    db.hod_profiles.create_index("user_id", unique=True)
    db.principal_profiles.create_index("user_id", unique=True)
    db.admin_profiles.create_index("user_id", unique=True)
    db.subjects.create_index([("subject_number", 1), ("branch", 1), ("sem", 1)], unique=True)
    db.marks.create_index([("student_user_id", 1), ("branch", 1), ("sem", 1), ("subject_number", 1)], unique=True)
    db.branch_access.create_index([("faculty_user_id", 1), ("branch", 1)], unique=True)


def get_db(app):
    return app.extensions["mongo_db"]
