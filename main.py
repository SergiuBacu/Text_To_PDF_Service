from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, send_from_directory, \
    Response, make_response
from flask_login import login_required, current_user
from .upload import Upload
from .models import File
import google.cloud.storage as gcs
import glob
import os

main = Blueprint('main', __name__)

def allowed_file(filename):
    """
    check is filename is allowed. Based on https://flask.palletsprojects.com/en/1.1.x/patterns/fileuploads/
    :param filename: filname to check if it's valid
    :return: Boolean, (id the file is valid or not)
    """
    is_allowed = False
    # if the period is in the filename and the extension is allowed, then return True
    if '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']:
        is_allowed = True

    return is_allowed

def cleanup_tmp():
    """
    clean up temporary files in upload directory (from cloud downloads). Each temp file is a pdf prefixed with the bucket name
    :return: None
    """
    path_pattern = os.path.join(current_app.config['UPLOAD_DIR'], current_app.config['BUCKET_NAME'] + '*.pdf')
    for p in glob.glob(path_pattern):
        os.unlink(p)

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

    if not allowed_file(file.filename):
        flash('Only .txt files are allowed for upload, please try again')
        return redirect(url_for('main.upload')) # reload the page

    do_upload = Upload(file, current_user.id)
    do_upload.upload_file_local()
    flash('Uploaded file successfully')

    # return response with the redirect
    response = make_response(Response(profile(), 201))
    file_uploaded = File.query.filter_by(user_id = current_user.id, filename = file.filename.replace(' ','_')).first()
    response.headers['Location'] = url_for('main.down_pdf', id = file_uploaded.id)

    return response

@main.route('/service/download')
@login_required
def download():
    # get file data for current user
    rows = File.query.filter_by(user_id = current_user.id).all()
    # paths for downloading the file
    down_paths = [url_for('main.down_pdf', id = row.id) for row in rows]
    # add null at the beginning to account for table position
    down_paths.insert(0,'na')
    # header for the table
    header = ['Filename', 'File Status', 'Cloud URL', 'Download Link']

    return render_template('download.html', header = header, rows = rows, down_paths = down_paths)

@main.route('/service/pdf/<id>')
@login_required
def down_pdf(id):
    # get filename for the current user_id and file id
    file = File.query.filter_by(user_id=current_user.id, id = id).first()
    # handle case of filename change depending on the file upload/conversion status
    if file.status == 'local_converted':
        filename = file.filename.replace("txt", "pdf")
    elif file.status == "cloud_google":
        try:
            # cleanup any temp files from previous session of cloud downloads
            cleanup_tmp()
            # create local temp file to return to user, prepended with bucket name
            filename = current_app.config['BUCKET_NAME'] + '_' + file.filename.replace("txt", "pdf")
            bucket = gcs.Client().get_bucket(current_app.config['BUCKET_NAME'])
            blob = bucket.blob(file.cloud_url)
            with open(os.path.join(current_app.config['UPLOAD_DIR'], filename), 'wb') as tmp:
                blob.download_to_file(tmp)
        except Exception as ex:
            flash("error in downloading file from cloud: {}".format(str(ex)))
            return redirect(url_for('main.download'))
    else:
        filename = file.filename

    return send_from_directory(current_app.config['UPLOAD_DIR'], filename, as_attachment = True)
