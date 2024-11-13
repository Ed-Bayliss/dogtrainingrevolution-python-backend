import base64
import datetime
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
from flask_login import current_user, login_required, logout_user, login_user
from flask_mail import Message
from sqlalchemy import desc, text, func
import pathlib

from app.models.pets.pets_model import Pet
from app.models.products.products_model import Booking, Product
from app.models.accounts.accounts_model import User


# Blueprint Configuration
admin_url = Blueprint(
    "admin_url", __name__, template_folder="html", static_folder="static"
)

PARENT_PATH = str(pathlib.Path(__file__).parent.resolve())

UPLOAD_FOLDER = "app/static/uploads/"

from app import db

@login_required
@admin_url.route("/users", methods=["GET"])
def root():
    if "_user_id" in session:
        existing_user = User.query.filter_by(
            id=session["_user_id"]
        ).first()
    else:
        return redirect("/logout")
    if existing_user.account_type == "admin":
        all_users = (
            User.query.filter_by()
            .order_by(User.email)
            .all()
        )
    else:
        all_users = (
            User.query.filter_by(id=str(existing_user.id))
            .order_by(User.email)
            .all()
        )
    
    return render_template('admin/users.html', 
                           users=all_users,
                           existing_user=existing_user)

@admin_url.route("/users_json", methods=["POST", "GET"])
@login_required
def users_json():
    if "_user_id" in session:
        existing_user = User.query.filter_by(
            id=session["_user_id"]
        ).first()
    else:
        return redirect("/logout")
    if existing_user.account_type == "admin":
        all_users = (
            User.query.filter_by()
            .order_by(User.email)
            .all()
        )
    else:
        all_users = (
            User.query.filter_by(id=str(existing_user.id))
            .order_by(User.email)
            .all()
        )
    list_all_users = [transaction_row(r) for r in all_users]
    return jsonify(list_all_users)

def transaction_row(row):
    return dict(
        id=row.id,
        firstname=row.firstname,
        surname=row.surname,
        email=row.email,
        verified=row.verified,
        account_type=row.account_type,
        phone=row.phone,
    )


@admin_url.route("/loaduserdetails", methods=["POST"])
@login_required
def loaduserdetails():
    users_details = (
        User.query.filter_by(id=str(request.json["userRef"]))
        .order_by(User.email)
        .all()
    )
    users_details_list = [User.to_dict() for User in users_details]
    return jsonify(users_details_list)

@admin_url.route("/updateduserdetails", methods=["POST"])
@login_required
def updateduserdetails():
    users_details = User.query.filter_by(id=str(request.json["userRef"])).first()
    if users_details is not None:
        users_details.firstname = request.json["firstname"]
        users_details.surname = request.json["surname"]
        users_details.email = request.json["email"]
        users_details.account_type = request.json["account_type"]
        users_details.phone = request.json["phone"]
        users_details.verified = request.json["verified"]

        if request.json["password"] != '':
            users_details.set_password(request.json["password"])

        db.session.commit()
    
    return jsonify({"msg": "complete"})


@admin_url.route("/deleteuserdetails", methods=["POST"])
@login_required
def deleteuserdetails():

    users_details = User.query.filter_by(id=str(request.json["userRef"])).first()
    if users_details is not None:
        db.session.delete(users_details)
        db.session.commit()
    
    return jsonify({"msg": "complete"})


@login_required
@admin_url.route("/classes", methods=["GET"])
def classes_root():
    if "_user_id" in session:
        existing_user = User.query.filter_by(
            id=session["_user_id"]
        ).first()
    else:
        return redirect("/logout")
    
    if existing_user.account_type == "admin":
        products = Product.query.filter_by().all()
    else:
        products = []
    instructors = User.query.filter_by(account_type='admin').all()
    return render_template('admin/classes.html',
                          users=[],
                          existing_user=existing_user,
                          products=products,
                          instructors=instructors)

@admin_url.route("/classes_json", methods=["GET", "POST"])
@login_required
def classes_json():
    if "_user_id" in session:
        existing_user = User.query.filter_by(
            id=session["_user_id"]
        ).first()
    else:
        return redirect("/logout")
    
    if existing_user.account_type == "admin":
        products = Product.query.filter_by().all()
    else:
        products = []

    class_details_list = [Product.to_dict() for Product in products]

    return jsonify(class_details_list)

# @admin_url.route("/classeslist_json", methods=["GET", "POST"])
# @login_required
# def classeslist_json():
   
#     products = Product.query.filter_by().all()

#     class_details_list = [Product.to_dict() for Product in products]

#     return jsonify(class_details_list)


@login_required
@admin_url.route("/product_add", methods=["GET", "POST"])
def add_product():
    if "_user_id" not in session:
        return redirect("/logout")
    
    existing_user = User.query.filter_by(id=session["_user_id"]).first()

    # Parse datetime fields
    start_str = request.form['productStart'].strip()
    try:
        # Parse the string into a datetime object
        start_datetime = datetime.datetime.strptime(start_str, '%Y-%m-%dT%H:%M')
        # Format the datetime object to the new format
        formatted_start = start_datetime.strftime('%Y-%m-%d %H:%M:%S')
        print("Parsed and formatted date:", formatted_start)
    except ValueError as e:
        print("Error parsing date:", e)
        print("Date string received:", start_str)

    end_str = request.form['productEnd'].strip()
    try:
        # Parse the string into a datetime object
        end_datetime = datetime.datetime.strptime(end_str, '%Y-%m-%dT%H:%M')
        # Format the datetime object to the new format
        formatted_end = end_datetime.strftime('%Y-%m-%d %H:%M:%S')
        print("Parsed and formatted date:", formatted_end)
    except ValueError as e:
        print("Error parsing date:", e)
        print("Date string received:", end_str)

    # Handle recurrence days as a list
    recurrence_days = request.form.get('productrecurrence_days', '[]')
    recurrence_days = eval(recurrence_days) if isinstance(recurrence_days, str) else recurrence_days

    # Handle the file upload if an image is provided
    image_url = None
    if 'productImage' in request.files:
        image_file = request.files['productImage']
        if image_file.filename != '':
            # Read the image file and encode it to base64
            image_data = image_file.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        else:
            image_base64 = None
    else:
        image_base64 = None

    session_days=request.form['chkDays'] == 'true',  # Boolean check
    session_weeks=request.form['chkWeeks'] == 'true',

    session_type = 'weeks'
    if session_days == True:
        session_type = 'days'

    # Create product
    product = Product(
        id=str(uuid.uuid4()),
        title=request.form['productTitle'],
        start=formatted_start,
        end=formatted_end,
        spaces=request.form['productSpaces'],
        colour=request.form['productColour'],
        is_recurring=request.form['productRecur'] == 'true',  # Boolean check
        session_type=session_type,
        block_booking=request.form['productinterval'],
        recurrence_pattern=request.form['productRecurrence'],
        location=request.form['productLocation'],
        recurrence_days=recurrence_days,
        recurrence_end=request.form['productRecurEnd'],
        price=request.form['productPrice'],  # Add price
        user_id=request.form['productInstructor'],  # Add instructor
        # Get the short description from the form and trim it to 512 characters
        short_desc = request.form['short_desc'][:512],
        full_desc = request.form['full_desc'],

        image_base64=image_base64
    )

    # Save to database
    db.session.add(product)
    db.session.commit()
    
    return jsonify({"msg": "complete"})

@login_required
@admin_url.route("/loadproductdetails", methods=["GET", "POST"])
def loadproductdetails():
    product_details = (
        Product.query.filter_by(id=str(request.json["productRef"]))
        .order_by(Product.title)
        .all()
    )
    product_details_list = [Product.to_dict() for Product in product_details]
    return jsonify(product_details_list)

@admin_url.route("/updatedproductdetails", methods=["POST"])
@login_required
def updatedproductdetails():
    if "_user_id" not in session:
        return redirect("/logout")

    product_details = Product.query.filter_by(id=str(request.form["productRef"])).first()

    if product_details is None:
        return jsonify({"error": "Product not found"}), 404

    # Parse datetime fields
    # start_str = request.form['productStart']
    # end_str = request.form['productEnd']
    start_str = request.form['productStart'].strip()
    try:
        # Parse the string into a datetime object
        start_datetime = datetime.datetime.strptime(start_str, '%Y-%m-%dT%H:%M')
        # Format the datetime object to the new format
        formatted_start = start_datetime.strftime('%Y-%m-%d %H:%M:%S')
        print("Parsed and formatted date:", formatted_start)
    except ValueError as e:
        print("Error parsing date:", e)
        print("Date string received:", start_str)

    end_str = request.form['productEnd'].strip()
    try:
        # Parse the string into a datetime object
        end_datetime = datetime.datetime.strptime(end_str, '%Y-%m-%dT%H:%M')
        # Format the datetime object to the new format
        formatted_end = end_datetime.strftime('%Y-%m-%d %H:%M:%S')
        print("Parsed and formatted date:", formatted_end)
    except ValueError as e:
        print("Error parsing date:", e)
        print("Date string received:", end_str)

    # Handle recurrence days as a list
    recurrence_days = request.form.get('productrecurrence_days', '[]')
    recurrence_days = eval(recurrence_days) if isinstance(recurrence_days, str) else recurrence_days

    # Handle the file upload if an image is provided
    # if 'productImage' in request.files:
    #     image_file = request.files['productImage']
    #     if image_file.filename != '':
    #         # Read the image file and encode it to base64
    #         image_data = image_file.read()
    #         image_base64 = base64.b64encode(image_data).decode('utf-8')
    #         product_details.image_base64 = image_base64
    # If no new image is uploaded, keep the existing image

    product_details.image_base64 = request.form['productImage']
    # Update product details
    product_details.title = request.form['productTitle']
    product_details.start = formatted_start
    product_details.end = formatted_end
    product_details.spaces = request.form['productSpaces']
    product_details.colour = request.form['productColour']
    product_details.is_recurring = request.form['productRecur'] == 'true'  # Boolean check
    product_details.recurrence_pattern = request.form['productRecurrence']
    product_details.location = request.form['productLocation']
    product_details.recurrence_days = recurrence_days
    product_details.block_booking = request.form['productinterval']
    product_details.recurrence_end = request.form['productRecurEnd']
    product_details.price = request.form['productPrice']
    product_details.user_id = request.form['productInstructor']
    # Get the short description from the form and trim it to 512 characters
    product_details.short_desc = request.form['short_desc'][:512]
    product_details.full_desc = request.form['full_desc']

    # Save changes to the database
    db.session.commit()

    return jsonify({"msg": "complete"})

@admin_url.route("/product_delete", methods=["POST"])
@login_required
def product_delete():

    product_details = Product.query.filter_by(id=str(request.json["productRef"])).first()
    if product_details is not None:
        db.session.delete(product_details)
        db.session.commit()
    
    return jsonify({"msg": "complete"})

@login_required
@admin_url.route("/pets", methods=["GET"])
def pets_root():
    if "_user_id" in session:
        existing_user = User.query.filter_by(id=session["_user_id"]).first()
    else:
        return redirect("/logout")
    
    if existing_user.account_type == "admin":
        # pets = Pet.query.filter_by().all()
        pets_with_users = db.session.execute(
            text(
                "select public.pets.id, public.accounts.firstname, public.accounts.surname, public.pets.name, public.pets.breed From public.pets left join public.accounts on public.pets.client_id = public.accounts.id order by public.accounts.surname, public.accounts.firstname, public.pets.name"
            )
        ).all()
        users = User.query.filter_by().all()
    else:
        pets_with_users = Pet.query.filter_by(client_id=session["_user_id"]).all()
        users = User.query.filter_by(id=session["_user_id"]).all()
    
    return render_template('user/pets.html',
                          pets=pets_with_users,
                          users=users,
                          existing_user=existing_user)

@login_required
@admin_url.route("/pets_json", methods=["GET"])
def pets_json():
    if "_user_id" in session:
        existing_user = User.query.filter_by(id=session["_user_id"]).first()
    else:
        return redirect("/logout")
    
    if existing_user.account_type == "admin":
        # Admin query to get all pets with user details
        pets_with_users = db.session.execute(
            text(
                """
                SELECT public.pets.id, 
                       public.accounts.firstname, 
                       public.accounts.surname, 
                       public.pets.name, 
                       public.pets.breed 
                FROM public.pets 
                LEFT JOIN public.accounts 
                ON public.pets.client_id = public.accounts.id 
                ORDER BY public.accounts.surname, public.accounts.firstname, public.pets.name;
                """
            )
        ).all()
    else:
        # Non-admin query to get only pets associated with the current user
        pets_with_users = db.session.execute(
            text(
                """
                SELECT public.pets.id, 
                       public.accounts.firstname, 
                       public.accounts.surname, 
                       public.pets.name, 
                       public.pets.breed 
                FROM public.pets 
                LEFT JOIN public.accounts 
                ON public.pets.client_id = public.accounts.id 
                WHERE public.accounts.id = :user_id
                ORDER BY public.accounts.surname, public.accounts.firstname, public.pets.name;
                """
            ),
            {"user_id": existing_user.id}
        ).all()
    
    list_pets = [pet_rows(r) for r in pets_with_users]
    return jsonify(list_pets)

def pet_rows(row):
    return dict(
        id=str(row.id),
        firstname=row.firstname,
        surname=row.surname,
        name=row.name,
        breed=row.breed
    )


@login_required
@admin_url.route("/pets_add", methods=["GET", "POST"])
def pets_add():
    pet = Pet(
        id=str(uuid.uuid4()),
        client_id=request.json['client_id'],
        name=request.json['name'],
        breed=request.json['breed'],
        dob=request.json['dob'],
        microchip=request.json['microchip'],
        gender=request.json['gender'] == '1',
        neutered=request.json['neutered'] == '1',
    )

    db.session.add(pet)
    db.session.commit()
    return jsonify({"msg": "complete"})

@admin_url.route("/loadpetdetails", methods=["POST"])
@login_required
def loadpetdetails():
    pet_details = (
        Pet.query.filter_by(id=str(request.json["petRef"]))
        .order_by(Pet.name)
        .all()
    )
    pet_details_list = [pet.to_dict() for pet in pet_details]
    return jsonify(pet_details_list)


@admin_url.route("/pet_update", methods=["POST"])
@login_required
def pet_update():
    pet_details = Pet.query.filter_by(id=str(request.json["petRef"])).first()
    if pet_details is not None:
        pet_details.name = request.json["name"]
        pet_details.breed = request.json["breed"]
        pet_details.dob = request.json["dob"]
        pet_details.microchip = request.json["microchip"]
        pet_details.gender = request.json['gender'] == '1'
        pet_details.neutered = request.json['neutered'] == '1'
        db.session.commit()
    
    return jsonify({"msg": "complete"})

@admin_url.route("/pet_delete", methods=["POST"])
@login_required
def pet_delete():

    pet_details = Pet.query.filter_by(id=str(request.json["petRef"])).first()
    if pet_details is not None:
        db.session.delete(pet_details)
        db.session.commit()
    
    return jsonify({"msg": "complete"})


