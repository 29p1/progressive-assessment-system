# Progressive Assessment System (Flask + MongoDB)

A role-based academic progress portal with five roles:
- student
- faculty
- hod
- principal
- admin

## Features
- Secure password hashing with Werkzeug
- Session-based authentication
- Role-aware registration and login
- Student dashboard with semester selector, cards, marksheet, and Chart.js graph
- Faculty dashboard for class/subject-wise mark entry
- HOD analytics page for branch progress
- Principal analytics page for all-branch progress
- Admin dashboard for users, subjects, and faculty branch access

## Project structure
```
app/
  models/
  routes/
  services/
  templates/
  static/
scripts/
tests/
run.py
requirements.txt
```

## MongoDB collections
- users
- student_profiles
- faculty_profiles
- hod_profiles
- principal_profiles
- admin_profiles
- subjects
- marks
- branch_access

## Setup
1. Create a Python virtual environment and activate it.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment variables (optional):
   - `SECRET_KEY`
   - `MONGO_URI` (default: `mongodb://localhost:27017`)
   - `MONGO_DB_NAME` (default: `progressive_assessment`)
   - For production, always set a strong `SECRET_KEY`.
4. Run the app:
   ```bash
   python run.py
   ```
5. Open `http://127.0.0.1:5000`

## Seed sample data
```bash
python scripts/seed.py
```

## Run tests
```bash
pytest -q
```
