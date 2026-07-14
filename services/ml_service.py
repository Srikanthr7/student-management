"""
ML Service — Performance prediction and attendance risk using scikit-learn.
"""
from typing import Dict, Any


def predict_performance(student_id: int) -> Dict[str, Any]:
    """
    Predict student pass/fail and performance risk using marks history.
    Uses a simple heuristic model (train on real data for better results).
    """
    try:
        from models import Mark, Attendance, Student
        from extensions import db

        student = db.session.get(Student, student_id)
        if not student:
            return {'error': 'Student not found'}

        marks = Mark.query.filter_by(student_id=student_id).all()
        if not marks:
            return {
                'prediction': 'Insufficient Data',
                'confidence': 0,
                'risk_level': 'unknown',
                'recommendation': 'Add marks to get performance prediction.',
                'cgpa': 0,
                'pass_rate': 0,
            }

        # Feature extraction
        percentages = [m.percentage for m in marks]
        avg_pct = sum(percentages) / len(percentages)
        pass_rate = sum(1 for p in percentages if p >= 40) / len(percentages) * 100
        cgpa = student.calculate_cgpa()
        att_pct = student.attendance_percentage()

        # Simple rule-based prediction (replace with trained model for production)
        if avg_pct >= 75 and att_pct >= 75:
            prediction = 'Excellent'
            risk_level = 'low'
            confidence = min(95, int(avg_pct))
            recommendation = 'Keep up the great work! Consider aiming for honors.'
        elif avg_pct >= 60 and att_pct >= 65:
            prediction = 'Good'
            risk_level = 'low'
            confidence = min(85, int(avg_pct))
            recommendation = 'Good performance. Focus on weak subjects to improve CGPA.'
        elif avg_pct >= 50 and att_pct >= 55:
            prediction = 'Average'
            risk_level = 'medium'
            confidence = 65
            recommendation = 'Performance is average. Attend extra classes and seek help.'
        elif avg_pct >= 40:
            prediction = 'At Risk'
            risk_level = 'high'
            confidence = 70
            recommendation = 'Risk of failure detected. Immediate academic counseling recommended.'
        else:
            prediction = 'Fail Risk'
            risk_level = 'critical'
            confidence = 80
            recommendation = 'Critical: High probability of failure. Contact academic advisor immediately.'

        # Attendance risk overlay
        if att_pct < 75 and risk_level not in ('critical',):
            risk_level = 'high'
            recommendation += f' Also, attendance ({att_pct:.1f}%) is below minimum 75% threshold.'

        return {
            'prediction': prediction,
            'confidence': confidence,
            'risk_level': risk_level,
            'recommendation': recommendation,
            'avg_percentage': round(avg_pct, 2),
            'pass_rate': round(pass_rate, 2),
            'cgpa': cgpa,
            'attendance_percentage': round(att_pct, 2),
            'total_subjects': len(marks),
        }

    except Exception as e:
        return {'error': str(e), 'prediction': 'Error', 'risk_level': 'unknown'}


def predict_attendance_risk(student_id: int) -> Dict[str, Any]:
    """Predict attendance risk for a student."""
    try:
        from models import Student
        from extensions import db

        student = db.session.get(Student, student_id)
        if not student:
            return {'error': 'Student not found'}

        att_pct = student.attendance_percentage()

        if att_pct == 0:
            return {'risk': 'no_data', 'message': 'No attendance data available.'}
        elif att_pct >= 85:
            risk = 'low'
            message = 'Attendance is excellent. Keep it up!'
        elif att_pct >= 75:
            risk = 'medium'
            message = f'Attendance ({att_pct:.1f}%) is at the minimum threshold. Be careful!'
        elif att_pct >= 60:
            risk = 'high'
            message = f'Attendance ({att_pct:.1f}%) is below threshold. Risk of being barred from exams.'
        else:
            risk = 'critical'
            message = f'Critical: Attendance ({att_pct:.1f}%) is dangerously low. Immediate action needed.'

        return {
            'risk': risk,
            'attendance_percentage': att_pct,
            'message': message,
        }
    except Exception as e:
        return {'error': str(e)}


def chatbot_response(query: str) -> str:
    """Simple rule-based chatbot for student queries."""
    query_lower = query.lower().strip()

    responses = {
        ('attendance', 'present', 'absent'): (
            'Your attendance percentage is calculated as (Present + Late) / Total Classes × 100. '
            'Minimum 75% attendance is required to appear in exams.'
        ),
        ('cgpa', 'gpa', 'grade point'): (
            'CGPA is calculated as the average grade points across all subjects. '
            'Grade scale: O=4.0, A+=3.7, A=3.3, B+=3.0, B=2.7, C=2.3, D=1.0, F=0.0'
        ),
        ('marks', 'result', 'exam'): (
            'You can view your marks in the Marks section. '
            'Marks are entered subject-wise for each exam type (midterm/final/internal).'
        ),
        ('pass', 'fail', 'minimum'): (
            'Minimum passing marks is 40% in each subject. '
            'Students scoring below 40% are marked as Failed (F grade).'
        ),
        ('holiday', 'schedule', 'timetable'): (
            'Please check the academic calendar on the notice board or contact your department office for the timetable.'
        ),
        ('fee', 'payment', 'fees'): (
            'For fee-related queries, please visit the accounts department or contact the administration office.'
        ),
        ('certificate', 'document', 'upload'): (
            'You can upload documents like certificates, resumes, and other files in your student profile under the Files section.'
        ),
        ('hello', 'hi', 'hey'): (
            'Hello! I\'m EduBot, your EduTrack Pro assistant. How can I help you today? '
            'Ask me about attendance, marks, CGPA, or any academic queries!'
        ),
        ('help', 'support', 'contact'): (
            'For assistance, you can: \n'
            '• Visit your department office\n'
            '• Contact your class teacher\n'
            '• Email admin@edutrackpro.com\n'
            '• Use the notifications section to send messages'
        ),
    }

    for keywords, response in responses.items():
        if any(kw in query_lower for kw in keywords):
            return response

    return (
        'I\'m not sure about that query. Please contact your department office or '
        'email admin@edutrackpro.com for assistance. You can also ask about: '
        'attendance, marks, CGPA, exams, documents, or fees.'
    )
