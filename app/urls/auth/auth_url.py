import datetime
from uuid import uuid4
from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from flask_mail import Message
from sqlalchemy import desc, text, func
import pathlib

from app.models.accounts.accounts_model import User
from app import db, login_manager


# Blueprint Configuration
auth_url = Blueprint(
    "auth_url", __name__, template_folder="html", static_folder="static"
)

PARENT_PATH = str(pathlib.Path(__file__).parent.resolve())

UPLOAD_FOLDER = "app/static/uploads/"

@auth_url.route("/login", methods=['GET','POST'])
def login():
   if request.method == 'POST':
        data = request.json
    
        existing_user = User.query.filter_by(
            email=data['email'].lower()
        ).first()
        if existing_user and existing_user.check_password(password=data["password"].strip()):
            login_user(existing_user)
            return jsonify({})
   return render_template('login/login.html')

@auth_url.route("/logout")
@login_required
def logout():
    """User log-out logic."""
    logout_user()
    return redirect("/login")



@auth_url.route("/signup", methods=["POST"])
def signup():
    """
    User sign-up page.

    GET requests serve sign-up page.
    POST requests validate form & user creation.
    """
    import random

    image = random.randint(0, 25)
    data = request.json
    
    existing_user = User.query.filter_by(
        email=data['email'].lower()
    ).first()

    if existing_user is None:
    
        user = User(
            id=str(uuid4()),
            firstname="",
            surname="",
            email=data['email'],
            account_type='client',
            verified=False,
            password="",
            created_on=datetime.datetime.now(),
            last_login=datetime.datetime.now(),
        )
        user.set_password(data['password'])
        print(user.password)

        db.session.add(user)
        db.session.commit()

        existing_user = User.query.filter_by(
            email=data['email'].lower()
        ).first()
    login_user(existing_user)

    return jsonify({'successful': 200})

@login_manager.user_loader
def load_user(user_id):
    """Check if user is logged-in upon page load."""
    if user_id is not None:
        return User.query.get(user_id)
    return None


@login_manager.unauthorized_handler
def unauthorized():
    """Redirect unauthorized users to Login page."""
    flash("You must be logged in to view that page.")
    return redirect(url_for("login_blueprints.login"))
