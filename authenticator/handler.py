import json
import pyotp
from datetime import datetime, timedelta
import pymysql
import mysql.connector
import base64


def handle(event, context):

    # try:
        username = event.query['username']
        password = event.query['password']
        mfa = event.query['otp_code']

        if not all([username, password, mfa]):
            return {
                "statusCode": 400,
                "body": "user_id, password, and mfa are required",
                "headers": {
                    "Content-type": "text/plain",
                    "Access-Control-Allow-Origin": "http://127.0.0.1:8000"
                }
            }
        user = get_user(username)
        
        if not user:
            return {
                "statusCode": 404,
                "body": "User not found",
                "headers": {
                    "Content-type": "text/plain",
                    "Access-Control-Allow-Origin": "http://127.0.0.1:8000"
                }
            } 

        # Check expiry (6 months)
        if datetime.utcnow() - user['gendate'] > timedelta(days=180):
            update_expired_user(user['username'])
            return {
                "statusCode": 403,
                "body": "password or mfa expired",
                "headers": {
                    "Content-type": "text/plain",
                    "Access-Control-Allow-Origin": "http://127.0.0.1:8000"
                }
            }

        # Decrypt and check password

        stored_password = decrypt_password(user['password'])
        stored_password_user = decrypt_password(password)

        if stored_password != stored_password_user:
            return {
                "statusCode": 401,
                "body": password,
                "headers": {
                    "Content-type": "text/plain",
                    "Access-Control-Allow-Origin": "http://127.0.0.1:8000"
                }
            }

        stored_password_2fa = decrypt_password(user['mfa'])
        # Check TOTP

        totp = pyotp.TOTP(stored_password_2fa)
        verify = totp.verify(mfa)
        if not verify:
            return {
                "statusCode": 401,
                "body": {"verify": verify},
                "headers": {
                    "Content-type": "text/plain",
                    "Access-Control-Allow-Origin": "http://127.0.0.1:8000"
                }
            }

        return {
                "statusCode": 200,
                "body": "Authentication successful",
                "headers": {
                    "Content-type": "text/plain",
                    "Access-Control-Allow-Origin": "http://127.0.0.1:8000"
                }
            }

    # except Exception as e:
    #     return {
    #         "statusCode": 500,
    #         "body": "Erreur",
    #         "headers": {
    #             "Content-type": "text/plain",
    #             "Access-Control-Allow-Origin": "http://127.0.0.1:8000"
    #         }
    #     }

def get_secret(key):
    with open("/var/openfaas/secrets/{}".format(key)) as f:
        return f.read().strip()

def get_conn() -> pymysql.connections.Connection:
    mdp = get_secret("password")
    return mysql.connector.connect(
        host="mysql.openfaas-fn.svc.cluster.local",
        user="root",
        password=mdp,
        database="cloud-connect"
    )

def get_user(username) -> dict | None:
    connection = get_conn()
    with connection:
        with connection.cursor(dictionary=True) as cursor:
            sql = "SELECT * FROM users WHERE username = %s"
            cursor.execute(sql, (username,))
            user = cursor.fetchone()
            return user

def decrypt_password(password):
    decoded_bytes = base64.b64decode(password)
    decoded_str = decoded_bytes.decode("utf-8")
    return decoded_str

def update_expired_user(username):
    connection = get_conn()
    with connection:
        with connection.cursor() as cursor:
            sql = "UPDATE users SET expired = 1 WHERE username = %s"
            cursor.execute(sql, (username,))
            connection.commit()
