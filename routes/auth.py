"""
Authentication routes — Login, Logout, Profile.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from datetime import datetime

from extensions import db, limiter
from models import User, Notification

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        if user and user.is_active and user.check_password(password):
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()

            # Create welcome-back notification
            notif = Notification(
                user_id=user.id,
                title='Login Successful',
                message=f'Welcome back, {user.username}! You logged in at {datetime.utcnow().strftime("%H:%M")}.',
                type='success'
            )
            db.session.add(notif)
            db.session.commit()

            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Update email
        if email and email != current_user.email:
            if User.query.filter_by(email=email).first():
                flash('Email already in use.', 'danger')
                return render_template('auth/profile.html')
            current_user.email = email
            flash('Email updated.', 'success')

        # Update password
        if current_password:
            if not current_user.check_password(current_password):
                flash('Current password is incorrect.', 'danger')
                return render_template('auth/profile.html')
            if new_password != confirm_password:
                flash('New passwords do not match.', 'danger')
                return render_template('auth/profile.html')
            if len(new_password) < 8:
                flash('Password must be at least 8 characters.', 'danger')
                return render_template('auth/profile.html')
            current_user.set_password(new_password)
            flash('Password updated successfully.', 'success')

        db.session.commit()
        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html')


@auth_bp.route('/users')
@login_required
def users_list():
    if not current_user.is_admin():
        flash('Admin access required.', 'danger')
        return redirect(url_for('dashboard.index'))
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('auth/users.html', users=users)


@auth_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    if not current_user.is_admin():
        flash('Admin access required.', 'danger')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'student')

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
        else:
            user = User(username=username, email=email, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash(f'User "{username}" created successfully.', 'success')
            return redirect(url_for('auth.users_list'))

    return render_template('auth/add_user.html')


@auth_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
def toggle_user(user_id):
    if not current_user.is_admin():
        flash('Admin access required.', 'danger')
        return redirect(url_for('dashboard.index'))
    user = db.session.get(User, user_id)
    if user and user.id != current_user.id:
        user.is_active = not user.is_active
        db.session.commit()
        status = 'activated' if user.is_active else 'deactivated'
        flash(f'User "{user.username}" {status}.', 'success')
    return redirect(url_for('auth.users_list'))
