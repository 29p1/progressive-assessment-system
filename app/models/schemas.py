ROLES = {"student", "faculty", "hod", "principal", "admin"}

REQUIRED_FIELDS = {
    "student": [
        "enrollment_no",
        "password",
        "email",
        "branch",
        "sem",
        "first_name",
        "last_name",
        "college_name",
    ],
    "faculty": [
        "email",
        "password",
        "number_of_subjects",
        "first_name",
        "last_name",
        "college_name",
    ],
    "hod": ["password", "email", "branch", "first_name", "last_name", "college_name"],
    "principal": ["password", "email", "first_name", "last_name", "college_name"],
    "admin": ["password", "email", "first_name", "last_name"],
}
