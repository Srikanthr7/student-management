"""
Student Service — ID generation and sample data seeding.
"""
import random
from datetime import date, timedelta, datetime
from extensions import db
from models import Student, Department, Subject, User, Attendance, Mark, Notification


def generate_student_id() -> str:
    """Generate unique student ID like ETP2024001."""
    year = date.today().year
    last = Student.query.filter(
        Student.student_id.like(f'ETP{year}%')
    ).order_by(Student.student_id.desc()).first()
    if last:
        num = int(last.student_id[-4:]) + 1
    else:
        num = 1
    return f'ETP{year}{num:04d}'


def get_paginated_students(page: int, per_page: int, **filters):
    query = Student.query.filter_by(is_active=True)
    for k, v in filters.items():
        if v:
            query = query.filter_by(**{k: v})
    return query.order_by(Student.full_name).paginate(page=page, per_page=per_page)


def search_students(search_term: str):
    from sqlalchemy import or_
    return Student.query.filter(
        Student.is_active == True,
        or_(
            Student.full_name.ilike(f'%{search_term}%'),
            Student.roll_number.ilike(f'%{search_term}%'),
            Student.student_id.ilike(f'%{search_term}%'),
            Student.email.ilike(f'%{search_term}%'),
        )
    ).order_by(Student.full_name).all()


def seed_sample_data():
    """Seed the database with realistic sample data."""
    # Departments
    dept_data = [
        {'name': 'Computer Science & Engineering', 'code': 'CSE', 'head_of_dept': 'Dr. Rajesh Kumar'},
        {'name': 'Electronics & Communication', 'code': 'ECE', 'head_of_dept': 'Dr. Priya Sharma'},
        {'name': 'Mechanical Engineering', 'code': 'ME', 'head_of_dept': 'Dr. Amit Singh'},
        {'name': 'Civil Engineering', 'code': 'CE', 'head_of_dept': 'Dr. Sunita Patel'},
        {'name': 'Information Technology', 'code': 'IT', 'head_of_dept': 'Dr. Vikram Nair'},
    ]
    depts = {}
    for d in dept_data:
        dept = Department.query.filter_by(code=d['code']).first()
        if not dept:
            dept = Department(**d)
            db.session.add(dept)
            db.session.flush()
        depts[d['code']] = dept

    # Teacher users
    teachers = []
    teacher_data = [
        ('prof_rahul', 'rahul@edutrack.com', 'Teacher@123'),
        ('prof_meera', 'meera@edutrack.com', 'Teacher@123'),
        ('prof_suresh', 'suresh@edutrack.com', 'Teacher@123'),
    ]
    for uname, email, pwd in teacher_data:
        t = User.query.filter_by(username=uname).first()
        if not t:
            t = User(username=uname, email=email, role='teacher')
            t.set_password(pwd)
            db.session.add(t)
            db.session.flush()
        teachers.append(t)

    # Subjects
    subject_data = [
        ('Data Structures', 'DS101', 'CSE', 4, 1, 0),
        ('Algorithms', 'AL201', 'CSE', 4, 2, 0),
        ('Database Systems', 'DB301', 'CSE', 3, 3, 1),
        ('Operating Systems', 'OS401', 'CSE', 3, 4, 0),
        ('Machine Learning', 'ML501', 'CSE', 4, 5, 1),
        ('Circuit Theory', 'CT101', 'ECE', 4, 1, 2),
        ('Digital Electronics', 'DE201', 'ECE', 4, 2, 2),
        ('Thermodynamics', 'TD101', 'ME', 4, 1, 0),
        ('Fluid Mechanics', 'FM201', 'ME', 3, 2, 0),
        ('Structural Analysis', 'SA101', 'CE', 4, 1, 1),
        ('Web Technologies', 'WT101', 'IT', 3, 1, 1),
        ('Network Security', 'NS301', 'IT', 3, 3, 2),
    ]
    subjects = {}
    for name, code, dept_code, credits, sem, t_idx in subject_data:
        subj = Subject.query.filter_by(code=code).first()
        if not subj:
            subj = Subject(
                name=name, code=code,
                department_id=depts[dept_code].id,
                credits=credits, semester=sem,
                teacher_id=teachers[t_idx % len(teachers)].id
            )
            db.session.add(subj)
            db.session.flush()
        subjects[code] = subj

    db.session.commit()

    # Students
    first_names = ['Arjun', 'Priya', 'Rahul', 'Sneha', 'Vikram', 'Ananya', 'Kiran',
                   'Divya', 'Suresh', 'Meera', 'Amit', 'Pooja', 'Ravi', 'Kavitha',
                   'Deepak', 'Swati', 'Manoj', 'Lakshmi', 'Nikhil', 'Reshma',
                   'Sanjay', 'Nandita', 'Arun', 'Bhavna', 'Harish']
    last_names = ['Sharma', 'Patel', 'Kumar', 'Singh', 'Nair', 'Rao', 'Verma',
                  'Gupta', 'Reddy', 'Iyer', 'Joshi', 'Mehta', 'Shah', 'Pillai',
                  'Banerjee', 'Mishra', 'Tiwari', 'Pandey', 'Das', 'Bhat']

    dept_codes = ['CSE', 'ECE', 'ME', 'CE', 'IT']
    student_count = 0
    existing_rolls = set(s.roll_number for s in Student.query.all())
    existing_emails = set(s.email for s in Student.query.all())

    for i in range(40):
        dept_code = dept_codes[i % len(dept_codes)]
        dept = depts[dept_code]
        year = random.randint(1, 4)
        semester = year * 2 - random.randint(0, 1)
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        full_name = f'{fn} {ln}'
        roll_number = f'{dept_code}{2021 + year % 4}{i+1:03d}'
        email = f'{fn.lower()}.{ln.lower()}{i}@student.edu'

        if roll_number in existing_rolls or email in existing_emails:
            continue

        existing_rolls.add(roll_number)
        existing_emails.add(email)

        dob = date(2000 + random.randint(1, 5), random.randint(1, 12), random.randint(1, 28))

        s = Student(
            student_id=generate_student_id(),
            full_name=full_name,
            roll_number=roll_number,
            department_id=dept.id,
            year=year,
            semester=semester,
            email=email,
            phone=f'98{random.randint(10000000, 99999999)}',
            address=f'{random.randint(1, 200)}, Sample Street, City',
            date_of_birth=dob,
        )
        db.session.add(s)
        db.session.flush()
        student_count += 1

        # Add marks for department subjects
        dept_subjects = Subject.query.filter_by(department_id=dept.id).all()
        for subj in dept_subjects[:3]:
            for exam_type in ['midterm', 'final']:
                max_m = 100.0
                obtained = round(random.uniform(35, 98), 1)
                mark = Mark(
                    student_id=s.id,
                    subject_id=subj.id,
                    exam_type=exam_type,
                    marks_obtained=obtained,
                    max_marks=max_m,
                    semester=subj.semester,
                    academic_year='2024-25',
                    entered_by=teachers[0].id,
                )
                db.session.add(mark)

        # Add attendance records for past 30 days
        for subj in dept_subjects[:2]:
            for day_offset in range(30):
                att_date = date.today() - timedelta(days=day_offset)
                if att_date.weekday() < 5:  # weekdays only
                    status = random.choices(
                        ['present', 'absent', 'late'],
                        weights=[75, 20, 5]
                    )[0]
                    att = Attendance(
                        student_id=s.id,
                        subject_id=subj.id,
                        date=att_date,
                        status=status,
                        marked_by=teachers[0].id,
                    )
                    db.session.add(att)

    db.session.commit()
    print(f'[SUCCESS] Seeded {student_count} students with marks and attendance data.')
