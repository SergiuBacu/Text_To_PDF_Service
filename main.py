from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from .upload import Upload
from .models import File

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html',name=current_user.name)



@main.route('/service/upload')
def upload():
    return render_template('upload.html')

@main.route('/service/upload', methods=['POST'])
def upload_post():
    file = request.files['file']

    # check if the file already exists in the database
    file_exists = File.query.filter_by(user_id = current_user.id, filename = file.filename.replace(' ','_')).first()
    if file_exists:
        flash('The file already exists, please try again.')
        return redirect(url_for('main.upload'))  # redirect to main upload

    # test if the filename is too long
    if len(file.filename) > 1000:
        flash('File name too long, please try again.')
        return redirect(url_for('main.upload'))  # reload page

    # TODO: restrict upload to only text files, see flask upload doc for how to restrict by extension

    do_upload = Upload(file, current_user.id)
    do_upload.upload_file_local()
    flash('Uploaded file successfully')
    return redirect(url_for('main.profile'))