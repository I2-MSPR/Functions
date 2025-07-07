import pyotp
import qrcode
import qrcode.image.svg
import base64
import json
from google.cloud.sql.connector import Connector, IPTypes
import pymysql 

def handle(event, context):
    try :
        key = generate_secret()
        qr = generate_qrcode(key, event.query["username"])
        encoded_key = crypt_secret(key)
        time_test=database_storage(encoded_key, event.query["username"])
        return {
            "statusCode": 200,
            "body": {"qrcode": qr.to_string().decode("utf-8"), "time":time_test}
        }
        """
        if database_storage(encoded_key, event.query["username"]) :
            return {
                "statusCode": 200,
                "body": {"qrcode": qr.to_string().decode("utf-8")}
            }
        else :
            return {
                "statusCode": 500
            }
            """
    except:
        raise 
    """
        return {
            "statusCode": 500
        }
        """


def generate_secret():
    return pyotp.random_base32()

def generate_qrcode(key, username):
    uri = pyotp.totp.TOTP(key).provisioning_uri(name=username, issuer_name="Cloud Connect")
    factory = qrcode.image.svg.SvgPathImage
    return qrcode.make(uri, image_factory=factory)

def crypt_secret(key):
    encoded_binary = (base64.b64encode(key.encode('ascii')))
    return encoded_binary.decode('ascii')

def database_storage(encoded_key, username):
    connection = getconn()
    with connection.cursor() as cur:
        cur.execute("SELECT NOW()")
        data = cur.fetchone()[0]
    connection.close()
    return data

def getconn() -> pymysql.connections.Connection:
    mdp = get_secret("database-mdp")
    with Connector() as connector:
        return connector.connect(
            "firm-reason-462012-p9:europe-west1:mspr2",
            "pymysql",
            user="cloud-connect-prod",
            password=mdp,
            db="cloud_connect",
            ip_type=IPTypes.PUBLIC,   
        )

def get_secret(key):
    with open("/var/openfaas/secrets/{}".format(key)) as f:
        return f.read().strip()
