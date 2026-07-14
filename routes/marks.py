"""
Marks & Performance routes — Entry, GPA/CGPA, Rank List, Analytics.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func

from extensions import db
from models import Mark, Student, Subject, Department

marks_bp = Blueprint('marks', __name__, url_prefix='/marks')


@marks_bp.route('/')
@login_required
def index():
    departments = Department.query.order_by(Department.name).all()
    subjects = Subject.query.order_by(Subject.name).all()
    return render_template('marks/index.html', departments=departments, subjects=subjects)


@marks_bp.route('/entry', methods=['GET', 'POST'])
@login_required
def entry():
    if not (current_user.is_admin() or current_user.is_teacher()):
        flash('Permission denied.', 'danger')
        return redirect(url_for('marks.index'))

    departments = Department.query.order_by(Department.name).all()
    subjects = Subject.query.order_by(Subject.name).all()

    selected_dept = request.args.get('dept_id', type=int)
    selected_subject = request.args.get('subject_id', type=int)
    exam_type = request.args.get('exam_type', 'midterm')
    semester = request.args.get('semester', 1, type=int)
    academic_year = request.args.get('academic_year', '2024-25')

    students = []
    existing_marks = {}

    if selected_dept and selected_subject:
        students = Student.query.filter_by(
            department_id=selected_dept, is_active=True
        ).order_by(Student.roll_number).all()

        existing = Mark.query.filter_by(
            subject_id=selected_subject,
            exam_type=exam_type,
            semester=semester,
            academic_year=academic_year,
        ).all()
        existing_marks = {m.student_id: m for m in existing}

    if request.method == 'POST':
        subject_id = request.form.get('subject_id', type=int)
        e_type = request.form.get('exam_type', 'midterm')
        sem = request.form.get('semester', 1, type=int)
        acad_year = request.form.get('academic_year', '2024-25')
        max_marks = request.form.get('max_marks', 100.0, type=float)
        student_ids = request.form.getlist('student_ids[]')
        saved = 0

        for sid in student_ids:
            sid = int(sid)
            marks_val = request.form.get(f'marks_{sid}', type=float)
            if marks_val is None:
                continue

            marks_val = min(marks_val, max_marks)

            existing = Mark.query.filter_by(
                student_id=sid, subject_id=subject_id,
                exam_type=e_type, semester=sem, academic_year=acad_year
            ).first()

            if existing:
                existing.marks_obtained = marks_val
                existing.max_marks = max_marks
                existing.entered_by = current_user.id
            else:
                mark = Mark(
                    student_id=sid,
                    subject_id=subject_id,
                    exam_type=e_type,
                    marks_obtained=marks_val,
                    max_marks=max_marks,
                    semester=sem,
                    academic_year=acad_year,
                    entered_by=current_user.id,
                )
                db.session.add(mark)
            saved += 1

        db.session.commit()
        flash(f'Marks saved for {saved} students.', 'success')
        return redirect(url_for('marks.entry',
                                dept_id=request.form.get('dept_id'),
                                subject_id=subject_id,
                                exam_type=e_type,
                                semester=sem,
                                academic_year=acad_year))

    return render_template(
        'marks/entry.html',
        departments=departments,
        subjects=subjects,
        students=students,
        selected_dept=selected_dept,
        selected_subject=selected_subject,
        exam_type=exam_type,
        semester=semester,
        academic_year=academic_year,
        existing_marks=existing_marks,
    )


@marks_bp.route('/rank-list')
@login_required
def rank_list():
    departments = Department.query.order_by(Department.name).all()
    selected_dept = request.args.get('dept_id', type=int)
    semester = request.args.get('semester', type=int)
    academic_year = request.args.get('academic_year', '2024-25')

    rank_data = []
    if selected_dept:
        students = Student.query.filter_by(
            department_id=selected_dept, is_active=True
        ).all()

        for s in students:
            query = s.marks
            if semester:
                query = query.filter_by(semester=semester)
            if academic_year:
                query = query.filter_by(academic_year=academic_year)

            student_marks = query.all()
            if not student_marks:
                continue

            total_obtained = sum(m.marks_obtained for m in student_marks)
            total_max = sum(m.max_marks for m in student_marks)
            pct = round((total_obtained / total_max) * 100, 2) if total_max > 0 else 0
            cgpa = s.calculate_cgpa()

            rank_data.append({
                'student': s,
                'total_obtained': total_obtained,
                'total_max': total_max,
                'percentage': pct,
                'cgpa': cgpa,
                'pass_count': sum(1 for m in student_marks if m.is_pass),
                'fail_count': sum(1 for m in student_marks if not m.is_pass),
                'marks_count': len(student_marks),
            })

        rank_data.sort(key=lambda x: x['percentage'], reverse=True)
        for i, item in enumerate(rank_data, 1):
            item['rank'] = i

    return render_template(
        'marks/rank_list.html',
        departments=departments,
        selected_dept=selected_dept,
        semester=semester,
        academic_year=academic_year,
        rank_data=rank_data,
    )


@marks_bp.route('/analytics')
@login_required
def analytics():
    departments = Department.query.order_by(Department.name).all()
    subjects = Subject.query.order_by(Subject.name).all()
    selected_dept = request.args.get('dept_id', type=int)
    selected_subject = request.args.get('subject_id', type=int)

    grade_distribution = {'O': 0, 'A+': 0, 'A': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'E': 0, 'F': 0}
    pass_fail = {'pass': 0, 'fail': 0}
    avg_marks = 0
    total_marks_records = 0

    query = Mark.query
    if selected_subject:
        query = query.filter_by(subject_id=selected_subject)
    elif selected_dept:
        subj_ids = [s.id for s in Subject.query.filter_by(department_id=selected_dept).all()]
        if subj_ids:
            query = query.filter(Mark.subject_id.in_(subj_ids))

    all_marks = query.all()
    total_marks_records = len(all_marks)

    if all_marks:
        for m in all_marks:
            g = m.grade
            if g in grade_distribution:
                grade_distribution[g] += 1
            if m.is_pass:
                pass_fail['pass'] += 1
            else:
                pass_fail['fail'] += 1
        avg_marks = round(sum(m.percentage for m in all_marks) / total_marks_records, 2)

    # Subject-wise averages
    subject_avgs = []
    for subj in subjects:
        subj_marks = Mark.query.filter_by(subject_id=subj.id).all()
        if subj_marks:
            avg = round(sum(m.percentage for m in subj_marks) / len(subj_marks), 1)
            subject_avgs.append({'subject': subj.name, 'avg': avg, 'count': len(subj_marks)})

    subject_avgs.sort(key=lambda x: x['avg'], reverse=True)

    return render_template(
        'marks/analytics.html',
        departments=departments,
        subjects=subjects,
        selected_dept=selected_dept,
        selected_subject=selected_subject,
        grade_distribution=grade_distribution,
        pass_fail=pass_fail,
        avg_marks=avg_marks,
        total_marks_records=total_marks_records,
        subject_avgs=subject_avgs,
    )


@marks_bp.route('/student/<int:student_id>')
@login_required
def student_marks(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('students.list_students'))

    marks = Mark.query.filter_by(student_id=student_id).order_by(
        Mark.semester, Mark.subject_id, Mark.exam_type
    ).all()

    from services.ml_service import predict_performance
    prediction = predict_performance(student_id)

    return render_template(
        'marks/student_marks.html',
        student=student,
        marks=marks,
        cgpa=student.calculate_cgpa(),
        prediction=prediction,
    )
