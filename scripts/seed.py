from app import create_app
from app.db import get_db
from app.services.user_service import create_user, upsert_mark


def seed():
    app = create_app()
    db = get_db(app)

    student_payload = {
        "enrollment_no": "23CS001",
        "password": "student123",
        "email": "student@example.com",
        "branch": "CSE",
        "sem": 5,
        "first_name": "Amit",
        "last_name": "Patel",
        "college_name": "ABC College",
    }
    faculty_payload = {
        "email": "faculty@example.com",
        "password": "faculty123",
        "number_of_subjects": 1,
        "subject_name": "Database Management",
        "subject_number": "DB301",
        "sem": 5,
        "branch": "CSE",
        "branches": "CSE,IT",
        "first_name": "Rina",
        "last_name": "Shah",
        "college_name": "ABC College",
    }

    student_id, _ = create_user(db, "student", student_payload)
    faculty_id, _ = create_user(db, "faculty", faculty_payload)

    if student_id and faculty_id:
        upsert_mark(
            db,
            faculty_id,
            student_id,
            "CSE",
            5,
            "DB301",
            {"pa1": 20, "pa2": 22, "practical": 23, "gtu": 21},
        )


if __name__ == "__main__":
    seed()
    print("Sample data seeded.")
