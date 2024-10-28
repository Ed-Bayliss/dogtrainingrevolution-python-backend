import os
from uuid import uuid4

from sqlalchemy.dialects.postgresql import UUID

from app import db
from sqlalchemy.ext.declarative import DeclarativeMeta

BaseModel: DeclarativeMeta = db.Model

class Product(BaseModel):
    """Product model."""

    __table_args__ = {"schema": "public"}
    __tablename__ = "products"
    
    id = db.Column(UUID(), primary_key=True, default=uuid4())
    title = db.Column(db.String(64), nullable=False, unique=False)
    location = db.Column(db.String(64), nullable=False, unique=False)
    start = db.Column(db.String(64), nullable=False, unique=False)
    end = db.Column(db.String(64), nullable=True, unique=False)
    category = db.Column(db.String(16), nullable=True, unique=False)
    spaces = db.Column(db.Integer, nullable=True, unique=False)
    colour = db.Column(db.String(16), nullable=False, unique=False)
    
    # Recurrence Fields
    is_recurring = db.Column(db.Boolean, default=False, nullable=False)
    recurrence_pattern = db.Column(db.String(16), nullable=True)  # e.g., daily, weekly, monthly
    recurrence_interval = db.Column(db.Integer, nullable=True)  # e.g., every 2 days/weeks
    recurrence_end = db.Column(db.String(64), nullable=True)  # End date for recurrence
    recurrence_days = db.Column(db.ARRAY(db.String(10)), nullable=True)  # Days of week (e.g., ['Monday', 'Wednesday'])

    short_desc = db.Column(db.String(512), nullable=True)
    full_desc = db.Column(db.String(50000), nullable=True)
    
    price = db.Column(db.Float, nullable=True, unique=False)

    def __init__(
        self,
        id,
        title,
        location,
        start,
        end=None,  # Optional field
        category=None,  # Optional field
        spaces=None,  # Optional field
        colour=None,
        is_recurring=False,
        recurrence_pattern=None,
        recurrence_interval=None,
        recurrence_end=None,
        recurrence_days=None,
        price=None,
        short_desc=None,
        full_desc=None,
    ):
        self.id = id
        self.title = title
        self.location = location
        self.start = start
        self.end = end
        self.category = category
        self.spaces = spaces
        self.colour = colour
        self.is_recurring = is_recurring
        self.recurrence_pattern = recurrence_pattern
        self.recurrence_interval = recurrence_interval
        self.recurrence_end = recurrence_end
        self.recurrence_days = recurrence_days
        self.price = price
        self.short_desc=short_desc
        self.full_desc=full_desc

    def to_dict(self):
        """Convert User object to dictionary for JSON serialization."""
        return {
            "id": str(self.id),  # Convert UUID to string for JSON compatibility
            "title": self.title,
            "start": self.start,
            "end": self.end,
            "spaces": self.spaces,
            "colour": self.colour,
            "is_recurring": self.is_recurring,
            "recurrence_pattern": self.recurrence_pattern,
            "recurrence_interval": self.recurrence_interval,
            "recurrence_end": self.recurrence_end,
            "recurrence_days": self.recurrence_days,
            "short_desc": self.short_desc,
            "full_desc": self.full_desc,
        }



class Booking(BaseModel):
    """Booking model."""

    __table_args__ = {"schema": "public"}
    __tablename__ = "bookings"

    id = db.Column(UUID(), primary_key=True, default=uuid4())
    
    # Foreign keys linking to Product, Pet, and Client
    product_id = db.Column(UUID(), db.ForeignKey('public.products.id'), nullable=False)
    pet_id = db.Column(UUID(), db.ForeignKey('public.pets.id'), nullable=False)
    client_id = db.Column(UUID(), db.ForeignKey('public.accounts.id'), nullable=False)
    
    # Other fields
    booking_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Integer, nullable=True)  # e.g., 1 = confirmed, 0 = pending, etc.

    # Relationships
    product = db.relationship("Product", backref="bookings")
    pet = db.relationship("Pet", backref="bookings")
    client = db.relationship("User", backref="bookings")

    def __init__(self, id, product_id, pet_id, client_id, booking_date, status=None):
        self.id = id
        self.product_id = product_id
        self.pet_id = pet_id
        self.client_id = client_id
        self.booking_date = booking_date
        self.status = status
