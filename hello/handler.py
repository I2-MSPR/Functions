def handle(event, context):
    username = event.query['username']
    return {
        "statusCode": 200,
        "body": {
            "id": 1,
            "username": username,
            "password": "RXBzaS4xMjM=",
        },
        "headers": {
            "Content-type": "text/plain",
            "Access-Control-Allow-Origin": "http://127.0.0.1:8000"
        }
    }
