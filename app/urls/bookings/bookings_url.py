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
            """SELECT 
                public.bookings.id, 
                public.bookings.booking_date, 
                public.bookings.status, 
                public.accounts.firstname, 
                public.accounts.surname, 
                public.pets.name, 
                public.products.title,
                public.products.start,
                public.products.end
            FROM 
                public.bookings
            INNER JOIN 
                public.accounts ON public.bookings.client_id = public.accounts.id
            INNER JOIN 
                public.pets ON public.bookings.pet_id = public.pets.id
            INNER JOIN 
                public.products ON public.bookings.product_id = public.products.id
            ORDER BY 
                booking_date DESC;"""
        )
    ).fetchall()

    # Iterate over the SQL booking results and add each as an event
    for booking in bookings:
        # Extract date and time components
        event_date = booking.booking_date.strftime('%Y-%m-%d')
        start_time = booking.start.split(' ')[1]  # Extract the time part
        end_time = booking.end.split(' ')[1]  # Extract the time part

        # Combine date with start and end times
        event_start = f"{event_date} {start_time}"
        event_end = f"{event_date} {end_time}"

        # Create a new event for each booking
        event = Event()
        event.name = f"{booking.title} with {booking.name}"
        event.begin = datetime.strptime(event_start, "%Y-%m-%d %H:%M:%S")
        event.end = datetime.strptime(event_end, "%Y-%m-%d %H:%M:%S")
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
                "ORDER BY booking_date ASC"
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
                "ORDER BY booking_date ASC"
            ),
            {"client_id": existing_user.id}  # Binding the parameter safely
        ).fetchall()

    list_bookings = [booking_rows(r) for r in bookings]
    return jsonify(list_bookings)

@bookings_url.route("/admin_delete_booking", methods=["POST"])
def admin_delete_booking():
    booking = Booking.query.filter_by(id=str(request.json['booking_id'])).first()
    db.session.delete(booking)
    db.session.commit()
    return jsonify({})

@bookings_url.route("/save_edit_booking", methods=["POST"])
def save_edit_booking():
    booking = Booking.query.filter_by(id=str(request.json['booking_id'])).first()
    booking.booking_date = request.json['booking_date']
    db.session.commit()
    return jsonify({})

@bookings_url.route("/get_all_products", methods=["POST"])
def get_all_products():
    products = Product.query.all()
    all_products = {}
    for product in products:
        all_products[str(product.id)] = product.title
    return jsonify(all_products)

@bookings_url.route("/get_all_clients", methods=["POST"])
def get_all_clients():
    clients = User.query.filter_by(account_type="client").all()
    all_clients = {}
    for client in clients:
        all_clients[str(client.id)] = client.firstname + ' ' + client.surname
    return jsonify(all_clients)


@bookings_url.route("/get_filtered_pets", methods=["POST"])
def get_filtered_pets():
    pets = Pet.query.filter_by(client_id=str(request.json['client_id'])).all()
    all_pets = {}
    for pet in pets:
        all_pets[str(pet.id)] = pet.name
    return jsonify(all_pets)

@bookings_url.route("/admin_create_booking", methods=["POST"])
def admin_create_booking():
    print(request.json)
    booking = Booking(
        id=str(uuid.uuid4()),
        product_id=str(request.json['bookingId']),
        pet_id=str(request.json['petId']),
        client_id=str(request.json['clientId']),
        booking_date=request.json['bookingDate'],
        status=1,
        linked_booking_id=None,
    )
    db.session.add(booking)
    db.session.commit()
    return jsonify({})
       


@bookings_url.route("/admin_get_booking", methods=["POST"])
def admin_get_booking():
    booking = db.session.execute(
        text(
            "SELECT public.bookings.id, public.bookings.booking_date, public.bookings.status, public.accounts.firstname, public.accounts.surname, public.pets.name AS pet_name, public.products.title "
            "FROM public.bookings "
            "INNER JOIN public.accounts ON public.bookings.client_id = public.accounts.id "
            "INNER JOIN public.pets ON public.bookings.pet_id = public.pets.id "
            "INNER JOIN public.products ON public.bookings.product_id = public.products.id "
            "WHERE public.bookings.id = :booking_id "
            "ORDER BY booking_date ASC"
        ),
        {"booking_id": str(request.json['booking_id'])}  # Binding the parameter safely
    ).fetchone()
    return jsonify(booking_row(booking))


def booking_row(booking):
    return dict(
        id=str(booking.id),
        booking_date=booking.booking_date,
        status=booking.status,
        firstname=booking.firstname,
        surname=booking.surname,
        pet_name=booking.pet_name,  # Updated key to pet_name
        title=booking.title,
    )

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
            phone="",
            stripe_api_key="",
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
    print(product.session_type)
    if product.session_type == 'days':
        dates_list = [event_datetime + timedelta(days=i) for i in range(block_booking)]
    else:
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
    # Query to get product location using parameterized query
    product_id = bookings[0].product_id
    products = db.session.execute(
        text("SELECT location FROM public.products WHERE id=:product_id"),
        {'product_id': product_id}
    ).first()

    client_id = bookings[0].client_id
    clients = db.session.execute(
        text("select accounts.email from public.accounts where id=:client_id"),
        {'client_id': client_id}
    ).first()

    # Accumulate booking info
    booking_info = ""
    for booking in bookings:
        booking.status = 1
        formatted_date = booking.booking_date.strftime("%d/%m/%Y %H:%M")
        booking_info += f"{formatted_date}<br>"

    # Commit all changes after the loop
    db.session.commit()

    # Prepare email content with data from request and booking info
    data = request.json
    with open("app/static/emails/dtr_contact.html", "r") as file:
        body = file.read()
        body = body.replace("#classname#", data['classname'])
        body = body.replace("#location#", products[0])  # Access products as a tuple
        body = body.replace("#booking_info#", booking_info)  # Use accumulated booking_info

    # send email with username password
    send_email(clients[0], "david.greaves@pawtul.com", "Dog Training Revolution - Confirmation", body)

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
