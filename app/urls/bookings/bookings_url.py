import random
import secrets
from ics import Calendar, Event
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
from sqlalchemy import text

from flask_login import current_user, login_required, logout_user, login_user
from flask_mail import Message
from sqlalchemy import desc, text, func
import pathlib

from app.models.accounts.accounts_model import User
from app.models.products.products_model import Booking, Product
from app.models.pets.pets_model import Pet
from app.modules.stripe import Payments
from app.urls.auth.auth_url import send_email


# Blueprint Configuration
bookings_url = Blueprint(
    "bookings_url", __name__, template_folder="html", static_folder="static"
)

PARENT_PATH = str(pathlib.Path(__file__).parent.resolve())

UPLOAD_FOLDER = "app/static/uploads/"

from app import db

@bookings_url.route("/manage_bookings", methods=["GET"])
def manage_bookings():
    if "_user_id" in session:
        existing_user = User.query.filter_by(
            id=session["_user_id"]
        ).first()
    else:
        return redirect("/logout")
    
    if existing_user.account_type == "admin":
        bookings = db.session.execute(
            text(
                "SELECT public.bookings.id, public.bookings.booking_date, public.bookings.status, public.accounts.firstname, public.accounts.surname, public.pets.name, public.products.title "
                "FROM public.bookings "
                "INNER JOIN public.accounts ON public.bookings.client_id = public.accounts.id "
                "INNER JOIN public.pets ON public.bookings.pet_id = public.pets.id "
                "INNER JOIN public.products ON public.bookings.product_id = public.products.id "
                "ORDER BY booking_date DESC"
            )
        ).fetchall()
    else:
        bookings = db.session.execute(
            text(
                "SELECT public.bookings.id, public.bookings.booking_date, public.bookings.status, public.accounts.firstname, public.accounts.surname, public.pets.name, public.products.title "
                "FROM public.bookings "
                "INNER JOIN public.accounts ON public.bookings.client_id = public.accounts.id "
                "INNER JOIN public.pets ON public.bookings.pet_id = public.pets.id "
                "INNER JOIN public.products ON public.bookings.product_id = public.products.id "
                "WHERE public.bookings.client_id = :client_id "
                "ORDER BY booking_date DESC"
            ),
            {"client_id": existing_user.id}  # Binding the parameter safely
        ).fetchall()


    return render_template('loggedin/booking_list.html',
                            bookings=bookings,
                            existing_user=existing_user)


def generate_calendar_ics():
    # Initialize a new calendar
    calendar = Calendar()
    bookings = db.session.execute(
        text(
            "SELECT public.bookings.id, public.bookings.booking_date, public.bookings.status, public.accounts.firstname, public.accounts.surname, public.pets.name, public.products.title "
            "FROM public.bookings "
            "INNER JOIN public.accounts ON public.bookings.client_id = public.accounts.id "
            "INNER JOIN public.pets ON public.bookings.pet_id = public.pets.id "
            "INNER JOIN public.products ON public.bookings.product_id = public.products.id "
            "ORDER BY booking_date DESC"
        )
    ).fetchall()

    # Iterate over the SQL booking results and add each as an event
    for booking in bookings:
        # Create a new event for each booking
        event = Event()
        event.name = f"{booking.title} with {booking.name}"
        event.begin = booking.booking_date.strftime("%Y-%m-%d %H:%M:%S")
        event.description = (
            f"Status: {booking.status}\n"
            f"Client: {booking.firstname} {booking.surname}\n"
            f"Pet: {booking.name}\n"
            f"Product: {booking.title}"
        )

        # Add the event to the calendar
        calendar.events.add(event)

    # Write the calendar to an .ics file
    with open("app/static/calendar/bookings.ics", "w") as f:
        f.writelines(calendar)

    return

@bookings_url.route("/bookings_json", methods=["GET"])
def bookings_json():
    if "_user_id" in session:
        existing_user = User.query.filter_by(
            id=session["_user_id"]
        ).first()
    else:
        return redirect("/logout")
    
    if existing_user.account_type == "admin":
        bookings = db.session.execute(
            text(
                "SELECT public.bookings.id, public.bookings.booking_date, public.bookings.status, public.accounts.firstname, public.accounts.surname, public.pets.name AS pet_name, public.products.title "
                "FROM public.bookings "
                "INNER JOIN public.accounts ON public.bookings.client_id = public.accounts.id "
                "INNER JOIN public.pets ON public.bookings.pet_id = public.pets.id "
                "INNER JOIN public.products ON public.bookings.product_id = public.products.id "
                "ORDER BY booking_date DESC"
            )
        ).fetchall()
    else:
        bookings = db.session.execute(
            text(
                "SELECT public.bookings.id, public.bookings.booking_date, public.bookings.status, public.accounts.firstname, public.accounts.surname, public.pets.name AS pet_name, public.products.title "
                "FROM public.bookings "
                "INNER JOIN public.accounts ON public.bookings.client_id = public.accounts.id "
                "INNER JOIN public.pets ON public.bookings.pet_id = public.pets.id "
                "INNER JOIN public.products ON public.bookings.product_id = public.products.id "
                "WHERE public.bookings.client_id = :client_id "
                "ORDER BY booking_date DESC"
            ),
            {"client_id": existing_user.id}  # Binding the parameter safely
        ).fetchall()

    list_bookings = [booking_rows(r) for r in bookings]
    return jsonify(list_bookings)


def booking_rows(row):
    return dict(
        id=str(row.id),
        booking_date=row.booking_date,
        status=row.status,
        firstname=row.firstname,
        surname=row.surname,
        pet_name=row.pet_name,  # Updated key to pet_name
        title=row.title,
    )


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

@bookings_url.route("/external/bookings", methods=["GET"])
def external_bookings():
    return render_template('external/bookings.html')

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


@login_required
@bookings_url.route('/bookings/payment', methods=["POST"])
def booking_payment():
    product = Product.query.filter_by(id=request.json['eventId']).first()
    pet = Pet.query.filter_by(id=str(request.json['pet'])).first()



    # Example input
    event_datetime = datetime.strptime(request.json['eventDetails'].replace('Date: ', ''), '%d-%m-%Y %H:%M:%S')
    block_booking = product.block_booking  # Number of weeks to calculate

    # Generate list of dates, each one week apart
    dates_list = [event_datetime + timedelta(weeks=i) for i in range(block_booking)]
    linked_uuid = str(uuid.uuid4())
    for date in dates_list:
        uid = str(uuid.uuid4())
        record = Booking(
            id=str(uid),
            product_id=request.json['eventId'],
            linked_booking_id=str(linked_uuid),
            pet_id=str(pet.id),
            client_id=str(current_user.id),
            booking_date=date,
            status=0
        )
        db.session.add(record)
    db.session.commit()
    stripe_obj = Payments()
    payment_url = stripe_obj.create_payment_link(linked_uuid)
    generate_calendar_ics()
    return jsonify({'stripe_url': payment_url})


@login_required
@bookings_url.route('/external/bookings/payment', methods=["POST"])
def external_booking_payment():
    password_length = 13
    new_password = secrets.token_urlsafe(password_length)[:password_length]
    existing_user = User.query.filter_by(email=request.json['user']['email'].lower()).first()
    send_email_flag = False
    if existing_user is None:
        send_email_flag = True
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            firstname=request.json['user']['firstName'],
            surname=request.json['user']['surname'],
            email=request.json['user']['email'].lower(),
            account_type='client',
            verified=True,
            password="",
            created_on=datetime.now(),
            last_login=datetime.now(),
            phone=""
        )
        user.set_password(new_password)
        db.session.add(user)
        db.session.commit()
    else:
        user_id = str(existing_user.id)

    # Check if pet already exists based on client_id, name, and dob
    existing_pet = Pet.query.filter_by(
        client_id=user_id,
        name=request.json['pet']['name'],
        dob=request.json['pet']['dob']
    ).first()

    # If pet doesn't exist, create a new one
    if existing_pet is None:
        pet_id = str(uuid.uuid4())
        new_pet = Pet(
            id=pet_id,
            client_id=user_id,
            name=request.json['pet']['name'],
            breed=request.json['pet']['breed'],
            dob=request.json['pet']['dob'],
            microchip=request.json['pet']['microchip'],
            gender=request.json['pet']['gender'] == 1,
            neutered=request.json['pet']['neutered'] == 1
        )

        db.session.add(new_pet)
        db.session.commit()  # Commit the new pet
        existing_pet = Pet.query.filter_by(id=str(pet_id)).first()

    product = Product.query.filter_by(id=request.json['eventId']).first()
    if send_email_flag:
        with open("app/static/emails/signup.html", "r") as body:
            body = body.read()
            body = body.replace("#FIRSTNAME#", request.json['user']['firstName'])
            body = body.replace("#SURNAME#", request.json['user']['surname'])
            body = body.replace("#USERNAME#", request.json['user']['email'],)
            body = body.replace("#PASSWORD#", new_password)
        # send email with username password
        send_email(request.json['user']['email'], "david.greaves@pawtul.com", "Dog Training Revolution - Signup", body)
    existing_user = User.query.filter_by(
                email=request.json['user']['email'].lower()
            ).first()
    login_user(existing_user)


    # Example input
    event_datetime = datetime.strptime(request.json['eventDetails'].replace('Date: ', ''), '%d-%m-%Y %H:%M:%S')
    block_booking = product.block_booking  # Number of weeks to calculate

    # Generate list of dates, each one week apart
    dates_list = [event_datetime + timedelta(weeks=i) for i in range(block_booking)]
    linked_uuid = str(uuid.uuid4())
    for date in dates_list:
        uid = str(uuid.uuid4())
        record = Booking(
            id=str(uid),
            product_id=request.json['eventId'],
            linked_booking_id=str(linked_uuid),
            pet_id=str(existing_pet.id),
            client_id=str(current_user.id),
            booking_date=date,
            status=0
        )
        db.session.add(record)
    db.session.commit()
    stripe_obj = Payments()
    payment_url = stripe_obj.create_payment_link(linked_uuid)
    generate_calendar_ics()
    return jsonify({'stripe_url': payment_url})

@login_required
@bookings_url.route('/booking/confirmation/<uuid:linked_booking_id>', methods=["GET"])
def booking_confirmation(linked_booking_id):
    bookings = Booking.query.filter_by(linked_booking_id=str(linked_booking_id)).all()
    for booking in bookings:
        booking.status = 1
        db.session.commit()
    print('all booked')
    return redirect('/manage_bookings')


    

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
