from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# init SQLAlchemy so we can use it later in our models
database = SQLAlchemy()

def create_app():
    application = Flask(__name__)

    application.config['SECRET_KEY'] = '9OLWxND4o83j4K4iuopO'
    application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
    application.config['UPLOAD_DIR'] = os.path.join(os.getcwd(),os.environ['FLASK_APP'],'uploads')
    # if local path for uploads doesn't exist, create it
    if not os.path.exists(application.config['UPLOAD_DIR']):
        os.mkdir(application.config['UPLOAD_DIR'])


    database.init_app(application)

    loginmanager = LoginManager()
    loginmanager.login_view = 'auth.login'
    loginmanager.init_app(application)

    from .models import User

    @loginmanager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))

    # blueprint for auth routes in our app
    from .auth import auth as auth_blueprint
    application.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app
    from .main import main as main_blueprint
    application.register_blueprint(main_blueprint)

    return application

