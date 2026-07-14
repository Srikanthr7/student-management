"""
REST API routes — JWT-protected JSON API v1.
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from datetime import datetime

from extensions import db, limiter
from models import User, Student, Department, Attendance, Mark, Subject, Notification

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')


def api_response(data=None, message='', status=200, error=None):
    resp = {'status': 'success' if not error else 'error', 'message': message}
    if data is not None:
        resp['data'] = data
    if error:
        resp['error'] = error
    return jsonify(resp), status


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------
@api_bp.route('/auth/token', methods=['POST'])
@limiter.limit("10 per minute")
def get_token():
    """Obtain JWT access + refresh tokens.
    ---
    POST /api/v1/auth/token
    Body: { "username": "...", "password": "..." }
    """
    data = request.get_json()
    if not data:
        return api_response(error='JSON body required', status=400)

    username = data.get('username', '')
    password = data.get('password', '')

    user = User.query.filter(
        (User.username == username) | (User.email == username)
    ).first()

    if not user or not user.is_active or not user.check_password(password):
        return api_response(error='Invalid credentials', status=401)

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={'role': user.role, 'username': user.username}
    )
    refresh_token = create_refresh_token(identity=str(user.id))

    return api_response(
        data={
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {'id': user.id, 'username': user.username, 'role': user.role}
        },
        message='Token issued successfully'
    )


@api_bp.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    identity = get_jwt_identity()
    user = db.session.get(User, int(identity))
    if not user:
        return api_response(error='User not found', status=404)
    access_token = create_access_token(
        identity=identity,
        additional_claims={'role': user.role, 'username': user.username}
    )
    return api_response(data={'access_token': access_token}, message='Token refreshed')


# ---------------------------------------------------------------------------
# Students API
# ---------------------------------------------------------------------------
@api_bp.route('/students', methods=['GET'])
@jwt_required()
def api_students():
    """List all students with optional filters."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    dept_id = request.args.get('dept_id', type=int)

    query = Student.query.filter_by(is_active=True)
    if search:
        from sqlalchemy import or_
        query = query.filter(
            or_(
                Student.full_name.ilike(f'%{search}%'),
                Student.roll_number.ilike(f'%{search}%'),
                Student.email.ilike(f'%{search}%'),
            )
        )
    if dept_id:
        query = query.filter_by(department_id=dept_id)

    pagination = query.order_by(Student.full_name).paginate(
        page=page, per_page=min(per_page, 100), error_out=False
    )

    return api_response(data={
        'students': [s.to_dict() for s in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
    })


@api_bp.route('/students/<int:student_id>', methods=['GET'])
@jwt_required()
def api_student_detail(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        return api_response(error='Student not found', status=404)
    return api_response(data=student.to_dict())


@api_bp.route('/students', methods=['POST'])
@jwt_required()
def api_create_student():
    claims = get_jwt()
    if claims.get('role') not in ('admin', 'teacher'):
        return api_response(error='Insufficient permissions', status=403)

    data = request.get_json()
    if not data:
        return api_response(error='JSON body required', status=400)

    required = ['full_name', 'roll_number', 'department_id', 'email']
    for field in required:
        if not data.get(field):
            return api_response(error=f'Field "{field}" is required', status=422)

    if Student.query.filter_by(roll_number=data['roll_number']).first():
        return api_response(error='Roll number already exists', status=409)
    if Student.query.filter_by(email=data['email']).first():
        return api_response(error='Email already exists', status=409)

    from services.student_service import generate_student_id
    student = Student(
        student_id=generate_student_id(),
        full_name=data['full_name'],
        roll_number=data['roll_number'],
        department_id=data['department_id'],
        year=data.get('year', 1),
        semester=data.get('semester', 1),
        email=data['email'],
        phone=data.get('phone', ''),
        address=data.get('address', ''),
    )
    db.session.add(student)
    db.session.commit()
    return api_response(data=student.to_dict(), message='Student created', status=201)


@api_bp.route('/students/<int:student_id>', methods=['PUT'])
@jwt_required()
def api_update_student(student_id):
    claims = get_jwt()
    if claims.get('role') not in ('admin', 'teacher'):
        return api_response(error='Insufficient permissions', status=403)

    student = db.session.get(Student, student_id)
    if not student:
        return api_response(error='Student not found', status=404)

    data = request.get_json() or {}
    for field in ['full_name', 'email', 'phone', 'address', 'year', 'semester']:
        if field in data:
            setattr(student, field, data[field])
    db.session.commit()
    return api_response(data=student.to_dict(), message='Student updated')


@api_bp.route('/students/<int:student_id>', methods=['DELETE'])
@jwt_required()
def api_delete_student(student_id):
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return api_response(error='Admin access required', status=403)

    student = db.session.get(Student, student_id)
    if not student:
        return api_response(error='Student not found', status=404)

    student.is_active = False
    db.session.commit()
    return api_response(message='Student deactivated')


# ---------------------------------------------------------------------------
# Departments API
# ---------------------------------------------------------------------------
@api_bp.route('/departments', methods=['GET'])
@jwt_required()
def api_departments():
    depts = Department.query.order_by(Department.name).all()
    return api_response(data=[{
        'id': d.id, 'name': d.name, 'code': d.code,
        'head_of_dept': d.head_of_dept, 'student_count': d.student_count()
    } for d in depts])


# ---------------------------------------------------------------------------
# Attendance API
# ---------------------------------------------------------------------------
@api_bp.route('/attendance', methods=['GET'])
@jwt_required()
def api_attendance():
    student_id = request.args.get('student_id', type=int)
    subject_id = request.args.get('subject_id', type=int)

    query = Attendance.query
    if student_id:
        query = query.filter_by(student_id=student_id)
    if subject_id:
        query = query.filter_by(subject_id=subject_id)

    records = query.order_by(Attendance.date.desc()).limit(100).all()
    return api_response(data=[{
        'id': r.id,
        'student_id': r.student_id,
        'subject_id': r.subject_id,
        'date': r.date.isoformat(),
        'status': r.status,
    } for r in records])


# ---------------------------------------------------------------------------
# Marks API
# ---------------------------------------------------------------------------
@api_bp.route('/marks', methods=['GET'])
@jwt_required()
def api_marks():
    student_id = request.args.get('student_id', type=int)
    query = Mark.query
    if student_id:
        query = query.filter_by(student_id=student_id)
    marks = query.order_by(Mark.created_at.desc()).limit(200).all()
    return api_response(data=[m.to_dict() for m in marks])


# ---------------------------------------------------------------------------
# Statistics API
# ---------------------------------------------------------------------------
@api_bp.route('/stats', methods=['GET'])
@jwt_required()
def api_stats():
    from datetime import date
    first_day = date.today().replace(day=1)
    return api_response(data={
        'total_students': Student.query.filter_by(is_active=True).count(),
        'total_departments': Department.query.count(),
        'new_this_month': Student.query.filter(Student.created_at >= first_day).count(),
        'total_subjects': Subject.query.count(),
    })


# ---------------------------------------------------------------------------
# API Documentation
# ---------------------------------------------------------------------------
@api_bp.route('/docs', methods=['GET'])
def api_docs():
    from flask import render_template
    return render_template('api_docs.html')
