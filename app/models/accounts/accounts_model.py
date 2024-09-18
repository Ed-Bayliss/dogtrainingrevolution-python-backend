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

    def __init__(self, id, firstname, surname, email, password, created_on, last_login, verified, account_type):
        self.id = id
        self.firstname = firstname
        self.surname = surname
        self.email = email
        self.password = password
        self.created_on = created_on
        self.last_login = last_login
        self.verified = verified
        self.account_type = account_type

    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password):
        """Check hashed password."""
    
        return check_password_hash(self.password, password),
       

    def __repr__(self):
        return "<User {}>".format(self.username)