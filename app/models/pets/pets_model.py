import os
from uuid import uuid4

from sqlalchemy.dialects.postgresql import UUID

from app import db
from sqlalchemy.ext.declarative import DeclarativeMeta

BaseModel: DeclarativeMeta = db.Model


class Pet(BaseModel):
    """pets database model."""

    __table_args__ = {"schema": "public"}
    __tablename__ = "pets"
    
    id = db.Column(UUID(), primary_key=True, default=uuid4())
    client_id = db.Column(UUID(), nullable=True)
    name = db.Column(db.String(128), nullable=True, unique=False)
    breed = db.Column(db.String(128), nullable=True, unique=False)
    dob = db.Column(db.String(16), nullable=True, unique=False)
    microchip = db.Column(db.String(100), nullable=True, unique=False)
    gender = db.Column(db.Boolean, nullable=True, unique=False)
    neutered = db.Column(db.Boolean, nullable=True, unique=False)
    

    def __init__(
        self,
        id,
        client_id,
        name,
        breed,
        type,
        dob,
        microchip,
        gender,
        neutered,
    ):
        self.id = id
        self.client_id = client_id
        self.name = name
        self.breed = breed
        self.type = type
        self.dob = dob
        self.microchip = microchip
        self.gender = gender
        self.neutered = neutered
