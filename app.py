from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import random
import hashlib
import os
import jwt
from models import db, User, EncryptedMessage  # Import models from models.py

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

db.init_app(app)  # Initialize db with app
mail = Mail(app)

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
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(username=username).first()
    if user and verify_password(user.password, password):
        session['user_id'] = user.id  # Store user ID in session
        session['username'] = user.username
        flash('You have successfully logged in.', 'success')
        return redirect(url_for('main'))
    else:
        flash('Invalid username or password. Please try again.', 'danger')
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    flash('You have successfully logged out.', 'success')
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
        flash('Email already registered.', 'danger')
        return redirect(url_for('signup'))

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

    flash('Registration successful. Please log in.', 'success')
    return redirect(url_for('index'))

@app.route('/main')
def main():
    username = session.get('username')
    if not username:
        return redirect(url_for('index'))  # Redirect to login if user is not logged in

    user = User.query.filter_by(username=username).first()
    if user:
        user_initials = f"{user.firstname[0]}{user.lastname[0]}".upper()
        user_full_name = f"{user.firstname} {user.lastname}"
        user_first_name = user.firstname
        return render_template('main.html', user_initials=user_initials, user_full_name=user_full_name, user_first_name=user_first_name)
    else:
        flash('User not found.', 'danger')
        return redirect(url_for('index'))  # Redirect to login if user is not found

@app.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html')

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
        flash('Password reset link has been sent to your email.', 'info')
        return redirect(url_for('index'))
    else:
        flash('The email address or username you entered does not match any account.', 'danger')
        return redirect(url_for('forgot_password'))

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
        msg.body = f'Hi {user.firstname},\n\nYour password has been successfully reset. Your username is: {user.username}\nYour new password is: {new_password}\n\nIf you did not request this change, please contact us immediately.'
        mail.send(msg)
        session['reset_email'] = user.email  # Store the email in the session
        session['username'] = user.username  # Store the username in the session
        flash('Your password has been reset successfully.', 'success')
        return redirect(url_for('index'))

    return render_template('reset_password.html', token=token)

@app.route('/store-encrypted-message', methods=['POST'])
def store_encrypted_message():
    data = request.json
    user_id = session.get('user_id')
    message = data.get('message')
    cipher_key = data.get('cipherKey')

    if not user_id:
        return jsonify({'status': 'error', 'message': 'User not logged in.'}), 401

    if not message or not cipher_key:
        return jsonify({'status': 'error', 'message': 'Invalid input data.'}), 400

    encrypted_message = EncryptedMessage(user_id=user_id, cipher_key=cipher_key, encrypted_message=message)
    try:
        db.session.add(encrypted_message)
        db.session.commit()
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/decrypt-message', methods=['GET'])
def decrypt_message():
    cipher_key = request.args.get('cipherKey')
    if not cipher_key:
        return jsonify({'message': 'Cipher key is required'}), 400

    encrypted_message = EncryptedMessage.query.filter_by(cipher_key=cipher_key).first()
    if encrypted_message:
        return jsonify({'message': encrypted_message.encrypted_message}), 200
    else:
        return jsonify({'message': 'Invalid cipher key'}), 404

if __name__ == '__main__':
    app.run(debug=True)