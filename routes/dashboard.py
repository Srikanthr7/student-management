"""
Dashboard routes — Main analytics and overview.
"""
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, extract
from datetime import datetime, date, timedelta

from extensions import db
from models import Student, Department, Attendance, Mark, User, Notification, Subject

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    # Core stats
    total_students = Student.query.filter_by(is_active=True).count()
    total_departments = Department.query.count()
    total_subjects = Subject.query.count()

    # New registrations this month
    first_day = date.today().replace(day=1)
    new_this_month = Student.query.filter(
        Student.is_active == True,
        Student.created_at >= first_day
    ).count()

    # Overall attendance this month
    month_attendance = Attendance.query.filter(
        Attendance.date >= first_day
    ).all()
    if month_attendance:
        present_count = sum(1 for a in month_attendance if a.status in ('present', 'late'))
        overall_attendance = round((present_count / len(month_attendance)) * 100, 1)
    else:
        overall_attendance = 0.0

    # Low attendance students (< 75%)
    low_attendance_students = []
    active_students = Student.query.filter_by(is_active=True).all()
    for s in active_students:
        pct = s.attendance_percentage()
        if 0 < pct < 75:
            low_attendance_students.append({
                'student': s,
                'percentage': pct
            })
    low_attendance_students.sort(key=lambda x: x['percentage'])
    low_attendance_count = len(low_attendance_students)

    # Recent active students
    recent_students = Student.query.filter_by(is_active=True).order_by(Student.created_at.desc()).limit(5).all()

    # Recent notifications
    recent_notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).limit(5).all()

    # Department distribution for chart
    dept_data = db.session.query(
        Department.name,
        func.count(Student.id).label('count')
    ).outerjoin(Student, (Student.department_id == Department.id) & (Student.is_active == True)).group_by(Department.id).all()

    dept_labels = [d.name for d in dept_data]
    dept_counts = [d.count for d in dept_data]

    # Monthly enrollment for last 6 months
    monthly_labels = []
    monthly_counts = []
    for i in range(5, -1, -1):
        dt = date.today() - timedelta(days=i * 30)
        label = dt.strftime('%b %Y')
        count = Student.query.filter(
            Student.is_active == True,
            extract('month', Student.created_at) == dt.month,
            extract('year', Student.created_at) == dt.year
        ).count()
        monthly_labels.append(label)
        monthly_counts.append(count)


    # Performance distribution
    all_marks = Mark.query.all()
    grade_dist = {'O': 0, 'A+': 0, 'A': 0, 'B+': 0, 'B': 0, 'C': 0, 'F': 0}
    for m in all_marks:
        g = m.grade
        if g in grade_dist:
            grade_dist[g] += 1
        else:
            grade_dist['F'] += 1

    return render_template(
        'dashboard/index.html',
        total_students=total_students,
        total_departments=total_departments,
        total_subjects=total_subjects,
        new_this_month=new_this_month,
        overall_attendance=overall_attendance,
        low_attendance_count=low_attendance_count,
        low_attendance_students=low_attendance_students[:5],
        recent_students=recent_students,
        recent_notifications=recent_notifications,
        dept_labels=dept_labels,
        dept_counts=dept_counts,
        monthly_labels=monthly_labels,
        monthly_counts=monthly_counts,
        grade_dist=grade_dist,
    )


@dashboard_bp.route('/dashboard/chart-data')
@login_required
def chart_data():
    """API endpoint for dynamic chart data."""
    first_day = date.today().replace(day=1)

    # Attendance trend last 7 days
    attendance_trend = []
    for i in range(6, -1, -1):
        d = date.today() - timedelta(days=i)
        records = Attendance.query.filter_by(date=d).all()
        if records:
            present = sum(1 for r in records if r.status in ('present', 'late'))
            pct = round((present / len(records)) * 100, 1)
        else:
            pct = 0
        attendance_trend.append({'date': d.strftime('%a'), 'percentage': pct})

    return jsonify({
        'attendance_trend': attendance_trend,
    })


@dashboard_bp.route('/chatbot', methods=['POST'])
@login_required
def chatbot():
    from flask import request
    from services.ml_service import chatbot_response
    data = request.get_json() or {}
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'response': 'Please say something!'})
    response = chatbot_response(message)
    return jsonify({'response': response})

