import pyotp
import qrcode
import qrcode.image.svg
import base64
import json

def handle(event, context):
    try :
        key = generate_secret()
        qr = generate_qrcode(key, event.query["username"])
        encoded_key = crypt_secret(key)
        if database_storage(encoded_key, event.query["username"]) :
            return {
                "statusCode": 200,
                "body": {"qrcode": qr.to_string().decode("utf-8")}
            }
        else :
            return {
                "statusCode": 500
            }
    except:
        return {
            "statusCode": 500
        }

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
    return True