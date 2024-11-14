from collections import defaultdict
import datetime
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
from app.models.products.products_model import Booking
from app.urls.bookings.bookings_url import generate_calendar_ics
from app import db

scheduler_ = Blueprint(
    "scheduler_", __name__, template_folder="templates", static_folder="static"
)

PARENT_PATH = str(pathlib.Path(__file__).parent.resolve())

UPLOAD_FOLDER = "app/static/uploads/"

BOOKING_COUNT = defaultdict(int)

# @scheduler.task('cron', id='pet_alerts', hour=19, minute=50)
@scheduler.task("interval", id="calendar_refresh", minutes=1)
def calendar():
    with scheduler.app.app_context():
        generate_calendar_ics()

@scheduler.task("interval", id="check_paid_bookings", minutes=1)
def check_paid_bookings():
    with scheduler.app.app_context():

        # Fetch all bookings with status 0
        bookings = Booking.query.filter_by(status=0).all()
        
        # Create a set of current booking IDs
        current_booking_ids = {booking.id for booking in bookings}
        
        # Loop through each booking
        for booking in bookings:
            # Increment the appearance count for each booking
            BOOKING_COUNT[booking.id] += 1
            print(booking.id, BOOKING_COUNT[booking.id])
            
            # Check if the booking has been seen 10 times
            if BOOKING_COUNT[booking.id] >= 4:
                # Delete the booking from the database
                db.session.delete(booking)
                db.session.commit()
                
                # Remove the booking from the dictionary
                del BOOKING_COUNT[booking.id]
                print(f"Deleted booking with ID {booking.id} after 10 appearances.")
        
        # Remove any entries from BOOKING_COUNT that are not in current_booking_ids
        for booking_id in list(BOOKING_COUNT.keys()):
            if booking_id not in current_booking_ids:
                del BOOKING_COUNT[booking_id]
                print(f"Removed booking ID {booking_id} from tracking as it no longer exists in the status=0 bookings.")
        
        # Optional: print the current booking counts for debugging
        print("Current booking counts:", dict(BOOKING_COUNT))

@scheduler.task("cron", id="send_reminders", hour=2)
# @scheduler.task("interval", id="send_reminders", seconds=10)
def send_reminders():
    with scheduler.app.app_context():
        # Get today's date
        today = datetime.datetime.today().date()
        
        # Fetch all bookings with status 1
        bookings = Booking.query.filter_by(status=1).all()
        
        # Loop through each booking
        for booking in bookings:
            # Check if the booking_date matches today
            if booking.booking_date.date() == today:
                print(f"Booking ID {booking.id} is today.")
                #send email reminder