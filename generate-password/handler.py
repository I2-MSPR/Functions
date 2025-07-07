import base64
from io import BytesIO
import pymysql
import qrcode
import string
import secrets
import mysql.connector
import json

def handle(event, context):
    username = event.query['username']
    
    try:
        password = generate_password()
        user = get_user(username)
        if user is None:
            create_user(username, password)
        else:
            update_user(username, password)
        
        qrcode = generate_qrcode(password)
        
        return {
            "statusCode": 200,
            "body": { "qrcode": qrcode },
            "headers": {
                "Content-type": "text/plain",
                "Access-Control-Allow-Origin": "http://127.0.0.1:8000"
            }
        } 
    except:
       return {
            "statusCode": 400,
            "body": "error"
        } 

    
def generate_password() -> str :
    uppers = string.ascii_uppercase
    lowers = string.ascii_lowercase
    digits = string.digits
    specialchars = "!@#$%^&*()-_=+[]{}|;:,.<>?/"
    chars = uppers + lowers + digits + specialchars
    
    password = [
        secrets.choice(uppers),
        secrets.choice(lowers),
        secrets.choice(digits),
        secrets.choice(specialchars),
    ]
    password += [secrets.choice(chars) for i in range(20)]
    
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)

def get_conn() -> pymysql.connections.Connection:
    db_password = get_secret("password")
    return mysql.connector.connect(
        host="mysql.openfaas-fn.svc.cluster.local",
        user="root",
        password=db_password,
        database="cloud-connect"
    )

def get_user(username) -> dict | None:
    connection = get_conn()
    with connection:
        with connection.cursor(dictionary=True) as cursor:
            sql = "SELECT password FROM users WHERE username = %s"
            cursor.execute(sql, (username,))
            user = cursor.fetchone()
            return user
    
def create_user(username, password):
    base64_password = base64.b64encode(password.encode('utf-8')).decode('utf-8')
    connection = get_conn()
    with connection:
        with connection.cursor(dictionary=True) as cursor:
            sql = "INSERT INTO users (username, password, gendate, expired) VALUES (%s, %s, NOW(), 0)"
            cursor.execute(sql, (username, base64_password))
            connection.commit()

def update_user(username, password):
    base64_password = base64.b64encode(password.encode('utf-8')).decode('utf-8')
    connection = get_conn()
    with connection:
        with connection.cursor(dictionary=True) as cursor:
            sql = "UPDATE users SET password=%s, gendate=NOW(), expired=0 WHERE username = %s"
            cursor.execute(sql, (base64_password, username,))
            connection.commit()

def generate_qrcode(password):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(password)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')

    return img_base64

def get_secret(key):
    with open("/var/openfaas/secrets/{}".format(key)) as f:
        return f.read().strip()