# Schoolbook – Student Management System

Flask + SQLAlchemy + SQLite + Tailwind (CDN). Registration, login, role-based access, student CRUD, attendance and marks.

## Run locally
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
flask --app app init-db         # creates instance/sms.db (also happens automatically on first run)
python app.py                   # open http://127.0.0.1:5000
```
Set a real secret before deploying: `export SECRET_KEY="long-random-string"` (Windows: `set SECRET_KEY=...`).

## Roles
- **Admin**: everything, including deleting students.
- **Teacher**: dashboard, add/edit/search students, attendance, marks.
- **Student**: personal portal. Matched to a student record by email, so register with the same email the teacher used.

## Notes
- Passwords are hashed with Werkzeug; all POST forms carry a CSRF token.
- Registration lets anyone pick any role (as specified). For production, restrict Admin/Teacher sign-up (invite code or admin approval).
- Use a production server (e.g. `gunicorn app:app`) instead of `python app.py` when deploying.

## Structure
`app.py` routes and access control · `models.py` User, Student, Attendance, Mark · `templates/` Jinja2 pages
