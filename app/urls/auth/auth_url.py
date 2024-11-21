import base64
import datetime
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import secrets
import smtplib
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
        
        if existing_user and existing_user.check_password(password=data["login_passwd"].strip())[0] == True:
            if existing_user.verified == True:
                login_user(existing_user)
                return jsonify({"message": "success"})
            else:
                return jsonify({"message": "unverified"})
        else:
            return jsonify({"message": "incorrect"})
        
   return render_template('home/home.html')

@auth_url.route("/logout")
@login_required
def logout():
    """User log-out logic."""
    logout_user()
    return redirect("/")

@auth_url.route("/send_email", methods=["POST"])
def send_email():
    """
    User sign-up page.

    GET requests serve sign-up page.
    POST requests validate form & user creation.
    """
    data = request.json
    with open("app/static/emails/dtr_contact.html", "r") as body:
            body = body.read()
            body = body.replace("#NAME#", data['name'])
            body = body.replace("#EMAIL#", data['email'])
            body = body.replace("#SUBJECT#", data['subject'])
            body = body.replace("#MESSAGE#", data['message'])
    # send email with username password
    send_email(data['email'], "david.greaves@pawtul.com", "Dog Training Revolution - Contact", body)

    return jsonify({'successful': 200})


@auth_url.route("/signup", methods=["POST"])
def signup():
    """
    User sign-up page.

    GET requests serve sign-up page.
    POST requests validate form & user creation.
    """
    import random

    image = random.randint(0, 25)
    password_length = 13
    new_password = secrets.token_urlsafe(password_length)
    data = request.json
    
    existing_user = User.query.filter_by(
        email=data['registerEmail'].lower()
    ).first()

    if existing_user is None:
    
        user = User(
            id=str(uuid4()),
            firstname=data['registerName'],
            surname=data['registersurName'],
            email=data['registerEmail'].lower(),
            account_type='client',
            verified=False,
            password="",
            created_on=datetime.datetime.now(),
            last_login=datetime.datetime.now(),
            phone=data['registerPhone'],
            stripe_api_key="",
        )
        user.set_password(new_password)
        # print(user.password)

        db.session.add(user)
        db.session.commit()

        existing_user = User.query.filter_by(
            email=data['registerEmail'].lower()
        ).first()
        with open("app/static/emails/signup.html", "r") as body:
                body = body.read()
                body = body.replace("#FIRSTNAME#", data['registerName'])
                body = body.replace("#SURNAME#", data['registersurName'])
                body = body.replace("#USERNAME#", data['registerEmail'])
                body = body.replace("#PASSWORD#", new_password)
        # send email with username password
        send_email(data['registerEmail'], "david.greaves@pawtul.com", "Dog Training Revolution - Signup", body)

        login_user(existing_user)
        return jsonify({'successful': 200})

    else:
        login_user(existing_user)
        return jsonify({'error': 500})

@auth_url.route("/forgotPassword", methods=["POST"])
def forgotPassword():
    """
    User sign-up page.

    GET requests serve sign-up page.
    POST requests validate form & user creation.
    """
    import random

    image = random.randint(0, 25)
    password_length = 13
    new_password = secrets.token_urlsafe(password_length)
    data = request.json
    
    existing_user = User.query.filter_by(
        email=data['email'].lower()
    ).first()

    if existing_user:
    
        existing_user.set_password(new_password)
        db.session.commit()

        with open("app/static/emails/forgot.html", "r") as body:
                body = body.read()
                body = body.replace("#FIRSTNAME#", existing_user.firstname)
                body = body.replace("#SURNAME#", existing_user.surname)
                body = body.replace("#USERNAME#", existing_user.email)
                body = body.replace("#PASSWORD#", new_password)
        # send email with username password
        send_email(existing_user.email, "david.greaves@pawtul.com", "Dog Training Revolution - Forgot Password", body)

        return jsonify({'successful': 200})

    else:
        login_user(existing_user)
        return jsonify({'error': 500})


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
    return redirect(url_for("auth_url.login"))

def send_email(receiver, cc_email, subject, body):
    try:
        # Create a multipart message
        message = MIMEMultipart()
        message["From"] = "no-reply@pawtul.com"
        message["To"] = receiver
        message["Cc"] = cc_email
        message["Subject"] = subject

        message.attach(MIMEText(body, "html"))

        # Connect to the SMTP server and send the email
        with smtplib.SMTP("smtp.exchange2019.ionos.co.uk", 587) as server:
            server.starttls()
            server.login("no-reply@pawtul.com", "Ej-?bq5[X;?zfbzhX]Yf")
            server.send_message(message)

    except:
        flash("Email Error: Please check clients email address")

    """
    Logs a user out. (You do not need to pass the actual user.) This will
    also clean up the remember me cookie if it exists.
    """

    if "_user_id" in session:
        session.pop("_user_id")

    if "_fresh" in session:
        session.pop("_fresh")

    if "_id" in session:
        session.pop("_id")

    session.pop()
    # current_app.login_manager._update_request_context_with_user()
    return True

def send_email_bulk(receiver, cc_email, subject, body):
    try:
        # Create a multipart message
        message = MIMEMultipart()
        message["From"] = "no-reply@pawtul.com"
        message["To"] = receiver
        message["Cc"] = cc_email
        message["Subject"] = subject

        message.attach(MIMEText(body, "html"))

        # Connect to the SMTP server and send the email
        with smtplib.SMTP("smtp.exchange2019.ionos.co.uk", 587) as server:
            server.starttls()
            server.login("no-reply@pawtul.com", "Ej-?bq5[X;?zfbzhX]Yf")
            server.send_message(message)

    except:
        flash("Email Error: Please check clients email address")

    return True

