import sqlite3
import hashlib
import bcrypt
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float, Boolean, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import secrets
import os
import base64
from cryptography.fernet import Fernet
from config import DATABASE_CONFIG, EMAIL_CONFIG
from email_service import EmailService
import json

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(LargeBinary, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    reset_token = Column(String(100))
    reset_token_expires = Column(DateTime)
    login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)

class PredictionHistory(Base):
    __tablename__ = 'prediction_history'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    image_name = Column(Text)  # Encrypted
    predicted_disease = Column(Text)  # Encrypted
    confidence_score = Column(Float)
    accuracy_level = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)
    image_path = Column(Text)  # Encrypted
    notes = Column(Text)  # Encrypted
    session_id = Column(String(100))

class UserSession(Base):
    __tablename__ = 'user_sessions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    session_token = Column(String(255), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    ip_address = Column(String(45))
    user_agent = Column(Text)

class DatabaseManager:
    def __init__(self, db_path=None):
        try:
            if db_path is None:
                db_path = DATABASE_CONFIG['db_path']

            # Initialize encryption
            self.encryption_key = DATABASE_CONFIG['encryption_key'].encode()
            if len(self.encryption_key) != 32:
                # Generate a proper 32-byte key
                self.encryption_key = hashlib.sha256(self.encryption_key).digest()
            # Create Fernet key from the encryption key
            fernet_key = base64.urlsafe_b64encode(self.encryption_key)
            self.cipher = Fernet(fernet_key)

            # Create database directory
            db_dir = os.path.dirname(os.path.abspath(db_path))
            if not os.path.exists(db_dir):
                os.makedirs(db_dir)

            # Create engine
            self.engine = create_engine(
                f'sqlite:///{db_path}',
                echo=False,
                pool_pre_ping=True,
                connect_args={'check_same_thread': False}
            )

            # Create tables
            Base.metadata.create_all(self.engine)

            # Create session
            Session = sessionmaker(bind=self.engine)
            self.session = Session()

            # Initialize email service
            self.email_service = EmailService()

        except Exception as e:
            print(f"Database initialization error: {str(e)}")
            raise e

    def encrypt_data(self, data):
        """Encrypt sensitive data"""
        if data is None:
            return None
        return self.cipher.encrypt(str(data).encode()).decode()

    def decrypt_data(self, encrypted_data):
        """Decrypt sensitive data"""
        if encrypted_data is None:
            return None
        try:
            return self.cipher.decrypt(encrypted_data.encode()).decode()
        except:
            # If decryption fails, try to detect if it's an old encrypted format
            # or return a user-friendly placeholder
            if encrypted_data.startswith('gAAAAA'):  # Fernet encrypted data
                return "[Encrypted Data - Please re-run analysis]"
            return encrypted_data  # Return as-is if decryption fails

    def hash_password(self, password):
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt)

    def verify_password(self, password, hashed):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed)

    def is_account_locked(self, user):
        """Check if account is locked due to failed attempts"""
        if user.locked_until and user.locked_until > datetime.utcnow():
            return True, user.locked_until
        return False, None

    def lock_account(self, user):
        """Lock account for 30 minutes after 5 failed attempts"""
        user.login_attempts += 1
        if user.login_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        self.session.commit()

    def reset_login_attempts(self, user):
        """Reset login attempts after successful login"""
        user.login_attempts = 0
        user.locked_until = None
        self.session.commit()

    def create_user(self, username, email, password):
        """Create new user with welcome email"""
        try:
            # Check if username or email exists
            existing_user = self.session.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()

            if existing_user:
                if existing_user.username == username:
                    return False, "Username already exists"
                else:
                    return False, "Email already registered"

            # Create user
            hashed_password = self.hash_password(password)
            new_user = User(
                username=username,
                email=email,
                password_hash=hashed_password
            )

            self.session.add(new_user)
            self.session.commit()

            # Send welcome email
            try:
                self.email_service.send_welcome_email(email, username)
            except Exception as e:
                print(f"Welcome email failed: {str(e)}")

            return True, "Account created successfully!"

        except Exception as e:
            self.session.rollback()
            return False, f"Error creating account: {str(e)}"

    def authenticate_user(self, username_or_email, password):
        """Authenticate user login"""
        try:
            user = self.session.query(User).filter(
                (User.username == username_or_email) | (User.email == username_or_email)
            ).first()

            if not user:
                return False, None, "Invalid username or email"

            if not user.is_active:
                return False, None, "Account is deactivated"

            # Check if account is locked
            locked, unlock_time = self.is_account_locked(user)
            if locked:
                return False, None, f"Account locked until {unlock_time.strftime('%H:%M')}"

            # Verify password
            if not self.verify_password(password, user.password_hash):
                self.lock_account(user)
                return False, None, "Invalid password"

            # Reset login attempts on successful login
            self.reset_login_attempts(user)

            # Update last login
            user.last_login = datetime.utcnow()
            self.session.commit()

            return True, user, "Login successful"

        except Exception as e:
            return False, None, f"Login error: {str(e)}"

    def get_user_by_id(self, user_id):
        """Get user by ID"""
        try:
            return self.session.query(User).filter_by(id=user_id).first()
        except Exception as e:
            print(f"Get user error: {str(e)}")
            return None

    def update_user_profile(self, user_id, username=None, email=None):
        """Update user profile"""
        try:
            user = self.session.query(User).filter_by(id=user_id).first()
            if not user:
                return False, "User not found"

            # Check if new username/email is available
            if username and username != user.username:
                existing = self.session.query(User).filter_by(username=username).first()
                if existing:
                    return False, "Username already taken"
                user.username = username

            if email and email != user.email:
                existing = self.session.query(User).filter_by(email=email).first()
                if existing:
                    return False, "Email already registered"
                user.email = email

            self.session.commit()
            return True, "Profile updated successfully"

        except Exception as e:
            self.session.rollback()
            return False, f"Update error: {str(e)}"

    def change_password(self, user_id, current_password, new_password):
        """Change user password"""
        try:
            user = self.session.query(User).filter_by(id=user_id).first()
            if not user:
                return False, "User not found"

            # Verify current password
            if not self.verify_password(current_password, user.password_hash):
                return False, "Current password is incorrect"

            # Update password
            user.password_hash = self.hash_password(new_password)
            self.session.commit()

            return True, "Password changed successfully"

        except Exception as e:
            self.session.rollback()
            return False, f"Password change error: {str(e)}"

    def initiate_password_reset(self, email):
        """Initiate password reset"""
        try:
            user = self.session.query(User).filter_by(email=email).first()
            if not user:
                return False, "Email not found"

            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            user.reset_token = reset_token
            user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)

            self.session.commit()

            # Send reset email
            try:
                self.email_service.send_password_reset_email(email, reset_token)
                return True, "Password reset email sent"
            except Exception as e:
                return False, f"Failed to send email: {str(e)}"

        except Exception as e:
            self.session.rollback()
            return False, f"Reset error: {str(e)}"

    def reset_password(self, token, new_password):
        """Reset password using token"""
        try:
            user = self.session.query(User).filter_by(reset_token=token).first()
            if not user:
                return False, "Invalid reset token"

            if user.reset_token_expires < datetime.utcnow():
                return False, "Reset token has expired"

            # Update password and clear reset token
            user.password_hash = self.hash_password(new_password)
            user.reset_token = None
            user.reset_token_expires = None

            self.session.commit()

            return True, "Password reset successfully"

        except Exception as e:
            self.session.rollback()
            return False, f"Reset error: {str(e)}"

    def save_prediction(self, user_id, image_name, predicted_disease, confidence, image_path, notes=""):
        """Save encrypted prediction to history"""
        try:
            # Determine accuracy level
            if confidence >= 0.95:
                accuracy_level = "Excellent"
            elif confidence >= 0.85:
                accuracy_level = "Very Good"
            elif confidence >= 0.75:
                accuracy_level = "Good"
            elif confidence >= 0.65:
                accuracy_level = "Fair"
            else:
                accuracy_level = "Poor"

            # Create prediction with encryption
            prediction = PredictionHistory(
                user_id=user_id,
                image_name=self.encrypt_data(image_name),
                predicted_disease=self.encrypt_data(predicted_disease),
                confidence_score=confidence,
                accuracy_level=accuracy_level,
                image_path=self.encrypt_data(image_path),
                notes=self.encrypt_data(notes),
                session_id=secrets.token_urlsafe(16)
            )
            self.session.add(prediction)
            self.session.commit()
            return True
        except Exception as e:
            print(f"Save prediction error: {str(e)}")
            self.session.rollback()
            return False

    def get_user_history(self, user_id, limit=50):
        """Get user's prediction history with decryption"""
        try:
            history = self.session.query(PredictionHistory).filter_by(
                user_id=user_id
            ).order_by(PredictionHistory.timestamp.desc()).limit(limit).all()

            # Decrypt data
            for record in history:
                record.image_name = self.decrypt_data(record.image_name)
                record.predicted_disease = self.decrypt_data(record.predicted_disease)
                record.image_path = self.decrypt_data(record.image_path)
                record.notes = self.decrypt_data(record.notes)

            return history
        except Exception as e:
            print(f"Get history error: {str(e)}")
            return []

    def get_user_statistics(self, user_id):
        """Get comprehensive user statistics"""
        try:
            history = self.get_user_history(user_id)

            if not history:
                return {
                    'total_scans': 0,
                    'healthy_plants': 0,
                    'diseases_detected': 0,
                    'avg_confidence': 0,
                    'high_confidence_predictions': 0,
                    'accuracy_distribution': {},
                    'recent_activity': 0,
                    'favorite_plants': []
                }

            total_scans = len(history)
            # Only count non-encrypted predictions for healthy/disease stats
            valid_predictions = [h for h in history if h.predicted_disease != "[Encrypted Data - Please re-run analysis]"]
            healthy_count = sum(1 for h in valid_predictions if 'healthy' in h.predicted_disease.lower())
            disease_count = len(valid_predictions) - healthy_count
            avg_confidence = sum(h.confidence_score for h in history) / total_scans if total_scans > 0 else 0
            high_confidence = sum(1 for h in history if h.confidence_score >= 0.8)

            # Accuracy distribution
            accuracy_dist = {}
            for h in history:
                level = h.accuracy_level
                accuracy_dist[level] = accuracy_dist.get(level, 0) + 1

            # Recent activity (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_activity = sum(1 for h in history if h.timestamp >= week_ago)

            # Plant analysis (exclude encrypted data)
            plant_counts = {}
            for h in valid_predictions:
                plant = h.predicted_disease.split('___')[0] if '___' in h.predicted_disease else 'Unknown'
                plant_counts[plant] = plant_counts.get(plant, 0) + 1

            favorite_plants = sorted(plant_counts.items(), key=lambda x: x[1], reverse=True)[:3]

            return {
                'total_scans': total_scans,
                'healthy_plants': healthy_count,
                'diseases_detected': disease_count,
                'avg_confidence': avg_confidence,
                'high_confidence_predictions': high_confidence,
                'accuracy_distribution': accuracy_dist,
                'recent_activity': recent_activity,
                'favorite_plants': favorite_plants
            }

        except Exception as e:
            print(f"Statistics error: {str(e)}")
            return {
                'total_scans': 0,
                'healthy_plants': 0,
                'diseases_detected': 0,
                'avg_confidence': 0,
                'high_confidence_predictions': 0,
                'accuracy_distribution': {},
                'recent_activity': 0,
                'favorite_plants': []
            }

    def create_session(self, user_id, ip_address=None, user_agent=None):
        """Create user session"""
        try:
            # Clean up expired sessions
            self.session.query(UserSession).filter(
                UserSession.expires_at < datetime.utcnow()
            ).delete()

            # Create new session
            session_token = secrets.token_urlsafe(64)
            expires_at = datetime.utcnow() + timedelta(days=7)  # 7 days

            session = UserSession(
                user_id=user_id,
                session_token=session_token,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent
            )

            self.session.add(session)
            self.session.commit()

            return session_token

        except Exception as e:
            self.session.rollback()
            return None

    def validate_session(self, session_token):
        """Validate session token"""
        try:
            session = self.session.query(UserSession).filter_by(
                session_token=session_token
            ).first()

            if not session:
                return False, None

            if session.expires_at < datetime.utcnow():
                self.session.delete(session)
                self.session.commit()
                return False, None

            user = self.get_user_by_id(session.user_id)
            return True, user

        except Exception as e:
            return False, None

    def destroy_session(self, session_token):
        """Destroy user session"""
        try:
            session = self.session.query(UserSession).filter_by(
                session_token=session_token
            ).first()

            if session:
                self.session.delete(session)
                self.session.commit()

            return True

        except Exception as e:
            self.session.rollback()
            return False