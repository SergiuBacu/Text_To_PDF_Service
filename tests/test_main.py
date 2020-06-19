from unittest import TestCase, main as ut_main
from werkzeug.security import generate_password_hash
from flask import  current_app
from ..main import allowed_file, cleanup_tmp
from .. import create_app, database as db
from ..models import File, User
import os

# Run this above the project directory as:  python -m project.tests.test_main -b
# Remember to have Zookeeper and Kafka running

TEST_DB = 'test.db'
TEST_USER = 'testuser'

class Test(TestCase):

    # run before all tests in one run
    @classmethod
    def setUpClass(cls) -> None:
        pass

    # run after all tests in one run
    @classmethod
    def tearDownClass(cls) -> None:
        pass

    # run before each test
    def setUp(self) -> None:
        self.flask_app = create_app()
        self.flask_app.config['TESTING'] = True
        self.flask_app.config['WTF_CSRF_ENABLED'] = False
        self.flask_app.config['LOGIN_DISABLED'] = False
        self.flask_app.config['DEBUG'] = False
        self.flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
                                                           os.path.join(self.flask_app.config['BASEDIR'], TEST_DB)
        self.app = self.flask_app.test_client()
        with self.flask_app.app_context():
            db.drop_all()
            db.create_all()
            # create test user
            new_user = User(email=TEST_USER, name=TEST_USER, password=generate_password_hash("test", method='sha256'))
            db.session.add(new_user)
            db.session.commit()

    # run after each test
    def tearDown(self) -> None:
        # delete test user
        with self.flask_app.app_context():
            db.session.query(User).filter(User.email == TEST_USER).delete()
            db.session.commit()

    def test_allowed_file_valid(self):
        """
        Test validation of good text filename
        :return: None
        """
        with self.flask_app.app_context():
            response = allowed_file("file123.txt")
            self.assertEqual(response, True)

    def test_allowed_file_invalid(self):
        """
        Test validation of bad pdf filename
        :return: None
        """
        with self.flask_app.app_context():
            response = allowed_file("file123.pdf")
            self.assertEqual(response, False)

    def test_allowed_file_invalid2(self):
        """
        Test validation of bad null filename
        :return: None
        """
        with self.flask_app.app_context():
            response = allowed_file("")
            self.assertEqual(response, False)

    def test_cleanup_tmp(self):
        # 1. create the file
      with self.flask_app.app_context():
          with open(os.path.join(self.flask_app.config['UPLOAD_DIR'], self.flask_app.config['BUCKET_NAME'] + 'test.pdf'),
                    'w') as fp:
              fp.write('test')
          # 2. run the delete function "cleanup_tmp"
          cleanup_tmp()
          # 3. verify if the file still exists, return true if it doesn't
          self.assertEqual(os.path.exists(
              os.path.join(self.flask_app.config['UPLOAD_DIR'], self.flask_app.config['BUCKET_NAME'] + 'test.pdf')), False)

    # ----------------------------

    def test_index(self):
        """
        Test rendering main index page
        :return: None
        """
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_profile(self):
        """
        Test rendering main profile page
        :return: None
        """
        response = self.app.get('/profile', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_upload(self):
        """
        Test rendering main upload page
        :return: None
        """
        response = self.app.get('/service/upload', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_upload_post_valid(self):
        """
        Test if a successfully logged in test user can upload a valid text file
        :return: None
        """
        # create test file
        fname = "unittest_testfile.txt"
        with open('%s' % os.path.join(fname), 'wb') as fout:
            fout.write(os.urandom(5*1024))

        # login user (fake method, when want to make unauthenticated request, overwrite this again and return None)
        with self.flask_app.app_context():
            user = db.session.query(User).filter(User.email == TEST_USER).first()

            @self.flask_app.login_manager.request_loader
            def load_user_from_request(request):
                return user

        # create request for testing, submit the request, and remove the source test file
        fout = open(fname, 'rb')
        response = self.app.post('/service/upload', data={'file': (fout, fname), },
                                 follow_redirects=True)
        fout.close()
        os.remove(fname)

        # check status
        self.assertTrue(os.path.exists(os.path.join(self.flask_app.config['UPLOAD_DIR'], fname)))
        self.assertTrue('/service/pdf' in response.headers['Location'])
        self.assertEqual(response.status_code, 201)

        # cleanup test file
        if os.path.exists(os.path.join(self.flask_app.config['UPLOAD_DIR'], fname)):
            os.remove(os.path.join(self.flask_app.config['UPLOAD_DIR'], fname))

    def test_download(self):
        """
        Test rendering main download page
        :return: None
        """
        response = self.app.get('/service/download', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_down_pdf(self):
        """
        Test if a successfully logged in test user can download a valid text file, after uploading it
        :return: None
        """
        # create test file
        fname = "unittest_testfile.txt"
        with open('%s' % os.path.join(fname), 'wb') as fout:
            fout.write(os.urandom(5 * 1024))

        # login user (fake method, when want to make unauthenticated request, overwrite this again and return None)
        with self.flask_app.app_context():
            user = db.session.query(User).filter(User.email == TEST_USER).first()

            @self.flask_app.login_manager.request_loader
            def load_user_from_request(request):
                return user

        # create request for testing, submit the request, and remove the source test file
        fout = open(fname, 'rb')
        response = self.app.post('/service/upload', data={'file': (fout, fname), },
                                 follow_redirects=True)
        fout.close()
        os.remove(fname)

        # check status of upload
        self.assertTrue(os.path.exists(os.path.join(self.flask_app.config['UPLOAD_DIR'], fname)))
        self.assertTrue('/service/pdf' in response.headers['Location'])
        self.assertEqual(response.status_code, 201)

        # get file ID for the file just uploaded
        with self.flask_app.app_context():
            file_obj = db.session.query(File).filter(File.filename == fname).first()

        # create request for download testing
        response = self.app.get('/service/pdf/' + str(file_obj.id),
                                follow_redirects=True)

        # check status of download
        self.assertEqual(response.status_code, 200)
        # test if file contents are same
        with open(os.path.join(self.flask_app.config['UPLOAD_DIR'], fname), 'rb') as test_file:
            self.assertEqual(response.data, test_file.read())

        # cleanup test file
        response.close()
        if os.path.exists(os.path.join(self.flask_app.config['UPLOAD_DIR'], fname)):
            os.remove(os.path.join(self.flask_app.config['UPLOAD_DIR'], fname))


# runs the unit tests in the module
if __name__ == '__main__':
    ut_main()
