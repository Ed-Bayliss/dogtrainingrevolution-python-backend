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
#    users = User.query.filter_by().all()
   all_users = (
        User.query.filter_by()
        .order_by(User.email)
        .all()
    )
   return render_template('admin/users.html',
                          users=all_users)


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
#    all_users = (
#         User.query.filter_by()
#         .order_by(User.email)
#         .all()
#     )
    return render_template('admin/classes.html',
                          users=[])

@login_required
@admin_url.route("/pets", methods=["GET"])
def pets_root():
    if "_user_id" in session:
        user_info = User.query.filter_by(id=session["_user_id"]).first()
    else:
        return redirect("/logout")
    
    if user_info.account_type == "admin":
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
                          users=users)

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
