from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import random
import hashlib
import os
import jwt
from models import db, User, EncryptedMessage, DecryptedMessage  # Import models from models.py

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
    error_message = None  # Set default error message to None
    return render_template('index.html', error_message=error_message)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(username=username).first()
    if user and verify_password(user.password, password):
        session['username'] = username
        session['user_id'] = user.id  # Store user_id in session
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
    if user:
        user_initials = f"{user.firstname[0]}{user.lastname[0]}".upper()
        user_full_name = f"{user.firstname} {user.lastname}"
        user_first_name = user.firstname
        return render_template('main.html', user_initials=user_initials, user_full_name=user_full_name, user_first_name=user_first_name)
    else:
        return redirect(url_for('index'))  # Redirect to login if user is not found


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
    user_id = session.get('user_id')
    cipher_key = request.args.get('cipherKey')

    if not user_id:
        return jsonify({'status': 'error', 'message': 'User not logged in.'}), 401

    if not cipher_key:
        return jsonify({'message': 'Cipher key is required'}), 400

    encrypted_message = EncryptedMessage.query.filter_by(cipher_key=cipher_key).first()
    if encrypted_message:
        return jsonify({'message': encrypted_message.encrypted_message}), 200
    
    decrypted_message = DecryptedMessage(user_id=user_id, cipher_key=cipher_key, encrypted_message=encrypted_message,date_time=datetime.utcnow())
    try:
        db.session.add(decrypted_message)
        db.session.commit()
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
    


@app.route('/send')
def send_page():
    username = session.get('username', '')
    user_id = session.get('user_id')  # Retrieve user_id from session
    if not username or not user_id:
        return redirect(url_for('index'))  # Redirect to login if user is not logged in

    user = User.query.filter_by(username=username).first()
    if user:
        user_initials = f"{user.firstname[0]}{user.lastname[0]}".upper()
        user_full_name = f"{user.firstname} {user.lastname}"
        user_first_name = user.firstname
        cipher_keys = EncryptedMessage.query.filter_by(user_id=user_id).all()  # Filter by user_id
        return render_template('send.html', user_initials=user_initials, user_full_name=user_full_name, user_first_name=user_first_name, cipher_keys=cipher_keys)
    else:
        return redirect(url_for('index'))  # Redirect to login if user is not found

@app.route('/received')
def received_page():
    username = session.get('username', '')
    user_id = session.get('user_id')  # Retrieve user_id from session
    if not username or not user_id:
        return redirect(url_for('index'))  # Redirect to login if user is not logged in

    user = User.query.filter_by(username=username).first()
    if user:
        user_initials = f"{user.firstname[0]}{user.lastname[0]}".upper()
        user_full_name = f"{user.firstname} {user.lastname}"
        user_first_name = user.firstname
        cipher_keys = DecryptedMessage.query.filter_by(user_id=user_id).all()  # Filter by user_id
        return render_template('received.html', user_initials=user_initials, user_full_name=user_full_name, user_first_name=user_first_name, cipher_keys=cipher_keys)
    else:
        return redirect(url_for('index'))  # Redirect to login if user is not found


@app.route('/delete-cipher-key/<int:cipher_id>', methods=['DELETE'])
def delete_cipher_key(cipher_id):
    user_id = session.get('user_id')
    cipher = EncryptedMessage.query.filter_by(id=cipher_id, user_id=user_id).first()
    if cipher:
        try:
            db.session.delete(cipher)
            db.session.commit()
            return jsonify({'status': 'success'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500
    else:
        return jsonify({'status': 'error', 'message': 'Cipher key not found or unauthorized.'}), 404

if __name__ == '__main__':
    app.run(debug=True)
