import datetime
import os
import uuid
from os import environ

import stripe

from app import db
from app.models.accounts.accounts_model import User
from app.models.products.products_model import Booking, Product

class Payments:
    def __init__(self):
        pass
   
    def create_payment_link(
        self,
        linked_booking_id
    ):
        dates = []
        bookings = Booking.query.filter_by(linked_booking_id=str(linked_booking_id)).all()
        for booking in bookings:
            product = Product.query.filter_by(id=booking.product_id).first()
            instructor = User.query.filter_by(id=str(product.user_id)).first()
            customer = User.query.filter_by(id=booking.client_id).first()
            stripe.api_key = instructor.stripe_api_key
            start = booking.booking_date.strftime("%d/%m/%Y")
            dates.append(start)
        d_string = ""
        for d in dates:
            d_string = d_string + d + "\n "

        session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price_data": {
                        "currency": "gbp",
                        "product_data": {
                            "name": product.title,
                            "description": (
                                "You are booking "
                                + product.title
                                + " on the following dates "
                                + d_string
                            ),
                        },
                        "unit_amount": str(int(float(product.price) * 100)),
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            allow_promotion_codes=False,
            stripe_account=None,
            customer_email=customer.email,
            client_reference_id=str(linked_booking_id),
            success_url='https://dogtrainingrevolution.org/booking/confirmation/' + str(linked_booking_id),
            cancel_url='https://dogtrainingrevolution.org/cancel_bookings/' + str(linked_booking_id),
        )

        return session

