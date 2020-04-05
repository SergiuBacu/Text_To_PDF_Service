from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, send_from_directory, \
    Response, make_response
from flask_login import login_required, current_user
from .upload import Upload
from .models import File
from . import database
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
    """Render index.html
    ---
    responses:
      200:
        description: Render index template
    """
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    """Render profile.html
    ---
    parameters:
      - name: user_name
        in: header
        type: string
        required: false
    security:
      type: http
      scheme: basic
    responses:
      200:
        description: Render profile template with current user's name
    """
    return render_template('profile.html',name=current_user.name)

@main.route('/service/upload')
def upload():
    """Render upload.html
    ---
    security:
      type: http
      scheme: basic
    responses:
      200:
        description: Render upload template for current user
    """
    return render_template('upload.html')

@main.route('/service/upload', methods=['POST'])
def upload_post():
    """Upload a file for a user
    ---
    consumes:
    - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
    security:
      type: http
      scheme: basic
    definitions:
      File:
        type: object
        properties:
          id:
            description: ID for File instance
            type: integer
            example: 2
          user_id:
            description: ID for user uploading file
            type: integer
            example: 1
          filename:
            description: name of file being uploaded, a .txt file
            type: string
            maxLength: 1000
            example: user1_file2.txt
          status:
            description: upload status for the file, either "local" (local and still txt file, "local_converted"
                         (converted to PDF but still local), or "cloud_google" (uploaded to Google Cloud Storage)
            enum: [local, local_converted, cloud_google]
            type: string
            maxLength: 100
            example: cloud_google
          cloud_url:
            description: URL for file in cloud
            type: string
            maxLength: 1000
            example: user/1/pdf/user1_file2.pdf
    responses:
      201:
        description: Render upload template after successful upload by current user
        schema:
          $ref: '#/definitions/File'
        headers:
          Location:
            description: API URL for the file, with file ID
            schema:
              type: string
              example: /service/pdf/1
      302:
        description: Redirect to /service/upload in case of error
      400:
        description: If file is not found (deleted before upload), return bad request
    """
    file = request.files['file']

    # check if the file already exists in the database
    file_exists = File.query.filter_by(user_id = current_user.id, filename = file.filename.replace(' ','_')).first()
    if file_exists:
        flash('The file already exists, please try again.') # show error message if path already exists in DB
        return redirect(url_for('main.upload'))  # redirect to main upload

    # test if the filename is too long
    if len(file.filename) > 1000:
        flash('File name too long, please try again.') # show error message if path is too long
        return redirect(url_for('main.upload'))  # reload page

    # restrict upload types to only txt files
    if not allowed_file(file.filename):
        flash('Only .txt files are allowed for upload, please try again')
        return redirect(url_for('main.upload')) # reload the page

    # create instance of Upload to upload file
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
    """Render download.html
        ---
        security:
          type: http
          scheme: basic
        definitions:
          FileList:
            type: array
            items:
              $ref: "#/definitions/File"
        responses:
          200:
            description: Render download template with list of files to download for current user
            schema:
              $ref: "#/definitions/FileList"

    """
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
    """Download a file
        ---
        parameters:
          - name: file_id
            in: path
            type: integer
            required: true
        security:
          type: http
          scheme: basic
        responses:
          200:
            description: Return requested file for current user
            content:
              application/pdf:
                schema:
                  type: string
                  format: binary
              text/plain:
                schema:
                  type: string
          302:
            description: Redirect to /service/download in case of error when getting file from cloud
          404:
            description: File is not found locally, was not uploaded to cloud yet
    """
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
            flash("Error in downloading file from cloud: {}".format(str(ex)))
            return redirect(url_for('main.download')) # reload the page
    else:
        filename = file.filename

    return send_from_directory(current_app.config['UPLOAD_DIR'], filename, as_attachment = True)
