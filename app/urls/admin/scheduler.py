import pathlib
from flask import (
    Blueprint,
    app,
    current_app,
    flash,
    redirect,
    render_template,
    session,
    jsonify,
    request,
)
from flask_login import current_user, login_required
from app import scheduler
from app.urls.bookings.bookings_url import generate_calendar_ics

scheduler_ = Blueprint(
    "scheduler_", __name__, template_folder="templates", static_folder="static"
)

PARENT_PATH = str(pathlib.Path(__file__).parent.resolve())

UPLOAD_FOLDER = "app/static/uploads/"


# @scheduler.task('cron', id='pet_alerts', hour=19, minute=50)
@scheduler.task("interval", id="pet_alerts", minutes=1)
def calendar():
    with scheduler.app.app_context():
        print('refreshed cal')
        generate_calendar_ics()
