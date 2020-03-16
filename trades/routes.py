from functools import wraps

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import validators

from . import db
from .models import User

bp = Blueprint('routes', __name__)


class RegisterForm(FlaskForm):
    user_name = StringField('user_name', [validators.InputRequired()])
    password = StringField('password', [validators.InputRequired()])


@bp.route('/register/', methods=('GET', 'POST'))
def register():
    print("starting register")
    register_form = RegisterForm()
    print(register_form.user_name.data, register_form.password.data)
    if register_form.validate_on_submit():
        print(User.query.filter_by(user_name=register_form.user_name.data).one_or_none())
        # Check if the user is in the database
        if User.query.filter_by(user_name=register_form.user_name.data).one_or_none() is not None:
            return render_template('register.html',
                                   form=register_form,
                                   message="User Already Exists, Please choose another user name")

        user = User(register_form.user_name.data, register_form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('routes.login'))

    return render_template('register.html',
                           form=register_form,
                           message="Enter a Unique User Name and Password")


@bp.route('/logout/')
def logout():
    print('starting logout')
    session.clear()
    return redirect(url_for('routes.login'))


@bp.route('/login/', methods=('GET', 'POST'))
def login():
    login_form = RegisterForm()
    if request.method == 'POST' and login_form.validate():
        existing_user = User.query.filter_by(user_name = login_form.user_name.data,
                                             password = login_form.password.data).one_or_none()
        if existing_user is None:
            return render_template('register.html', form=login_form, message="User name or password not correct")

        session['user_name'] = login_form.user_name.data
        return redirect(url_for('routes.portfolio'))

    return render_template('register.html', form=login_form, message="Enter your user name and password")


def login_required(route_function):
    @wraps(route_function)
    def decorated_function(*args, **kwgs):
        if 'user_name' in session:
            user_id = session['user_name']
            user = User.query.filter_by(user_name=user_id).one_or_none()
            if user:
                # This worked!
                # return route_function(user, *args, **kwgs)
                return route_function(*args, **kwgs)

            else:
                return redirect(url_for('routes.login'))

        return redirect(url_for('routes.login'))

    return decorated_function


@bp.route('/portfolio/', methods=('GET', 'POST'))
@login_required
def portfolio():
    url = '/dash/portfolio'
    print("This is portfolio:  "+session.get('user_name', None))
    return render_template('dash_iframe.html', url=url)


@bp.route("/", methods=('GET', 'POST'))
@login_required
def home():
    url = '/dash/home'
    print("This is home:  "+session.get('user_name', None))
    return render_template('dash_iframe.html', url=url)










