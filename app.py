from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import random
import hashlib
import os
import jwt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'minnocent1'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'mirenge.innocent@gmail.com'
app.config['MAIL_PASSWORD'] = 'sziq xztz tqxl zqjy'  # Replace this with the app password
app.config['MAIL_DEFAULT_SENDER'] = 'mirenge.innocent@gmail.com'  # Set the default sender

db = SQLAlchemy(app)
mail = Mail(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    dob = db.Column(db.Date, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

def generate_username(first_name, last_name):
    username = (first_name[:2] + last_name).lower()
    username += str(random.randint(10, 99))
    return username

def hash_password(password):
    salt = os.urandom(16)
    hashed_password = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return salt + hashed_password

def verify_password(stored_password, provided_password):
    salt = stored_password[:16]
    stored_hash = stored_password[16:]
    provided_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), salt, 100000)
    return stored_hash == provided_hash

@app.route('/')
def index():
    error_message = None  # Set default error message to None
    return render_template('index.html', error_message=error_message)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(username=username).first()
    if user and verify_password(user.password, password):
        return redirect(url_for('main'))
    else:
        error_message = "Invalid username or password. Please try again."
        return render_template('index.html', error_message=error_message)
    

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/signup')
def signup():
    error = request.args.get('error')
    return render_template('signup.html', error=error)

@app.route('/register', methods=['POST'])
def register():
    firstname = request.form['firstname']
    lastname = request.form['lastname']
    email = request.form['email']
    dob = datetime.strptime(request.form['dob'], '%Y-%m-%d').date()
    phone = request.form['phone']
    password = request.form['password']

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return redirect(url_for('signup', error="Email already registered"))

    username = generate_username(firstname, lastname)
    while User.query.filter_by(username=username).first():
        username = generate_username(firstname, lastname)

    hashed_password = hash_password(password)
    user = User(firstname=firstname, lastname=lastname, email=email, dob=dob, phone=phone, username=username, password=hashed_password)
    db.session.add(user)
    db.session.commit()

    msg = Message('Welcome to Our Website!', recipients=[email])
    msg.body = f'Your username is: {username}\nYour password is: {password}'
    mail.send(msg)

    return redirect(url_for('success', email=email))

@app.route('/success')
def success():
    email = request.args.get('email')
    return render_template('success.html', email=email)

@app.route('/main')
def main():
    username = session.get('username', '')
    if not username:
        return redirect(url_for('index'))  # Redirect to login if user is not logged in

    user = User.query.filter_by(username=username).first()
    user_initials = user.firstname[0] + user.lastname[0] if user else ''
    user_full_name = f"{user.firstname} {user.lastname}" if user else ''
    
    return render_template('main.html', user_initials=user_initials, user_full_name=user_full_name)

    
    return render_template('main.html',username=username)

@app.route('/forgot_password')
def forgot_password():
    error_message = None  # Set default error message to None
    return render_template('forgot_password.html', error_message=error_message)

@app.route('/reset_password', methods=['POST'])
def reset_password():
    email_or_username = request.form['email']
    user = User.query.filter((User.email == email_or_username) | (User.username == email_or_username)).first()

    if user:
        reset_token = generate_reset_token(user.id)
        reset_url = url_for('reset_with_token', token=reset_token, _external=True)
        msg = Message('Password Reset Request', recipients=[user.email])
        msg.body = f'Hi {user.firstname},\n\nPlease use the following link to reset your password: {reset_url}\n\nIf you did not request this, please ignore this email.'
        mail.send(msg)
        session['reset_email'] = user.email  # Store the email in the session
        return redirect(url_for('reset_link_sent'))
    else:
        error_message = "The email address or username you entered does not match any account."
        return render_template('forgot_password.html', error_message=error_message)

@app.route('/reset_link_sent')
def reset_link_sent():
    email = session.get('reset_email', '')
    return render_template('reset_link_sent.html', email=email)

def generate_reset_token(user_id):
    # Use JWT to generate a token with an expiration time
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token

@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = payload['user_id']
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        flash('The reset link is invalid or has expired.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        new_password = request.form['password']
        user = User.query.get(user_id)
        user.password = hash_password(new_password)
        db.session.commit()
        msg = Message('Password Reset Successful', recipients=[user.email])
        msg.body = f'Hi {user.firstname},\n\nYour password has been successfully reset. Your username is: {user.username}\nYour new password is:{new_password}\n\nIf you did not request this change, please contact us immediately.'
        mail.send(msg)
        session['reset_email'] = user.email  # Store the email in the session
        session['username'] = user.username  # Store the username in the session
        return redirect(url_for('reset_successful'))
    
    return render_template('reset_password.html', token=token)

@app.route('/reset_successful')
def reset_successful():
    email = session.get('reset_email', '')
    username = session.get('username', '')
    return render_template('reset_successful.html', email=email, username=username)

@app.route('/check_email', methods=['POST'])
def check_email():
    email = request.form['email']
    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({'exists': True})
    return jsonify({'exists': False})

if __name__ == '__main__':
    app.run(debug=True)
