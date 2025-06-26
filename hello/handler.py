def handle(event, context):
    username = event.query['username']
    return {
        "statusCode": 200,
        "body": {
            "id": 1,
            "username": username,
            "password": "RXBzaS4xMjM=",
        }
    }
