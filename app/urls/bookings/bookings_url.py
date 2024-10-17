import uuid
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

from datetime import datetime, timedelta

from datetime import datetime, timedelta
from sqlalchemy import text

from flask_login import current_user, login_required, logout_user, login_user
from flask_mail import Message
from sqlalchemy import desc, text, func
import pathlib

from app.models.accounts.accounts_model import User
from app.models.products.products_model import Booking, Product
from app.models.pets.pets_model import Pet


# Blueprint Configuration
bookings_url = Blueprint(
    "bookings_url", __name__, template_folder="html", static_folder="static"
)

PARENT_PATH = str(pathlib.Path(__file__).parent.resolve())

UPLOAD_FOLDER = "app/static/uploads/"

from app import db

@bookings_url.route("/bookings", methods=["GET"])
def root():
    if "_user_id" in session:
        existing_user = User.query.filter_by(
            id=session["_user_id"]
        ).first()
    else:
        return redirect("/logout")
    pets = Pet.query.filter_by(client_id=current_user.id).all()
    return render_template('loggedin/bookings.html',
                            pets=pets,
                            existing_user=existing_user)

@login_required
@bookings_url.route('/bookings/create', methods=["POST"])
def booking_create():
    pet = Pet.query.filter_by(id=str(request.json['pet'])).first()
    event_datetime = datetime.strptime(request.json['eventDetails'].replace('Date: ',''), '%d-%m-%Y %H:%M:%S')
    uid = str(uuid.uuid4())
    record = Booking(
        id=str(uid),
        product_id=request.json['eventId'],
        pet_id=str(pet.id),
        client_id=str(current_user.id),
        booking_date=event_datetime,
        status=0)
    record.client_id=str(current_user.id)
    db.session.add(record)
    db.session.commit()
    booking = Booking.query.filter_by(id=str(uid)).first()
    booking.client_id=current_user.id,
    db.session.commit()
    return jsonify({})


@bookings_url.route('/bookings/data', methods=["GET"])
def bookings():
    products = db.session.execute(
        text(
            "SELECT * FROM public.products ORDER BY start"
        )
    ).fetchall()
    # products = []
    # Generate all events, including recurring ones
    all_events = []
    for product in products:
        # Generate the individual and recurring events for each product
        events = generate_recurring_events(product)
        all_events.extend(events)

    return all_events
   


# Utility function to handle recurrence generation and booking check
def generate_recurring_events(row):
    events = []
    start_date = datetime.strptime(row.start, "%Y-%m-%d %H:%M:%S")  # Parse the start date
    end_date = datetime.strptime(row.recurrence_end, "%Y-%m-%d") if row.recurrence_end else None

    if not row.is_recurring:
        # If the event is not recurring, just return the single event with booking check
        return [generate_event_with_booking_check(row, start_date)]

    # Generate recurring events
    current_date = start_date
    recurrence_pattern = row.recurrence_pattern
    interval = row.recurrence_interval or 1  # Default to 1 if interval is not set
    days_of_week = [int(day) for day in row.recurrence_days] or []

    # Adjust days_of_week to match Python's weekday convention if necessary
    days_of_week = [(day + 6) % 7 for day in days_of_week]  # Shift days so that 0=Monday

    while True:
        if end_date and current_date > end_date:  # Break if we go past the recurrence end date
            break

        # Handle weekly recurrence
        if recurrence_pattern == 'weekly' and days_of_week:
            week_start = current_date - timedelta(days=current_date.weekday())  # Get the Monday of the current week
            for day in days_of_week:
                event_date = week_start + timedelta(days=day)
                # Ensure we add the event if it's on or before the end_date
                if event_date >= start_date and (not end_date or event_date <= end_date):
                    events.append(generate_event_with_booking_check(row, event_date))
            current_date += timedelta(weeks=interval)

        # Handle daily recurrence
        elif recurrence_pattern == 'daily':
            if not end_date or current_date <= end_date:  # Ensure current date is before or on end_date
                events.append(generate_event_with_booking_check(row, current_date))
            current_date += timedelta(days=interval)

        # Handle monthly recurrence
        elif recurrence_pattern == 'monthly':
            if not end_date or current_date <= end_date:
                events.append(generate_event_with_booking_check(row, current_date))
            current_date = add_months(current_date, interval)

        # Handle yearly recurrence
        elif recurrence_pattern == 'yearly':
            if not end_date or current_date <= end_date:
                events.append(generate_event_with_booking_check(row, current_date))
            current_date = add_years(current_date, interval)

        # Exit the loop if there is no end date and we have enough recurrences
        if not end_date and len(events) > 50:  # Limit to 50 occurrences if no end date
            break

    return events



# Helper function to generate an event and check for existing bookings
def generate_event_with_booking_check(row, event_date):
    event_time_str = event_date.strftime("%Y-%m-%d %H:%M:%S")
    
    # Query to check how many bookings exist for this event time
    existing_bookings = db.session.execute(
        text(
            "SELECT COUNT(*) FROM public.bookings WHERE booking_date = :event_time"
        ),
        {"event_time": event_time_str}
    ).scalar()

    # Calculate available spaces by deducting the number of bookings from the total spaces
    available_spaces = row.spaces - existing_bookings if row.spaces is not None else "N/A"
    # Generate the event with the updated spaces
    return {
        "eventName": f"{event_date.strftime('%H:%M')} {row.title} ({available_spaces} Spaces)",
        "calendar": row.category,
        "color": row.colour,
        "eventTime": event_time_str,
        "productId": row.id,
    }

# Helper functions for monthly and yearly increments
def add_months(current_date, months):
    new_month = current_date.month + months
    new_year = current_date.year + new_month // 12
    new_month = new_month % 12 or 12
    return current_date.replace(year=new_year, month=new_month)

def add_years(current_date, years):
    return current_date.replace(year=current_date.year + years)
