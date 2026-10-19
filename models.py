from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="Student")  # Admin | Teacher | Student
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.String(20), unique=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    course = db.Column(db.String(100), default="")
    phone = db.Column(db.String(30), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    attendance = db.relationship("Attendance", backref="student", cascade="all, delete-orphan")
    marks = db.relationship("Mark", backref="student", cascade="all, delete-orphan")

    @property
    def attendance_pct(self):
        total = len(self.attendance)
        if not total:
            return None
        present = sum(1 for a in self.attendance if a.status in ("Present", "Late"))
        return round(present * 100 / total, 1)


class Attendance(db.Model):
    __table_args__ = (db.UniqueConstraint("student_id", "date"),)
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(10), nullable=False)  # Present | Absent | Late


class Mark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Float, nullable=False)
    max_score = db.Column(db.Float, nullable=False, default=100)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def percent(self):
        return round(self.score * 100 / self.max_score, 1) if self.max_score else 0
