"""Application entry point."""
import os
import shutil
from flask_login import current_user
from app import create_app
from flask import make_response, render_template, request, redirect, session
from flask_mail import Mail
from flask_session.__init__ import Session
from flask_mobility import Mobility
import datetime

app = create_app()
# app.config['MAIL_SERVER'] = 'smtp.exchange2019.ionos.co.uk'
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_USERNAME'] = 'no-reply@pawtul.com'
# app.config['MAIL_PASSWORD'] = 'Ej-?bq5[X;?zfbzhX]Yf'
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USE_SSL'] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
Mobility(app)
mail = Mail(app)
app = app




if __name__ == "__main__":
    app.run()
