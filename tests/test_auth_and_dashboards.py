from app.db import get_db
from app.services.user_service import create_user, upsert_mark


def test_student_registration_and_login(client):
    register_response = client.post(
        "/auth/register?role=student",
        data={
            "enrollment_no": "23CS777",
            "password": "pass123",
            "email": "s777@example.com",
            "branch": "cse",
            "sem": "3",
            "first_name": "Test",
            "last_name": "Student",
            "college_name": "ABC",
        },
        follow_redirects=True,
    )
    assert register_response.status_code == 200
    assert b"Registration successful" in register_response.data

    login_response = client.post(
        "/auth/login?role=student",
        data={"identifier": "23cs777", "password": "pass123"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200
    assert b"Student Dashboard" in login_response.data


def test_faculty_mark_entry_updates_student_dashboard(app, client):
    db = get_db(app)
    student_id, _ = create_user(
        db,
        "student",
        {
            "enrollment_no": "23CS001",
            "password": "student123",
            "email": "student@example.com",
            "branch": "CSE",
            "sem": 5,
            "first_name": "Amit",
            "last_name": "Patel",
            "college_name": "ABC",
        },
    )
    faculty_id, _ = create_user(
        db,
        "faculty",
        {
            "email": "faculty@example.com",
            "password": "faculty123",
            "number_of_subjects": 1,
            "subject_name": "DBMS",
            "subject_number": "DB301",
            "sem": 5,
            "branch": "CSE",
            "branches": "CSE",
            "first_name": "Rina",
            "last_name": "Shah",
            "college_name": "ABC",
        },
    )

    upsert_mark(db, faculty_id, student_id, "CSE", 5, "DB301", {"pa1": 20, "pa2": 21, "practical": 22, "gtu": 23})

    login_response = client.post(
        "/auth/login?role=student",
        data={"identifier": "23CS001", "password": "student123"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200
    assert b"DBMS" in login_response.data
    assert b"86" in login_response.data
