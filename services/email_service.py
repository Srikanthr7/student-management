"""
Email Service — Send emails via Flask-Mail (stub-safe: logs if SMTP not configured).
"""
import logging
from flask import current_app, render_template_string

logger = logging.getLogger(__name__)

EMAIL_TEMPLATES = {
    'welcome': {
        'subject': 'Welcome to EduTrack Pro!',
        'body': '''
        <h2>Welcome, {{ name }}!</h2>
        <p>Your account has been created on <strong>EduTrack Pro</strong>.</p>
        <p>Student ID: <strong>{{ student_id }}</strong></p>
        <p>Login at: <a href="{{ login_url }}">EduTrack Pro</a></p>
        '''
    },
    'low_attendance': {
        'subject': 'Low Attendance Warning — EduTrack Pro',
        'body': '''
        <h2>Attendance Warning</h2>
        <p>Dear {{ name }},</p>
        <p>Your attendance in <strong>{{ subject }}</strong> has fallen to
        <strong>{{ percentage }}%</strong>, below the required 75%.</p>
        <p>Please attend classes regularly to avoid exam detention.</p>
        '''
    },
    'result_published': {
        'subject': 'Results Published — EduTrack Pro',
        'body': '''
        <h2>Results Published</h2>
        <p>Dear {{ name }},</p>
        <p>Your results for <strong>{{ exam_type }}</strong> in
        <strong>{{ subject }}</strong> have been published.</p>
        <p>Login to EduTrack Pro to view your marks.</p>
        '''
    }
}


def send_email(to: str, template_name: str, **kwargs) -> bool:
    """
    Send an email using a named template.
    Falls back to logging if SMTP is not configured.
    """
    try:
        from flask_mail import Message
        from extensions import mail

        template = EMAIL_TEMPLATES.get(template_name)
        if not template:
            logger.warning(f'Email template "{template_name}" not found.')
            return False

        subject = template['subject']
        html_body = render_template_string(template['body'], **kwargs)

        # Check if SMTP is configured
        if not current_app.config.get('MAIL_USERNAME'):
            logger.info(f'[EMAIL STUB] To: {to} | Subject: {subject}')
            logger.debug(f'[EMAIL STUB] Body: {html_body[:200]}...')
            return True  # Gracefully stubbed

        msg = Message(subject=subject, recipients=[to], html=html_body)
        mail.send(msg)
        logger.info(f'Email sent to {to}: {subject}')
        return True

    except Exception as e:
        logger.error(f'Failed to send email to {to}: {e}')
        return False


def send_bulk_email(recipients: list, template_name: str, **kwargs) -> int:
    """Send email to multiple recipients. Returns count of successful sends."""
    sent = 0
    for recipient in recipients:
        if send_email(recipient, template_name, **kwargs):
            sent += 1
    return sent
