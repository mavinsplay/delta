from flask import Flask, render_template, url_for, redirect, abort, request
from flask_wtf import FlaskForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_restful import Api
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from sql import User, global_init, create_session, datetime, sql_search, sql_formate, get_api_key, Upload_DB
from api import UsersResource, UsersListResource, DbLinksResourse, DbLinksResourseList
from email_validator import validate_email
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


class SearchForm(FlaskForm):
    data = StringField('', validators=[DataRequired()])
    submit = SubmitField('Search')


class EditForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    email = StringField('email', validators=[DataRequired()])
    submit = SubmitField('Edit')


class UploadForm(FlaskForm):
    database_name = StringField('Database name', validators=[DataRequired()])
    sourse_link = StringField('Sourse of leak (link)',
                              validators=[DataRequired()])
    db_link = StringField(
        'Database link (any cloud storage)', validators=[DataRequired()])
    i_agree = BooleanField('I agree with rules', validators=[DataRequired()])
    submit = SubmitField('Sent')


@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    if form.validate_on_submit():
        if current_user.is_authenticated:
            data, time = sql_search(form.data.data)
            return render_template('search.html', form=form,
                                   data=sql_formate(data),
                                   message=f'Search completed successfully time: {time}', )
        else:
            return render_template('search.html',
                                   form=form,
                                   data=None,
                                   message='To search sign in to system')
    return render_template('search.html', form=form, data=None)


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
                valid_email = validate_email(form.email.data)
                user.email = valid_email.original
                user.hashed_password = sha256(
                    form.password.data.encode('utf-8')).hexdigest()
                user.modified_date = datetime.datetime.now()
                db_sess.add(user)
                db_sess.commit()
                login_user(user, remember=form.remember_me.data)
                return redirect('/search')
            else:
                return render_template('registration.html', title='Registration', message='Passwords mismatch', form=form)
        except sqlalchemy.exc.IntegrityError:
            return render_template('registration.html', title='Registration', message='a user with this email exists', form=form)
        except ValueError as error:
            return render_template('registration.html', title='Registration', message=error.__class__.__name__, form=form)
    return render_template('registration.html', form=form, title='Registration')


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = EditForm()
    data = {}
    if request.method == 'GET':
        db_sess = create_session()
        user = db_sess.query(User).filter(
            User.email == current_user.email).first()
        if user:
            form.username.data = user.username
            form.email.data = user.email
            api_key = get_api_key(user)
            data = {
                'modified_date': user.modified_date,
                'access_level': user.access_level.level,
                'api_key': api_key
            }

        else:
            abort(404)

    if form.validate_on_submit():
        db_sess = create_session()
        user = db_sess.query(User).filter(
            User.email == current_user.email).first()
        if user:
            api_key = get_api_key(user)
            data = {
                'modified_date': user.modified_date,
                'access_level': user.access_level.level,
                'api_key': api_key
            }
            time_difference = datetime.datetime.now() - data['modified_date']
            if time_difference.total_seconds() > 3600:
                try:
                    user.username = form.username.data
                    valid_email = validate_email(form.email.data)
                    user.email = valid_email.original
                    user.modified_date = datetime.datetime.now()
                    db_sess.merge(user)
                    db_sess.commit()
                    data['modified_date'] = user.modified_date
                    data['access_level'] = user.access_level.level
                    data['api_key'] = get_api_key(user)
                    return render_template('account.html', form=form, title='Account', data=data, message='Pass, information updated successfully')
                except sqlalchemy.exc.IntegrityError:
                    return render_template('account.html', form=form, title='Account', data=data, message='A user with this email exists')
                except ValueError as error:
                    return render_template('account.html', form=form, title='Account', data=data, message=error.__class__.__name__)
            else:
                return render_template('account.html', form=form, title='Account', data=data, message='You can only update your account once per hour')
        else:
            abort(404)
    return render_template('account.html', form=form, title='Account', data=data)


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        db_sess = create_session()
        link = Upload_DB()
        link.user_id = current_user.id
        link.database_name = form.database_name.data
        link.sourse_link = form.sourse_link.data
        link.db_link = form.db_link.data
        db_sess.add(link)
        db_sess.commit()
        return render_template('upload.html',
                               message='Succefully, DB submitted for moderation', title='Upload DB',
                               form=form)
    return render_template('upload.html', form=form, title='Upload DB')


@app.route('/')
def general():
    return render_template('general.html', title='General')


api.add_resource(UsersListResource, '/api/v2/users')
api.add_resource(UsersResource, '/api/v2/users/<int:user_id>')

api.add_resource(DbLinksResourseList, '/api/v2/links')
api.add_resource(DbLinksResourse, '/api/v2/links/<int:link_id>')

if __name__ == '__main__':
    app.run(port=5000, host='0.0.0.0', debug=True)
