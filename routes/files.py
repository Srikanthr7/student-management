"""
File Management routes — Upload/download student documents.
Uses Cloudinary for persistent cloud storage when configured,
falls back to local disk storage in development.
"""
import os
from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, current_app, send_from_directory)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from extensions import db
from models import Student, UploadedFile
from services import cloudinary_service

files_bp = Blueprint('files', __name__, url_prefix='/files')

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'png', 'jpg', 'jpeg', 'gif', 'webp'}


def _allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@files_bp.route('/student/<int:student_id>')
@login_required
def student_files(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('students.list_students'))
    files = UploadedFile.query.filter_by(student_id=student_id).order_by(
        UploadedFile.uploaded_at.desc()
    ).all()
    return render_template('files/student_files.html', student=student, files=files)


@files_bp.route('/upload/<int:student_id>', methods=['POST'])
@login_required
def upload_file(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('students.list_students'))

    if 'file' not in request.files:
        flash('No file selected.', 'danger')
        return redirect(request.referrer)

    file = request.files['file']
    file_type = request.form.get('file_type', 'document')

    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(request.referrer)

    if not _allowed_file(file.filename):
        flash('File type not allowed.', 'danger')
        return redirect(request.referrer)

    original_name = file.filename
    filename = secure_filename(file.filename)
    unique_name = f"{student.student_id}_{file_type}_{filename}"

    # Determine subfolder (used for both local fallback and Cloudinary folder)
    subfolder_map = {
        'photo': 'photos',
        'document': 'documents',
        'certificate': 'certificates',
        'resume': 'resumes',
    }
    subfolder = subfolder_map.get(file_type, 'documents')

    cloudinary_url = None
    cloudinary_public_id = None
    file_size = None

    if current_app.config.get('CLOUDINARY_CLOUD_NAME'):
        # Upload to Cloudinary
        try:
            resource_type = cloudinary_service.get_resource_type(file_type)
            cloudinary_url, cloudinary_public_id = cloudinary_service.upload_file(
                file,
                folder=f'edutrack/{subfolder}',
                resource_type=resource_type,
            )
            # Estimate file size from content-length header if available
            file_size = request.content_length
        except Exception as e:
            flash(f'File upload to cloud failed: {e}', 'danger')
            return redirect(request.referrer)
    else:
        # Fallback: local disk storage
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder, unique_name)
        file.save(save_path)
        file_size = os.path.getsize(save_path)

    uploaded = UploadedFile(
        student_id=student_id,
        filename=unique_name,
        original_name=original_name,
        file_type=file_type,
        file_size=file_size,
        cloudinary_url=cloudinary_url,
        cloudinary_public_id=cloudinary_public_id,
        uploaded_by=current_user.id,
    )
    db.session.add(uploaded)
    db.session.commit()

    flash(f'File "{original_name}" uploaded successfully.', 'success')
    return redirect(request.referrer or url_for('students.student_detail', student_id=student_id))


@files_bp.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    from flask import redirect as flask_redirect
    f = db.session.get(UploadedFile, file_id)
    if not f:
        flash('File not found.', 'danger')
        return redirect(url_for('students.list_students'))

    # If stored on Cloudinary, redirect to the CDN URL
    if f.cloudinary_url:
        return flask_redirect(f.cloudinary_url)

    # Fallback: serve from local disk
    subfolder_map = {
        'photo': 'photos',
        'document': 'documents',
        'certificate': 'certificates',
        'resume': 'resumes',
    }
    subfolder = subfolder_map.get(f.file_type, 'documents')
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    return send_from_directory(upload_folder, f.filename, as_attachment=True,
                               download_name=f.original_name)


@files_bp.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    if not current_user.is_admin():
        flash('Admin access required.', 'danger')
        return redirect(request.referrer)

    f = db.session.get(UploadedFile, file_id)
    if not f:
        flash('File not found.', 'danger')
        return redirect(request.referrer)

    # Delete from Cloudinary if stored there
    if f.cloudinary_public_id:
        resource_type = cloudinary_service.get_resource_type(f.file_type)
        cloudinary_service.delete_file(f.cloudinary_public_id, resource_type=resource_type)
    else:
        # Delete from local disk (legacy)
        subfolder_map = {
            'photo': 'photos',
            'document': 'documents',
            'certificate': 'certificates',
            'resume': 'resumes',
        }
        subfolder = subfolder_map.get(f.file_type, 'documents')
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder, f.filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.session.delete(f)
    db.session.commit()
    flash('File deleted.', 'success')
    return redirect(request.referrer)
