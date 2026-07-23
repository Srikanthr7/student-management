# EduTrack Pro — Student Management System

EduTrack Pro is a modern, premium, full-stack Student Management System (SMS) built with Python, Flask, SQLAlchemy, SQLite (PostgreSQL-ready), Bootstrap 5, HTML, CSS, and modern interactive JavaScript.

---

## Key Features

1. **Authentication & Authorization**
   * Role-based access control (RBAC): Admin, Teacher, and Student roles.
   * Secure session management with Flask-Login.
   * Password hashing using Werkzeug.
   * Rate limiting on login attempts for security.

2. **Student Management (CRUD)**
   * Complete student records (Unique Student ID, roll number, department, semester, GPA, DOB, etc.).
   * Profile photo uploads with secure filesystem mapping.
   * Global search and paginated lists.

3. **Academics & Attendance**
   * Bulk attendance marking with status records (Present/Absent/Late).
   * Attendance rate tracker with alerts if attendance drops below the 75% threshold.

4. **Marks & GPA/CGPA Calculations**
   * Grade calculation and automatic CGPA calculation (using a standard 4.0 scale).
   * Dynamically generated leaderboard/rank lists.

5. **AI Assistant & Predictive Analytics**
   * **EduBot AI Chatbot**: Interactive rule-based assistant answering queries on grades, attendance rules, and fees.
   * **ML Service**: Smart pass/fail heuristics and attendance warning indicators based on student performance.

6. **Interactive Dashboard**
   * KPI stat cards with micro-animations.
   * Beautiful dynamic charts powered by Chart.js (grade distribution, department spread, registration trends, and attendance rates).

7. **Document Management**
   * Secure upload/download of certificates, resumes, and academic files.

8. **Developer API**
   * Protected endpoints using JSON Web Tokens (JWT).
   * Interactive Swagger-style documentation at `/api/v1/docs`.

---

## Technology Stack

* **Backend**: Python 3.11+, Flask, SQLAlchemy ORM, Flask-WTF, Flask-Migrate
* **Frontend**: HTML5, Vanilla CSS3 (Custom design system), Bootstrap 5.3, JavaScript (ES6+), Chart.js
* **Database**: SQLite (Development), PostgreSQL (Production-ready)
* **DevOps**: Gunicorn, Render Configuration

---

## Quick Start Guide

### Prerequisites
Make sure you have Python 3.11+ installed.

### 1. Set Up Virtual Environment
```bash
# Clone the repository and enter the directory
cd "student management"

# Create a virtual environment
python -m venv .venv

# Activate it (Windows PowerShell)
.\.venv\Scripts\Activate.ps1
# Or Command Prompt:
.\.venv\Scripts\activate.bat
# Or macOS/Linux:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup Configuration
Copy `.env.example` to `.env` and adjust keys:
```bash
cp .env.example .env
```
Inside `.env`, verify your defaults:
```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=some-secret-key-12345
WTF_CSRF_SECRET_KEY=some-csrf-secret-12345
JWT_SECRET_KEY=some-jwt-secret-12345
```

### 4. Initialize & Seed Database
Use Flask CLI commands to set up:
```bash
# Create database tables
flask init-db

# Seed sample data (creates default admin, teachers, subjects, marks, and student histories)
flask seed-data
```

### 5. Run the Application
Start the Flask dev server:
```bash
flask run --reload
```
Open your browser and navigate to `http://127.0.0.1:5000`.

---

## Default Accounts (Credentials)

| Role | Username | Password | Email |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `Admin@123` | `admin@edutrackpro.com` |
| **Teacher** | `prof_rahul` | `Teacher@123` | `rahul@edutrack.com` |
| **Student** | Check the database or add a new student via the UI |

---

## REST API Overview

* **Documentation Page**: Access `/api/v1/docs` in your browser.
* **Authentication**: POST `{ "username": "admin", "password": "Admin@123" }` to `/api/v1/auth/token` to retrieve a JWT token. Send the token in the `Authorization: Bearer <token>` header for other endpoints.
* **Key Endpoints**:
  * GET `/api/v1/students` — Fetch paginated student list
  * POST `/api/v1/students` — Create new student
  * GET `/api/v1/attendance` — View attendance logs
  * GET `/api/v1/marks` — Retrieve grade transcripts

---

## Production Deployment

### Deploying to Render
1. Connect this repository to your Render account.
2. Render will automatically parse the `render.yaml` file, provisioning a PostgreSQL database and setting up a Python web service configured with Gunicorn.
