from . import db
from datetime import datetime


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(120))
    trades = db.relationship('Trade', backref='users', lazy=True)

    def __init__(self, user_name=None, password=None):
        self.user_name = user_name
        self.password = password

    def __repr__(self):
        return '<user: {}, password: {}>'.format(self.user_name, self.password)


class Trade(db.Model):
    __tablename__ = 'trades'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    security = db.Column(db.String(3))
    value = db.Column(db.Float)
    n_shares = db.Column(db.Float)
    purchase_date = db.Column(db.DateTime, default = datetime.utcnow)

