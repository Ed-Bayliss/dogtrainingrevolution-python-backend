"""Database models."""
import os
from uuid import uuid4

from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import UUID
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from sqlalchemy.ext.declarative import DeclarativeMeta

BaseModel: DeclarativeMeta = db.Model


class User(UserMixin, BaseModel):
    """User account model."""

    __table_args__ = {"schema": "public"}
    __tablename__ = "accounts"
    id = db.Column(UUID(), primary_key=True, unique=True, default=uuid4())
    firstname = db.Column(db.String(64), nullable=False, unique=False)
    surname = db.Column(db.String(64), nullable=False, unique=False)
    email = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(
        db.String(256), primary_key=False, unique=False, nullable=False, default=""
    )
    created_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    last_login = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    verified = db.Column(db.Boolean, unique=False, nullable=False)
    account_type = db.Column(db.String(64), nullable=False, unique=False)
    phone = db.Column(db.String(64), unique=True, nullable=False)
    stripe_api_key = db.Column(db.String(64), unique=True, nullable=False)

    def __init__(self, id, firstname, surname, email, password, created_on, last_login, verified, account_type, phone, stripe_api_key):
        self.id = id
        self.firstname = firstname
        self.surname = surname
        self.email = email
        self.password = password
        self.created_on = created_on
        self.last_login = last_login
        self.verified = verified
        self.account_type = account_type
        self.phone = phone
        self.stripe_api_key = stripe_api_key

    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password):
        """Check hashed password."""
    
        return check_password_hash(self.password, password),
    
    def to_dict(self):
        """Convert User object to dictionary for JSON serialization."""
        return {
            "id": str(self.id),  # Convert UUID to string for JSON compatibility
            "firstname": self.firstname,
            "surname": self.surname,
            "email": self.email,
            "created_on": self.created_on.isoformat() if self.created_on else None,  # Convert datetime to ISO format
            "last_login": self.last_login.isoformat() if self.last_login else None,  # Convert datetime to ISO format
            "verified": self.verified,
            "account_type": self.account_type,
            "phone": self.phone,
            # Password field is excluded for security reasons
        }

    def __repr__(self):
        return "<User {}>".format(self.email)