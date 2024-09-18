"""Initialize app."""
from flask import Flask, make_response
from flask_login import LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
login_manager = LoginManager()
# scheduler = APScheduler()


def create_app():
    """Construct the core app object."""
    app = Flask(__name__, instance_relative_config=False, template_folder="html")
    app.config.from_object("config.Config")

    # Initialize Plugins
    db.init_app(app)
    mail = Mail(app)
    login_manager.init_app(app)
    # scheduler.init_app(app)
    # scheduler.start()

    with app.app_context():
        # Register Blueprints
        from app.urls.root.root_url import root_url
        from app.urls.auth.auth_url import auth_url
        from app.urls.bookings.bookings_url import bookings_url
        from app.urls.home.home_url import home_url

        app.register_blueprint(root_url)
        app.register_blueprint(auth_url)
        app.register_blueprint(bookings_url)
        app.register_blueprint(home_url)

        from app.models.pets.pets_model import Pet
        from app.models.products.products_model import Booking, Product

        # Create Database Models
        db.create_all()
        db.session.commit()

        # Compile static assets
        # if app.config["FLASK_ENV"] == "development":
        #     compile_static_assets(app)
        return app
