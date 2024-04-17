from flask import Flask, render_template, redirect, abort, request, send_file, url_for
from flask_wtf import FlaskForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_restful import Api
from flask_mail import Mail, Message
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FileField
from wtforms.validators import DataRequired
from email_validator import validate_email
from sql import User, global_init, create_session, datetime, Upload
from sql import sql_search, sql_formate, get_api_key, Upload_DB, generate_key
from api import UsersResource, UsersListResource, DbLinksResourse, DbLinksResourseList, DB_list
from hashlib import sha256
from io import BytesIO
import sqlalchemy
import os

HOST = 'http://127.0.0.1:5000'

app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = '8ca0713fc532cb0d5cbd072eaf4d4c14'

app.config['MAIL_SERVER'] = 'smtp.yandex.ru'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'tamasav@yandex.ru'
app.config['MAIL_PASSWORD'] = '290923vbn'

app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.db']

global_init('delta-users.db')

login_manager = LoginManager()
login_manager.init_app(app)

key, c = True, generate_key(40)



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
    i_agree = BooleanField('I agree with', validators=[DataRequired()])
    remember_me = BooleanField('remember me')
    submit = SubmitField('Register')


class SearchForm(FlaskForm):
    data = StringField('', validators=[DataRequired()])
    submit = SubmitField('Search')


class EditForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    email = StringField('email', validators=[DataRequired()])
    submit = SubmitField('Edit')

class DevUploadForm(FlaskForm):
    file = FileField('File', validators=[DataRequired()]) 
    submit = SubmitField('Sent')


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
                                   message=f'Search completed successfully time: {time}', title='Search')
        else:
            return render_template('search.html',
                                   form=form,
                                   data=None,
                                   message='To search sign in to system', title='Search')
    return render_template('search.html', form=form, data=None, title='Search')


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
    global key
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
                key = False
                return redirect(f'/check/{user.email}')
            else:
                return render_template('registration.html', title='Registration', message='Passwords mismatch', form=form)
        except sqlalchemy.exc.IntegrityError:
            return render_template('registration.html', title='Registration', message='a user with this email exists', form=form)
        except ValueError as error:
            return render_template('registration.html', title='Registration', message=error.__class__.__name__, form=form)
    return render_template('registration.html', form=form, title='Registration')


@app.route('/check/<email>', methods=['GET', 'POST'])
def check(email):
    global c
    if not key:
        mail = Mail(app)
        msg = Message('Hi', sender='tamasav@yandex.ru', recipients=[email])
        msg.body = f"To confirm your email, follow the link: \n{HOST}{url_for('secure', k=c)}"
        mail.send(msg)
        return 'A confirmation email has been sent to the email address you specified'
    return redirect('/search')


@app.route('/secure/<k>')
def secure(k):
    global key
    key = True
    return 'The mail has been confirmed, go back to the site: <a href="/search">click</a>'


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
                    return render_template('account.html', form=form, title='Account', data=data, message=f'information updated successfully')
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
    if current_user.access_level.level in ['developer', 'admin']:
        return redirect('/upload_dev')
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

@app.route('/upload_dev', methods=['GET', 'POST'])
def upload_dev():
    if current_user.access_level.level not in ['developer', 'admin']:
        abort(403)
    form = DevUploadForm()
    if form.validate_on_submit():
        uploaded_file = request.files['file']
        file_ext = os.path.splitext(uploaded_file.filename)[1]
        if uploaded_file.filename != '' and file_ext in app.config['UPLOAD_EXTENSIONS']:
            db_sess = create_session()
            file_content = uploaded_file.read()
            upload = Upload(filename=uploaded_file.filename, data=file_content)
            db_sess.add(upload)
            db_sess.commit()
            return render_template('developer_upload.html', form=form, message=f'Uploaded: {uploaded_file.filename}')
        else:
            return render_template('developer_upload.html', form=form, message='File type error')
    return render_template('developer_upload.html', form=form)

@app.route('/download/<upload_id>')
def download(upload_id):
    if current_user.access_level.level != 'developer':
        abort(403)
    db_sess = create_session()
    upload = db_sess.query(Upload).filter(Upload.id == upload_id).first()
    return send_file(BytesIO(upload.data), 
                     download_name=upload.filename, as_attachment=True)


@app.route('/')
def general():
    return render_template('general.html', title='General')

@app.route('/rules')
def rules():
    return render_template('rules.html', title='Rules')


api.add_resource(UsersListResource, '/api/v2/users')
api.add_resource(UsersResource, '/api/v2/users/<int:user_id>')

api.add_resource(DbLinksResourseList, '/api/v2/links')
api.add_resource(DbLinksResourse, '/api/v2/links/<int:link_id>')

api.add_resource(DB_list, '/api/v2/databases')

if __name__ == '__main__':
    app.run(port=5000, host='0.0.0.0', debug=True)
