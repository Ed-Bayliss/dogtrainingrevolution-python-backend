import os
from uuid import uuid4

from sqlalchemy.dialects.postgresql import UUID

from app import db
from sqlalchemy.ext.declarative import DeclarativeMeta

BaseModel: DeclarativeMeta = db.Model


class Client(BaseModel):
    """clients database model."""

    __table_args__ = {"schema": "public"}
    __tablename__ = "clients"

    id = db.Column(UUID(), primary_key=True, default=uuid4())
    firstname = db.Column(db.String(64), nullable=False, unique=False)
    lastname = db.Column(db.String(64), nullable=False, unique=False)
    email = db.Column(db.String(64), nullable=True, unique=False)
    phone = db.Column(db.String(16), nullable=True, unique=False)
    address1 = db.Column(db.String(64), nullable=True, unique=False)
    address2 = db.Column(db.String(64), nullable=True, unique=False)
    address3 = db.Column(db.String(64), nullable=True, unique=False)
    address4 = db.Column(db.String(64), nullable=True, unique=False)
    postcode = db.Column(db.String(16), nullable=True, unique=False)
    booking = db.Column(db.Boolean, nullable=True, unique=False)
    password = db.Column(db.String(64), nullable=False, unique=False)

    def __init__(
        self,
        id,
        business_id,
        firstname,
        lastname,
        email,
        phone,
        address1,
        address2,
        address3,
        address4,
        postcode,
        booking,
        password,
    ):
        self.id = id
        self.business_id = business_id
        self.firstname = firstname
        self.lastname = lastname
        self.email = email
        self.phone = phone
        self.address1 = address1
        self.address2 = address2
        self.address3 = address3
        self.address4 = address4
        self.postcode = postcode
        self.booking = booking
        self.password = password
