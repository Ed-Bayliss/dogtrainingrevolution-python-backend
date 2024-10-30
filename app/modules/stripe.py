import datetime
import os
import uuid
from os import environ

import stripe

from app import db
from app.models.products.products_model import Booking, Product

stripe.api_key = os.getenv('STRIPE')

class Payments:
    def __init__(self):
        self.api_key = stripe.api_key

   
    def create_payment_link(
        self,
        linked_booking_id
    ):
        dates = []
        bookings = Booking.query.filter_by(linked_booking_id=str(linked_booking_id)).all()
        for booking in bookings:
            product = Product.query.filter_by(id=booking.product_id).first()
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
            client_reference_id=str(linked_booking_id),
            success_url='https://dogtrainingrevolution.pawtul.com/booking/confirmation/' + str(linked_booking_id),
            cancel_url='https://dogtrainingrevolution.pawtul.com/cancel_bookings/' + str(linked_booking_id),
        )

        return session

    def get_balance(self, account_id):
        balance = stripe.Balance.retrieve(stripe_account=account_id)
        return balance

    def assign_account(self, business):
        subscription = Subscription.query.filter_by(
            business_id=str(business.id)
        ).first()
        customers = stripe.Customer.list()
        for customer in customers:
            if customer.email == business.email:
                if subscription is None:
                    suid = uuid.uuid4()
                    record = Subscription(
                        id=str(suid),
                        business_id=(str(business.id)),
                        customer_id=customer.id,
                        subscription_id=None,
                        product_id=None,
                        status=None,
                        end_of_cycle=None,
                    )
                    business.subscription_id = suid
                    db.session.add(record)
                    db.session.commit()

    def assign_subscription(self, business):
        subscriptions = stripe.Subscription.list()
        record = Subscription.query.filter_by(business_id=str(business.id)).first()
        for subscription in subscriptions:
            try:
                if record.customer_id == subscription.customer:
                    record.subscription_id = subscription.id
                    record.product_id = subscription["plan"].product
            except:
                pass
        db.session.commit()

    def is_subscription_active(self, subscription):
        subscription = stripe.Subscription.retrieve(subscription)
        return subscription["plan"]["active"]

    def cancel_subscription(self, subscription):
        stripe.Subscription.delete(subscription.subscription_id)
        stripe.Customer.delete(subscription.customer_id)

    def reset_subscription(self, user):
        user.subscription_id = "FREE"
        db.session.commit()
