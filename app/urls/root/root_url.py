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
from flask_login import current_user, login_required, logout_user, login_user
from flask_mail import Message
from sqlalchemy import desc, text, func
import pathlib

from app.models.products.products_model import Product


# Blueprint Configuration
root_url = Blueprint(
    "root_url", __name__, template_folder="html", static_folder="static"
)

PARENT_PATH = str(pathlib.Path(__file__).parent.resolve())

UPLOAD_FOLDER = "app/static/uploads/"

from app import db

@root_url.route("/", methods=["GET"])
def root():
   products = Product.query.filter_by().all()
   return render_template('home/home.html', products=products)
    # return render_template('admin/users.html', users=all_users, existing_user=existing_user)
    # return render_template('root/root.html')