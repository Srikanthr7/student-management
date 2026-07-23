"""
Attendance routes — Mark, view, monthly reports.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import date, timedelta
from sqlalchemy import func

from extensions import db
from models import Attendance, Student, Subject, Department

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')


@attendance_bp.route('/')
@login_required
def index():
    return redirect(url_for('attendance.mark_attendance'))



@attendance_bp.route('/mark', methods=['GET', 'POST'])
@login_required
def mark_attendance():
    departments = Department.query.order_by(Department.name).all()
    subjects = Subject.query.order_by(Subject.name).all()
    today = date.today()

    selected_dept = request.args.get('dept_id', type=int)
    selected_subject = request.args.get('subject_id', type=int)
    selected_date_str = request.args.get('date', today.isoformat())

    try:
        selected_date = date.fromisoformat(selected_date_str)
    except (ValueError, TypeError):
        selected_date = today

    students = []
    existing_attendance = {}

    if selected_dept and selected_subject:
        students = Student.query.filter_by(
            department_id=selected_dept, is_active=True
        ).order_by(Student.roll_number).all()

        existing = Attendance.query.filter_by(
            subject_id=selected_subject, date=selected_date
        ).all()
        existing_attendance = {a.student_id: a.status for a in existing}

    if request.method == 'POST':
        subject_id = request.form.get('subject_id', type=int)
        att_date_str = request.form.get('date', today.isoformat())
        try:
            att_date = date.fromisoformat(att_date_str)
        except ValueError:
            att_date = today

        student_ids = request.form.getlist('student_ids[]')
        saved = 0

        for sid in student_ids:
            sid = int(sid)
            status = request.form.get(f'status_{sid}', 'absent')
            remarks = request.form.get(f'remarks_{sid}', '')

            existing = Attendance.query.filter_by(
                student_id=sid, subject_id=subject_id, date=att_date
            ).first()

            if existing:
                existing.status = status
                existing.remarks = remarks
                existing.marked_by = current_user.id
            else:
                record = Attendance(
                    student_id=sid,
                    subject_id=subject_id,
                    date=att_date,
                    status=status,
                    remarks=remarks,
                    marked_by=current_user.id,
                )
                db.session.add(record)
            saved += 1

        db.session.commit()
        flash(f'Attendance marked for {saved} students.', 'success')

        # Check low attendance and create notifications
        _check_low_attendance_alerts(subject_id, att_date)

        return redirect(url_for('attendance.mark_attendance',
                                dept_id=request.form.get('dept_id'),
                                subject_id=subject_id,
                                date=att_date_str))

    return render_template(
        'attendance/mark.html',
        departments=departments,
        subjects=subjects,
        students=students,
        selected_dept=selected_dept,
        selected_subject=selected_subject,
        selected_date=selected_date,
        existing_attendance=existing_attendance,
    )


@attendance_bp.route('/report')
@login_required
def report():
    departments = Department.query.order_by(Department.name).all()
    subjects = Subject.query.order_by(Subject.name).all()

    selected_dept = request.args.get('dept_id', type=int)
    selected_subject = request.args.get('subject_id', type=int)
    month_str = request.args.get('month', date.today().strftime('%Y-%m'))

    try:
        year, month = map(int, month_str.split('-'))
    except (ValueError, AttributeError):
        year, month = date.today().year, date.today().month

    report_data = []
    dates_in_month = []

    if selected_dept and selected_subject:
        # Get all dates with attendance in this month/subject
        records = Attendance.query.filter(
            Attendance.subject_id == selected_subject,
            func.extract('year', Attendance.date) == year,
            func.extract('month', Attendance.date) == month,
        ).all()

        dates_in_month = sorted(set(r.date for r in records))
        date_status_map = {(r.student_id, r.date): r.status for r in records}

        students = Student.query.filter_by(
            department_id=selected_dept, is_active=True
        ).order_by(Student.roll_number).all()

        for student in students:
            row = {
                'student': student,
                'statuses': [],
                'present': 0,
                'absent': 0,
                'late': 0,
                'total': len(dates_in_month),
                'percentage': 0.0,
            }
            for d in dates_in_month:
                status = date_status_map.get((student.id, d), '-')
                row['statuses'].append(status)
                if status == 'present': row['present'] += 1
                elif status == 'absent': row['absent'] += 1
                elif status == 'late': row['late'] += 1

            if row['total'] > 0:
                row['percentage'] = round(
                    ((row['present'] + row['late']) / row['total']) * 100, 1
                )
            report_data.append(row)

    return render_template(
        'attendance/report.html',
        departments=departments,
        subjects=subjects,
        selected_dept=selected_dept,
        selected_subject=selected_subject,
        month_str=month_str,
        report_data=report_data,
        dates_in_month=dates_in_month,
    )


@attendance_bp.route('/student/<int:student_id>')
@login_required
def student_attendance(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('students.list_students'))

    records = Attendance.query.filter_by(student_id=student_id).order_by(
        Attendance.date.desc()
    ).all()

    # Group by subject
    from collections import defaultdict
    by_subject = defaultdict(list)
    for r in records:
        by_subject[r.subject].append(r)

    subject_stats = []
    for subj, recs in by_subject.items():
        total = len(recs)
        present = sum(1 for r in recs if r.status in ('present', 'late'))
        pct = round((present / total) * 100, 1) if total > 0 else 0
        subject_stats.append({
            'subject': subj,
            'total': total,
            'present': present,
            'percentage': pct,
            'low': pct < 75,
        })

    return render_template(
        'attendance/student.html',
        student=student,
        subject_stats=subject_stats,
        records=records,
    )


@attendance_bp.route('/api/students-by-dept')
@login_required
def students_by_dept():
    dept_id = request.args.get('dept_id', type=int)
    if not dept_id:
        return jsonify([])
    students = Student.query.filter_by(department_id=dept_id, is_active=True).order_by(
        Student.roll_number
    ).all()
    return jsonify([{'id': s.id, 'name': s.full_name, 'roll': s.roll_number} for s in students])


def _check_low_attendance_alerts(subject_id: int, att_date: date):
    """Create notifications for students with attendance below threshold."""
    from models import Notification
    from flask import current_app

    threshold = current_app.config.get('LOW_ATTENDANCE_THRESHOLD', 75.0)
    students = Student.query.filter_by(is_active=True).all()

    for student in students:
        pct = student.attendance_percentage(subject_id=subject_id)
        if 0 < pct < threshold:
            subject = db.session.get(Subject, subject_id)
            # Check if notification already exists today
            existing = Notification.query.filter(
                Notification.user_id == (student.user_id or 1),
                Notification.title.like(f'%Low Attendance%{subject.name if subject else ""}%'),
                func.date(Notification.created_at) == att_date,
            ).first()

            if not existing and student.user_id:
                notif = Notification(
                    user_id=student.user_id,
                    title=f'Low Attendance Warning',
                    message=f'Your attendance in {subject.name if subject else "subject"} is {pct}%, below the required {threshold}%.',
                    type='warning',
                    link=url_for('attendance.student_attendance', student_id=student.id),
                )
                db.session.add(notif)

    db.session.commit()
