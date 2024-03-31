from flask import Flask, render_template, url_for, redirect
from flask_wtf import FlaskForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_restful import Api
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from sql import User, global_init, create_session, datetime
from api import UsersResource, UsersListResource
from hashlib import sha256
import sqlalchemy

app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = '8ca0713fc532cb0d5cbd072eaf4d4c14'

global_init('delta-users.db')

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = create_session()
    return db_sess.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')


class LoginForm(FlaskForm):
    email = StringField('email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    remember_me = BooleanField('remember me')
    submit = SubmitField('Login')


class RegistrationForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    email = StringField('email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    repeat_password = PasswordField(
        'repeat password', validators=[DataRequired()])
    i_agree = BooleanField('I agree with rules', validators=[DataRequired()])
    remember_me = BooleanField('remember me')
    submit = SubmitField('Register')


@app.route('/search')
def search():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = create_session()
        user = db_sess.query(User).filter(
            User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(f'/search')
        return render_template('login.html',
                               message='Wrong Email or password', title='login',
                               form=form)
    return render_template('login.html', form=form)


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            if form.password.data == form.repeat_password.data:
                db_sess = create_session()
                user = User()
                user.username = form.username.data
                user.email = form.email.data
                user.hashed_password = sha256(form.password.data.encode('utf-8')).hexdigest()
                user.modified_date = datetime.datetime.now()
                db_sess.add(user)
                db_sess.commit()
                login_user(user, remember=form.remember_me.data)
                return redirect('/search')
            else:
                return render_template('registration.html', title='Register', message='Passwords mismatch', form=form)
        except sqlalchemy.exc.IntegrityError:
            return render_template('registration.html', title='Register', message='a user with this email exists', form=form)
    return render_template('registration.html', form=form, title='Register')


@app.route('/account')
def account():
    return render_template('login.html')


api.add_resource(UsersListResource, '/api/v2/users')
api.add_resource(UsersResource, '/api/v2/users/<int:user_id>')


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
