from . import database
from .models import File
import os
from werkzeug.utils import secure_filename
from flask import current_app

class Upload():
    def __init__(self, file, user_id):
        self.file = file
        self.filename = secure_filename(self.file.filename)
        self.user_id = user_id
        # set initial status as not uploaded
        self.status = 'not_uploaded'
        # local path where files are uploaded
        self.upload_der = current_app.config['UPLOAD_DIR']

    def upload_file_local(self):
        """
        write file to local directory and update database
        :return: None
        """
        # write file localy using flask request.files functionality
        self.file.save(os.path.join(self.upload_der, self.filename))
        self.status = 'local'

        # create new file entry
        new_file = File(user_id = self.user_id, filename = self.filename, status = self.status)

        # add the new file to the database
        database.session.add(new_file)
        database.session.commit()

    def set_local_path(self, new_path):
        """
        set directory for local file storage (default is uploads directory under flask app)
        :param new_path:
        :return: True if successfully set
        """
        ret = False
        if not os.path.exists(new_path):
            return ret

        self.upload_der = new_path
        ret = True
        return ret

    def queue_file_cloud(self):
        """
        queue file to kafka to have it uploaded to the cloud
        :return: None
        """
        # TODO: add functionality to queue file for cloud upload
        pass

    def convert_to_pdf(self):
        """
        convert text file to PDF
        :return: None
        """
        #TODO: add in ability to convert text files to PDF, and update database with PDF file name (or update existing file name), status becomes local_converted
        pass

