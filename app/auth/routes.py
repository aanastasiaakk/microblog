from flask import render_template, redirect, url_for, flash, request
from urllib.parse import urlsplit
from flask_login import login_user, logout_user, current_user
from flask_babel import _
import sqlalchemy as sa
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, \
    ResetPasswordRequestForm, ResetPasswordForm
from app.models import User
from app.auth.email import send_password_reset_email

# РЕФАКТОРИНГ (Завд.4): винесення дубльованих рядкових літералів
# ('main.index' зустрічався 7 разів, 'auth.login' — 4 рази) в константи
# (Extract Constant) — усуває Code Smell "Define a constant instead of
# duplicating this literal" і робить зміну маршруту централізованою.
MAIN_INDEX_ENDPOINT = 'main.index'
AUTH_LOGIN_ENDPOINT = 'auth.login'


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(MAIN_INDEX_ENDPOINT))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash(_('Invalid username or password'))
            return redirect(url_for(AUTH_LOGIN_ENDPOINT))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for(MAIN_INDEX_ENDPOINT)
        return redirect(next_page)
    return render_template('auth/login.html', title=_('Sign In'), form=form)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for(MAIN_INDEX_ENDPOINT))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for(MAIN_INDEX_ENDPOINT))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_('Congratulations, you are now a registered user!'))
        return redirect(url_for(AUTH_LOGIN_ENDPOINT))
    return render_template('auth/register.html', title=_('Register'),
                           form=form)


@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for(MAIN_INDEX_ENDPOINT))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.email == form.email.data))
        if user:
            send_password_reset_email(user)
        flash(
            _('Check your email for the instructions to reset your password'))
        return redirect(url_for(AUTH_LOGIN_ENDPOINT))
    return render_template('auth/reset_password_request.html',
                           title=_('Reset Password'), form=form)


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for(MAIN_INDEX_ENDPOINT))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for(MAIN_INDEX_ENDPOINT))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(_('Your password has been reset.'))
        return redirect(url_for(AUTH_LOGIN_ENDPOINT))
    return render_template('auth/reset_password.html', form=form)
