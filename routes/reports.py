"""
Reports routes — Excel/PDF export for students, attendance, marks.
"""
import io
from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for
from flask_login import login_required

from extensions import db
from models import Student, Department, Attendance, Mark, Subject

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


@reports_bp.route('/')
@login_required
def index():
    departments = Department.query.order_by(Department.name).all()
    total_students = Student.query.filter_by(is_active=True).count()
    return render_template('reports/index.html',
                           departments=departments,
                           total_students=total_students)


@reports_bp.route('/students/excel')
@login_required
def export_students_excel():
    from services.report_service import generate_students_excel
    dept_id = request.args.get('dept_id', type=int)

    query = Student.query.filter_by(is_active=True)
    if dept_id:
        query = query.filter_by(department_id=dept_id)

    students = query.order_by(Student.full_name).all()
    output = generate_students_excel(students)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='students_report.xlsx',
    )


@reports_bp.route('/students/pdf')
@login_required
def export_students_pdf():
    from services.report_service import generate_students_pdf
    dept_id = request.args.get('dept_id', type=int)

    query = Student.query.filter_by(is_active=True)
    if dept_id:
        query = query.filter_by(department_id=dept_id)

    students = query.order_by(Student.full_name).all()
    dept = db.session.get(Department, dept_id) if dept_id else None
    output = generate_students_pdf(students, dept)
    return send_file(
        output,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='students_report.pdf',
    )


@reports_bp.route('/attendance/excel')
@login_required
def export_attendance_excel():
    from services.report_service import generate_attendance_excel
    dept_id = request.args.get('dept_id', type=int)
    subject_id = request.args.get('subject_id', type=int)
    month_str = request.args.get('month', '')

    output = generate_attendance_excel(dept_id, subject_id, month_str)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='attendance_report.xlsx',
    )


@reports_bp.route('/marks/excel')
@login_required
def export_marks_excel():
    from services.report_service import generate_marks_excel
    dept_id = request.args.get('dept_id', type=int)
    semester = request.args.get('semester', type=int)
    academic_year = request.args.get('academic_year', '2024-25')

    output = generate_marks_excel(dept_id, semester, academic_year)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='marks_report.xlsx',
    )


@reports_bp.route('/marksheet/<int:student_id>/pdf')
@login_required
def student_marksheet_pdf(student_id):
    from services.report_service import generate_marksheet_pdf
    student = db.session.get(Student, student_id)
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('reports.index'))

    semester = request.args.get('semester', type=int)
    academic_year = request.args.get('academic_year', '2024-25')
    output = generate_marksheet_pdf(student, semester, academic_year)
    return send_file(
        output,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'marksheet_{student.student_id}.pdf',
    )
