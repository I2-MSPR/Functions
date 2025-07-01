import base64
from google.cloud.sql.connector import Connector, IPTypes
from io import BytesIO
import pymysql
import qrcode
import string
import secrets

def handle(event, context):
    username = event.query['username']
    
    user = get_user(username)
    
    if user is None:
        password = generate_password()
        create_user(username, password)
    else:
        password = user.password
    
    qrcode = generate_qrcode(password)
    
    return {
        "statusCode": 200,
        "body": { "qrcode": qrcode }
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
    db_password = get_secret("database-mdp")
    with Connector() as connector:
        return connector.connect(
            "firm-reason-462012-p9:europe-west1:mspr2",
            "pymysql",
            user="cloud-connect-prod",
            password=db_password,
            db="cloud_connect",
            ip_type=IPTypes.PUBLIC,   
        )

def get_user(username) -> dict | None:
    connection = get_conn()
    with connection:
        with connection.cursor(dictionary=True) as cursor:
            sql = "SELECT id FROM User WHERE username = %s"
            cursor.execute(sql, (username,))
            user = cursor.fetchone()
            return user
    
def create_user(username, password):
    base64_password = base64.b64encode(password.encode('utf-8')).decode('utf-8')
    connection = get_conn()
    with connection:
        with connection.cursor(dictionary=True) as cursor:
            sql = "INSERT INTO users (username, password) VALUES (%s, %s)"
            cursor.execute(sql, (username, base64_password))
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