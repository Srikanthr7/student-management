"""
Notifications routes.
"""
from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from flask_login import login_required, current_user

from extensions import db
from models import Notification

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@notifications_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('notifications/index.html', notifications=notifications)


@notifications_bp.route('/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_read(notif_id):
    notif = db.session.get(Notification, notif_id)
    if notif and notif.user_id == current_user.id:
        notif.is_read = True
        db.session.commit()
    return redirect(request.referrer or url_for('notifications.index'))


@notifications_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return redirect(url_for('notifications.index'))


@notifications_bp.route('/api/unread-count')
@login_required
def unread_count():
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})


@notifications_bp.route('/api/recent')
@login_required
def recent():
    notifs = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).limit(5).all()
    return jsonify([n.to_dict() for n in notifs])
