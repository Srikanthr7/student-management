"""
EduTrack Pro — SQLAlchemy Models
All database tables defined here following MVC pattern.
"""
from datetime import datetime, date
from extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # admin, teacher, student
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student_profile = db.relationship('Student', back_populates='user', uselist=False,
                                       foreign_keys='Student.user_id')
    notifications = db.relationship('Notification', back_populates='user',
                                     foreign_keys='Notification.user_id', lazy='dynamic')
    marks_entered = db.relationship('Mark', back_populates='entered_by_user',
                                     foreign_keys='Mark.entered_by')
    attendance_marked = db.relationship('Attendance', back_populates='marked_by_user',
                                         foreign_keys='Attendance.marked_by')

    def __init__(self, username: str, email: str, role: str = 'student', **kwargs):
        super().__init__(username=username, email=email, role=role, **kwargs)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def is_admin(self) -> bool:
        return self.role == 'admin'

    def is_teacher(self) -> bool:
        return self.role == 'teacher'

    def is_student_role(self) -> bool:
        return self.role == 'student'

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ---------------------------------------------------------------------------
# Departments
# ---------------------------------------------------------------------------
class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    head_of_dept = db.Column(db.String(120), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    students = db.relationship('Student', back_populates='department', lazy='dynamic')
    subjects = db.relationship('Subject', back_populates='department', lazy='dynamic')

    def student_count(self):
        return self.students.count()

    def __repr__(self):
        return f'<Department {self.code}: {self.name}>'


# ---------------------------------------------------------------------------
# Students
# ---------------------------------------------------------------------------
class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False, index=True)
    roll_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False, default=1)
    semester = db.Column(db.Integer, nullable=False, default=1)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    photo_filename = db.Column(db.String(255), nullable=True)     # legacy: local filename
    photo_url = db.Column(db.String(500), nullable=True)           # Cloudinary secure URL
    photo_public_id = db.Column(db.String(255), nullable=True)     # Cloudinary public_id (for deletion)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    department = db.relationship('Department', back_populates='students')
    user = db.relationship('User', back_populates='student_profile', foreign_keys=[user_id])
    attendance_records = db.relationship('Attendance', back_populates='student', lazy='dynamic',
                                          cascade='all, delete-orphan')
    marks = db.relationship('Mark', back_populates='student', lazy='dynamic',
                             cascade='all, delete-orphan')
    uploaded_files = db.relationship('UploadedFile', back_populates='student', lazy='dynamic',
                                      cascade='all, delete-orphan')

    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None

    def attendance_percentage(self, subject_id=None):
        query = self.attendance_records
        if subject_id:
            query = query.filter_by(subject_id=subject_id)
        total = query.count()
        if total == 0:
            return 0.0
        present = query.filter(Attendance.status.in_(['present', 'late'])).count()
        return round((present / total) * 100, 2)

    def calculate_cgpa(self):
        from sqlalchemy import func
        marks = self.marks.all()
        if not marks:
            return 0.0
        subject_grades = {}
        for mark in marks:
            key = mark.subject_id
            pct = (mark.marks_obtained / mark.max_marks) * 100 if mark.max_marks > 0 else 0
            gp = _percentage_to_grade_point(pct)
            if key not in subject_grades or gp > subject_grades[key]:
                subject_grades[key] = gp
        if not subject_grades:
            return 0.0
        return round(sum(subject_grades.values()) / len(subject_grades), 2)

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'full_name': self.full_name,
            'roll_number': self.roll_number,
            'department': self.department.name if self.department else None,
            'year': self.year,
            'semester': self.semester,
            'email': self.email,
            'phone': self.phone,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'attendance_percentage': self.attendance_percentage(),
            'cgpa': self.calculate_cgpa(),
        }

    def __repr__(self):
        return f'<Student {self.student_id}: {self.full_name}>'


def _percentage_to_grade_point(pct: float) -> float:
    if pct >= 90: return 4.0
    if pct >= 80: return 3.7
    if pct >= 75: return 3.3
    if pct >= 70: return 3.0
    if pct >= 65: return 2.7
    if pct >= 60: return 2.3
    if pct >= 55: return 2.0
    if pct >= 50: return 1.7
    if pct >= 45: return 1.3
    if pct >= 40: return 1.0
    return 0.0


# ---------------------------------------------------------------------------
# Subjects
# ---------------------------------------------------------------------------
class Subject(db.Model):
    __tablename__ = 'subjects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    credits = db.Column(db.Integer, default=3, nullable=False)
    semester = db.Column(db.Integer, nullable=False, default=1)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    department = db.relationship('Department', back_populates='subjects')
    teacher = db.relationship('User', foreign_keys=[teacher_id])
    attendance_records = db.relationship('Attendance', back_populates='subject', lazy='dynamic')
    marks = db.relationship('Mark', back_populates='subject', lazy='dynamic')

    def __repr__(self):
        return f'<Subject {self.code}: {self.name}>'


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------
class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    status = db.Column(db.String(10), nullable=False, default='present')  # present, absent, late
    marked_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    remarks = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    student = db.relationship('Student', back_populates='attendance_records')
    subject = db.relationship('Subject', back_populates='attendance_records')
    marked_by_user = db.relationship('User', back_populates='attendance_marked', foreign_keys=[marked_by])

    __table_args__ = (
        db.UniqueConstraint('student_id', 'subject_id', 'date', name='uq_attendance'),
    )

    def __repr__(self):
        return f'<Attendance student={self.student_id} date={self.date} status={self.status}>'


# ---------------------------------------------------------------------------
# Marks
# ---------------------------------------------------------------------------
class Mark(db.Model):
    __tablename__ = 'marks'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    exam_type = db.Column(db.String(30), nullable=False, default='midterm')  # midterm, final, internal, assignment
    marks_obtained = db.Column(db.Float, nullable=False, default=0.0)
    max_marks = db.Column(db.Float, nullable=False, default=100.0)
    semester = db.Column(db.Integer, nullable=False, default=1)
    academic_year = db.Column(db.String(10), nullable=False, default='2024-25')
    entered_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', back_populates='marks')
    subject = db.relationship('Subject', back_populates='marks')
    entered_by_user = db.relationship('User', back_populates='marks_entered', foreign_keys=[entered_by])

    @property
    def percentage(self):
        return round((self.marks_obtained / self.max_marks) * 100, 2) if self.max_marks > 0 else 0

    @property
    def grade(self):
        p = self.percentage
        if p >= 90: return 'O'
        if p >= 80: return 'A+'
        if p >= 75: return 'A'
        if p >= 70: return 'B+'
        if p >= 65: return 'B'
        if p >= 60: return 'C+'
        if p >= 55: return 'C'
        if p >= 50: return 'D'
        if p >= 40: return 'E'
        return 'F'

    @property
    def grade_point(self):
        return _percentage_to_grade_point(self.percentage)

    @property
    def is_pass(self):
        return self.percentage >= 40

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'subject': self.subject.name if self.subject else None,
            'exam_type': self.exam_type,
            'marks_obtained': self.marks_obtained,
            'max_marks': self.max_marks,
            'percentage': self.percentage,
            'grade': self.grade,
            'grade_point': self.grade_point,
            'is_pass': self.is_pass,
            'semester': self.semester,
            'academic_year': self.academic_year,
        }

    def __repr__(self):
        return f'<Mark student={self.student_id} subject={self.subject_id} {self.marks_obtained}/{self.max_marks}>'


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------
class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), nullable=False, default='info')  # info, warning, success, danger
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    link = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = db.relationship('User', back_populates='notifications', foreign_keys=[user_id])

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'is_read': self.is_read,
            'link': self.link,
            'created_at': self.created_at.isoformat(),
        }

    def __repr__(self):
        return f'<Notification user={self.user_id} title={self.title}>'


# ---------------------------------------------------------------------------
# Uploaded Files
# ---------------------------------------------------------------------------
class UploadedFile(db.Model):
    __tablename__ = 'uploaded_files'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)              # legacy: local stored filename
    original_name = db.Column(db.String(255), nullable=False)         # original upload name
    file_type = db.Column(db.String(30), nullable=False, default='document')  # photo, document, certificate, resume
    file_size = db.Column(db.Integer, nullable=True)                  # bytes
    cloudinary_url = db.Column(db.String(500), nullable=True)         # Cloudinary secure URL
    cloudinary_public_id = db.Column(db.String(255), nullable=True)   # Cloudinary public_id (for deletion)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    student = db.relationship('Student', back_populates='uploaded_files')
    uploader = db.relationship('User', foreign_keys=[uploaded_by])

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'filename': self.filename,
            'original_name': self.original_name,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'uploaded_at': self.uploaded_at.isoformat(),
        }

    def __repr__(self):
        return f'<UploadedFile {self.original_name} ({self.file_type})>'
