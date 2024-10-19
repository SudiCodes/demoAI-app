from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
import re

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    mobile_number = db.Column(db.String(15), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    is_demo_active = db.Column(db.Boolean, default=False)
    is_subscribed = db.Column(db.Boolean, default=False)
    subscription_till = db.Column(db.DateTime, nullable=True)

    def __init__(self, email, password, first_name, last_name, mobile_number=None, state=None, 
                 is_demo_active=False, is_subscribed=False, subscription_till=None):
        self.email = email
        self.password = self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
        self.mobile_number = mobile_number
        self.state = state
        self.is_demo_active = is_demo_active
        self.is_subscribed = is_subscribed
        self.subscription_till = subscription_till
        self.username = self.generate_username(first_name, last_name)

    def set_password(self, password):
        return bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    @staticmethod
    def generate_username(first_name, last_name):
        username = (first_name[:3] + last_name[-3:]).lower()
        count = 1
        while User.query.filter_by(username=username).first():
            username = f"{username}{count}"
            count += 1
        return username
