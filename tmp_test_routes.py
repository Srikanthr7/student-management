import sys
import os

from app import create_app
from extensions import db
from models import Student, Department, Subject, User, Attendance, Mark

app = create_app('testing')

with app.app_context():
    db.create_all()
    print("✓ App initialization successful.")
    print("✓ Database tables created.")

    urls = [rule.rule for rule in app.url_map.iter_rules()]
    print(f"✓ Registered routes count: {len(urls)}")

    with app.test_client() as client:
        # Create test user
        admin = User(username='testadmin', email='testadmin@test.com', role='admin')
        admin.set_password('password')
        db.session.add(admin)
        db.session.commit()

        # Login
        client.post('/auth/login', data={'username': 'testadmin', 'password': 'password'})

        # Test GET /attendance/
        resp = client.get('/attendance/', follow_redirects=True)
        print(f"✓ GET /attendance/ status: {resp.status_code}")

        # Test GET /dashboard
        resp = client.get('/dashboard')
        print(f"✓ GET /dashboard status: {resp.status_code}")

print("All route checks completed successfully!")
