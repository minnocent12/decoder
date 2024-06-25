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

from app import app, db, DecryptedMessage  # Adjust 'app' import as per your file structure

# Create an application context before working with the database
with app.app_context():
    # Create a new instance of DecryptedMessage
    new_decrypted_message = DecryptedMessage(
        user_id=2,
        cipher_key='my_cipher_key',
        encrypted_message='This is an encrypted message.',
        date_time=datetime.utcnow()
    )

    # Add the new_decrypted_message to the session and commit
    db.session.add(new_decrypted_message)
    db.session.commit()
