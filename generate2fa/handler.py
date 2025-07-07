import pyotp
import qrcode
import qrcode.image.svg
import base64
import json
import pymysql
import mysql.connector
from io import BytesIO

def handle(event, context):
    try :
        key = generate_secret()
        qr = generate_qrcode(key, event.query["username"])
        encoded_key = crypt_secret(key)
        userExists = database_storage(encoded_key, event.query["username"])
        if not userExists:
            return {
                "statusCode": 404,
                "body": "User not Found",
            "headers": {
                "Content-type": "text/plain",
                "Access-Control-Allow-Origin": "http://127.0.0.1:8000"
            }
            }
        return {
            "statusCode": 200,
            "body": { "qrcode" : qr },
            "headers": {
                "Content-type": "text/plain",
                "Access-Control-Allow-Origin": "http://127.0.0.1:8000"
            }
        }
    except:
        return {
            "statusCode": 500,
            "body": { "qr": qr, "userExists" : userExists },
            "headers": {
                "Content-type": "text/plain",
                "Access-Control-Allow-Origin": "http://127.0.0.1:8000"
            }
        }

def generate_secret():
    return pyotp.random_base32()

def generate_qrcode(key, username):
    uri = pyotp.totp.TOTP(key).provisioning_uri(name=username, issuer_name="Cloud Connect")
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    
    return img_base64


def crypt_secret(key):
    encoded_binary = (base64.b64encode(key.encode('ascii')))
    return encoded_binary.decode('ascii')

def database_storage(encoded_key, username):
    connection = getconn()
    with connection.cursor(dictionary=True) as cur:
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        if user is None:
            return False
        else:
            id = user["id"]
            cur.execute("UPDATE users SET mfa = %s WHERE id = %s", (encoded_key, id))
            connection.commit()
            return True

def getconn() -> pymysql.connections.Connection:
    mdp = get_secret("password")
    return mysql.connector.connect(
        host="mysql.openfaas-fn.svc.cluster.local",
        user="root",
        password=mdp,
        database="cloud-connect"
    )

def get_secret(key):
    with open("/var/openfaas/secrets/{}".format(key)) as f:
        return f.read().strip()
