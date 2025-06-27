import time
import pyotp
import qrcode
import base64

def handle(event, context):
    return {
        "statusCode": 200,
        "body": "Hello from OpenFaaS!"
    }


def generate_secret():
    return pyotp.random_base32()

def generate_qrcode(key, username):
    uri = pyotp.totp.TOTP(key).provisioning_uri(name=username, issuer_name="Cloud Connect")
    factory = qrcode.image.svg.SvgImage
    qr = qrcode.make(uri, image_factory=factory)

def crypt_secret(key):
    encoded_binary = (base64.b64encode(key.encode('ascii')))
    return encoded_binary.decode('ascii')