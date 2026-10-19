import os
import secrets
from datetime import date, datetime
from functools import wraps

from flask import (Flask, abort, flash, redirect, render_template, request,
                   session, url_for)
from sqlalchemy import or_
from werkzeug.security import check_password_hash, generate_password_hash

from models import Attendance, Mark, Student, User, db

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
    SQLALCHEMY_DATABASE_URI="sqlite:///sms.db",  # stored in ./instance/sms.db
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
db.init_app(app)

ROLES = ["Admin", "Teacher", "Student"]
STAFF = ["Admin", "Teacher"]


# ---------- security helpers ----------
@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.get("_csrf")
        if not token or token != request.form.get("_csrf"):
            abort(400, "Invalid or missing CSRF token. Reload the page and try again.")


@app.context_processor
def inject_globals():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return {"csrf_token": session["_csrf"], "today": date.today().isoformat()}


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def role_required(roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to continue.", "error")
                return redirect(url_for("login"))
            if session.get("role") not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator


def home_for(role):
    return url_for("dashboard") if role in STAFF else url_for("portal")


@app.errorhandler(403)
def forbidden(_):
    return render_template("error.html", code=403,
                           message="Your role doesn't have access to this page."), 403


@app.errorhandler(400)
def bad_request(e):
    return render_template("error.html", code=400, message=e.description), 400


@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", code=404, message="That page doesn't exist."), 404


# ---------- auth ----------
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(home_for(session["role"]))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        role = request.form.get("role", "")

        error = None
        if not name or not email or not password:
            error = "All fields are required."
        elif role not in ROLES:
            error = "Choose a valid role."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        elif password != confirm:
            error = "Passwords do not match."
        elif User.query.filter_by(email=email).first():
            error = "An account with this email already exists."

        if error:
            flash(error, "error")
            return render_template("register.html", roles=ROLES, form=request.form), 400

        db.session.add(User(name=name, email=email, role=role,
                            password_hash=generate_password_hash(password)))
        db.session.commit()
        flash("Account created. You can log in now.", "success")
        return redirect(url_for("login"))
    return render_template("register.html", roles=ROLES, form={})


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session["user_id"] = user.id
            session["role"] = user.role
            session["name"] = user.name
            session["email"] = user.email
            flash(f"Welcome back, {user.name}.", "success")
            return redirect(home_for(user.role))
        flash("Incorrect email or password.", "error")
        return render_template("login.html", email=email), 401
    if "user_id" in session:
        return redirect(home_for(session["role"]))
    return render_template("login.html", email="")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- dashboards ----------
@app.route("/dashboard")
@role_required(STAFF)
def dashboard():
    total_att = Attendance.query.count()
    present = Attendance.query.filter(Attendance.status.in_(["Present", "Late"])).count()
    stats = {
        "students": Student.query.count(),
        "teachers": User.query.filter_by(role="Teacher").count(),
        "attendance": round(present * 100 / total_att, 1) if total_att else None,
        "marks": Mark.query.count(),
    }
    recent = Student.query.order_by(Student.created_at.desc()).limit(5).all()
    return render_template("dashboard.html", stats=stats, recent=recent)


@app.route("/portal")
@role_required(["Student"])
def portal():
    student = Student.query.filter_by(email=session["email"]).first()
    records = []
    if student:
        records = sorted(student.attendance, key=lambda a: a.date, reverse=True)[:10]
    return render_template("student_portal.html", student=student, records=records)


# ---------- students CRUD ----------
@app.route("/students")
@role_required(STAFF)
def students():
    q = request.args.get("q", "").strip()
    query = Student.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Student.name.ilike(like), Student.email.ilike(like),
                                 Student.roll_no.ilike(like), Student.course.ilike(like)))
    return render_template("students.html", students=query.order_by(Student.name).all(), q=q)


@app.route("/students/add", methods=["POST"])
@role_required(STAFF)
def add_student():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    if not name or not email:
        flash("Name and email are required.", "error")
    elif Student.query.filter_by(email=email).first():
        flash("A student with this email already exists.", "error")
    else:
        s = Student(name=name, email=email,
                    course=request.form.get("course", "").strip(),
                    phone=request.form.get("phone", "").strip())
        db.session.add(s)
        db.session.flush()
        s.roll_no = f"STU{s.id:04d}"
        db.session.commit()
        flash(f"{s.name} added as {s.roll_no}.", "success")
    return redirect(url_for("students"))


@app.route("/students/<int:sid>/edit", methods=["POST"])
@role_required(STAFF)
def edit_student(sid):
    s = db.get_or_404(Student, sid)
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    clash = Student.query.filter(Student.email == email, Student.id != sid).first()
    if not name or not email:
        flash("Name and email are required.", "error")
    elif clash:
        flash("Another student already uses this email.", "error")
    else:
        s.name, s.email = name, email
        s.course = request.form.get("course", "").strip()
        s.phone = request.form.get("phone", "").strip()
        db.session.commit()
        flash("Student updated.", "success")
    return redirect(url_for("students"))


@app.route("/students/<int:sid>/delete", methods=["POST"])
@role_required(["Admin"])
def delete_student(sid):
    s = db.get_or_404(Student, sid)
    db.session.delete(s)
    db.session.commit()
    flash("Student deleted along with their attendance and marks.", "success")
    return redirect(url_for("students"))


@app.route("/students/<int:sid>")
@role_required(STAFF)
def student_detail(sid):
    s = db.get_or_404(Student, sid)
    records = sorted(s.attendance, key=lambda a: a.date, reverse=True)[:10]
    return render_template("student_portal.html", student=s, records=records, staff_view=True)


# ---------- attendance ----------
@app.route("/attendance", methods=["GET", "POST"])
@role_required(STAFF)
def attendance():
    raw = request.values.get("date") or date.today().isoformat()
    try:
        day = datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        flash("Invalid date.", "error")
        return redirect(url_for("attendance"))

    all_students = Student.query.order_by(Student.name).all()
    if request.method == "POST":
        existing = {a.student_id: a for a in Attendance.query.filter_by(date=day)}
        for s in all_students:
            status = request.form.get(f"status_{s.id}")
            if status not in ("Present", "Absent", "Late"):
                continue
            if s.id in existing:
                existing[s.id].status = status
            else:
                db.session.add(Attendance(student_id=s.id, date=day, status=status))
        db.session.commit()
        flash(f"Attendance saved for {day:%d %b %Y}.", "success")
        return redirect(url_for("attendance", date=day.isoformat()))

    current = {a.student_id: a.status for a in Attendance.query.filter_by(date=day)}
    return render_template("attendance.html", students=all_students, current=current,
                           day=day.isoformat())


# ---------- marks ----------
@app.route("/marks", methods=["GET", "POST"])
@role_required(STAFF)
def marks():
    if request.method == "POST":
        try:
            student_id = int(request.form["student_id"])
            score = float(request.form["score"])
            max_score = float(request.form.get("max_score") or 100)
            subject = request.form.get("subject", "").strip()
            if not subject or max_score <= 0 or not 0 <= score <= max_score:
                raise ValueError
            db.get_or_404(Student, student_id)
        except (KeyError, ValueError):
            flash("Enter a subject and a score between 0 and the maximum.", "error")
        else:
            db.session.add(Mark(student_id=student_id, subject=subject,
                                score=score, max_score=max_score))
            db.session.commit()
            flash("Marks recorded.", "success")
        return redirect(url_for("marks"))
    return render_template(
        "marks.html",
        students=Student.query.order_by(Student.name).all(),
        marks=Mark.query.order_by(Mark.created_at.desc()).limit(100).all())


@app.route("/marks/<int:mid>/delete", methods=["POST"])
@role_required(STAFF)
def delete_mark(mid):
    db.session.delete(db.get_or_404(Mark, mid))
    db.session.commit()
    flash("Mark removed.", "success")
    return redirect(url_for("marks"))


# ---------- setup ----------
@app.cli.command("init-db")
def init_db():
    """Create all database tables."""
    db.create_all()
    print("Database initialised.")


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
