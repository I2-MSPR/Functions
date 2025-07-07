import json
import os
import pyotp
from flask import jsonify
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, Column, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

# DB config
DB_URL = "mysql+pymysql://root:admin123@mysql-service.default.svc.cluster.local:3306/mydb"

engine = create_engine(DB_URL)
Base = declarative_base()

class UserCredential(Base):
    __tablename__ = 'user_credentials'
    user_id = Column(String, primary_key=True)
    encrypted_password = Column(String, nullable=False)
    twofa_secret = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expired = Column(Boolean, default=False)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Key (⚠️ should be same as other functions — use env var in production)
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY").encode()
cipher = Fernet(ENCRYPTION_KEY)

def handle(req):
    try:
        session = None 
        data = json.loads(req)
        user_id = data.get("user_id")
        password = data.get("password")
        otp_code = data.get("otp_code")

        if not all([user_id, password, otp_code]):
            return jsonify({"error": "user_id, password, and otp_code are required"}), 400

        session = Session()
        user = session.query(UserCredential).filter_by(user_id=user_id).first()

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Check expiry (6 months)
        if datetime.utcnow() - user.created_at > timedelta(days=180):
            user.expired = True
            session.commit()
            return jsonify({"error": "Account expired. Please regenerate credentials."}), 403

        if user.expired:
            return jsonify({"error": "Account already expired."}), 403

        # Decrypt and check password
        try:
            stored_password = cipher.decrypt(user.encrypted_password.encode()).decode()
        except Exception:
            return jsonify({"error": "Failed to decrypt password"}), 500

        if stored_password != password:
            return jsonify({"error": "Invalid password"}), 401

        # Check TOTP
        if not user.twofa_secret:
            return jsonify({"error": "No 2FA secret found"}), 400

        try:
            secret = cipher.decrypt(user.twofa_secret.encode()).decode()
        except Exception:
            return jsonify({"error": "Failed to decrypt 2FA secret"}), 500

        totp = pyotp.TOTP(secret)
        if not totp.verify(otp_code):
            return jsonify({"error": "Invalid 2FA code"}), 401

        return jsonify({"message": "Authentication successful"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if session:
            session.close()