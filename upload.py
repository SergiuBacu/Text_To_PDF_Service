from . import database
from .models import File
import os
from werkzeug.utils import secure_filename
from flask import current_app
from fpdf import FPDF

class Upload():
    def __init__(self, file, user_id):
        self.file = file
        self.filename = secure_filename(self.file.filename)
        self.user_id = user_id
        # set initial status as not uploaded
        self.status = 'not_uploaded'
        # local path where files are uploaded
        self.upload_dir = current_app.config['UPLOAD_DIR']

    def upload_file_local(self):
        """
        write file to local directory and update database
        :return: None
        """
        # write file localy using flask request.files functionality
        self.file.save(os.path.join(self.upload_dir, self.filename))
        self.status = 'local'

        # create new file entry
        new_file = File(user_id = self.user_id, filename = self.filename, status = self.status)

        # add the new file to the database
        database.session.add(new_file)
        database.session.commit()

        self.convert_to_pdf()

    def set_local_path(self, new_path):
        """
        set directory for local file storage (default is uploads directory under flask app)
        :param new_path:
        :return: True if successfully set
        """
        ret = False
        if not os.path.exists(new_path):
            return ret

        self.upload_dir = new_path
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
        pdf = FPDF('P', 'in', 'Letter')

        # set the font size
        font_height = 0.16

        # add a page , set margin and enable autyo page break
        pdf.add_page()
        pdf.set_margins(0.25,0.25)
        pdf.set_auto_page_break(True, margin = 0.25)

        # set the font and where the cursor starts
        pdf.set_font('Arial','', 10)
        pdf.set_xy(0.25, 0.25)

        # open the text filen abd line by line, read from file and write to pdf
        with open(os.path.join(self.upload_dir, self.filename), "r") as txt_file:
            line = 1
            while line:
                line = txt_file.readline()
                pdf.write(font_height, line)

        # write out pdf file, use 'latin-1' encoding to avoid unicode issues
        pdf.output(os.path.join(self.upload_dir, self.filename.replace('txt','pdf'))).encode('latin-1')

        # delete the original file
        if os.path.exists(os.path.join(self.upload_dir, self.filename.replace('txt','pdf'))):
            os.remove(os.path.join(self.upload_dir, self.filename))

        # upload DB with new status
        self.status = "local_converted"
        database.session.query(File).filter(File.user_id == self.user_id).\
            filter(File.filename == self.filename).update({"status": self.status})
        database.session.commit()


