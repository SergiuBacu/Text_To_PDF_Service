from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from .models import User
from . import database

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    """Render login.html
            ---
            responses:
              200:
                description: Render login template
    """
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    """Login a user
    ---
    consumes:
    - multipart/form-data
    parameters:
      - name: email address (username)
        in: formData
        type: string
        required: true
      - name: password
        in: formatData
        type: string
        required: true
    definitions:
      User:
        type: object
        properties:
          id:
            description: ID for user
            type: integer
            example: 1
          email:
            description: email address for user
            type: string
            maxLength: 100
            example: guesswho@gmail.com
          password:
            description: password for user, hashed
            type: string
            maxLength: 100
            example: sha256$Mhdeph6g$a187c9f939d5f1b19a5507f939f0ff2687a8f9b89356f640d810c582ea270d0c
          name:
            description: name of user
            type: string
            maxLength: 1000
            example: Guess Who
    responses:
      200:
        description: Login user and redirect to profile page for that user
        schema:
          $ref: '#/definitions/User'
        headers:
          Set-Cookie:
            description: Set session cookie
            schema:
              type: string
              example: session=abcde12345; Path=/; HttpOnly
      302:
        description: If there was an error, display error and redirect to login
    """
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    # check if user actually exists
    # take the user supplied password, hash it, and compare it to the hashed password in database
    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login'))  # if user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)
    return redirect(url_for('main.profile'))

@auth.route('/logout')
@login_required
def logout():
    """Perform logout
          ---
      security:
        type: http
        scheme: basic
      responses:
        302:
          description: Redirect to index
    """
    logout_user()
    return redirect(url_for('main.index'))

@auth.route('/signup')
def signup():
    """Render signup.html
    ---
      responses:
        200:
          description: Render signup template
    """
    return render_template('signup.html')

@auth.route('/signup', methods=['POST'])
def signup_post():
    """Create/signup a new user
    ---
    consumes:
    - multipart/form-data
    parameters:
      - name: email address (username)
        in: formData
        type: string
        required: true
      - name: name
        in: formData
        type: string
        required: true
      - name: password
        in: formData
        type: string
        required: true
    responses:
      200:
        description: Create new user and redirect to login page
        schema:
          $ref: '#/definitions/User'
      302:
        description: If there was an error (like user already exists), redirect to signup page
    """
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    user = User.query.filter_by(
        email=email).first()  # if this returns a user, then the email already exists in database

    if user:  # if a user is found, we want to redirect back to signup page so user can try again
        flash('Email address already exists')
        return redirect(url_for('auth.signup'))

    # create new user with the form data. Hash the password so plaintext version isn't saved.
    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))

    # add the new user to the database
    database.session.add(new_user)
    database.session.commit()

    return redirect(url_for('auth.login'))


