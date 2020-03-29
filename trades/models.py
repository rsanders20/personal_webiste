from . import db
from datetime import datetime


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(120))

    portfolios = db.relationship('Portfolio', backref='portfolios', lazy=True)

    def __init__(self, user_name=None, password=None):
        self.user_name = user_name
        self.password = password

    def __repr__(self):
        return '<user: {}, password: {}>'.format(self.user_name, self.password)


class Portfolio(db.Model):
    __tablename__ = 'portfolios'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(50))
    strategy = db.Column(db.String(50))
    trades = db.relationship('Trade', backref='trades', lazy=True)


class Trade(db.Model):
    __tablename__ = 'trades'
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    security = db.Column(db.String(10))
    value = db.Column(db.Float)
    n_shares = db.Column(db.Float)
    purchase_date = db.Column(db.DateTime, default = datetime.utcnow)
    sell_date = db.Column(db.DateTime, default = None)


class Dollar(db.Model):
    __tablename__ = 'dollars'
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    purchase_date = db.Column(db.DateTime, default = datetime.utcnow)
    value = db.Column(db.Float)
    added = db.Column(db.Boolean, default = False)
    de_invested = db.Column(db.Boolean, default = False)
    invested = db.Column(db.Boolean, default = False)

