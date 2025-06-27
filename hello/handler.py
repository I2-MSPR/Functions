def handle(event, context):
    usernames = ["Ikhlas", "Rémi", "Gaëtan", "Denis"]
    username = event.query['username']
    password = event.query['password']
    success = username in usernames and password == "RXBzaS4xMjM="
    
    return {
        "statusCode": 200 if success else 401,
        "body": {
            "message": "correct IDs" if success else "Not found"
        },
        "headers": {
            "Content-type": "text/plain",
            "Access-Control-Allow-Origin": "http://127.0.0.1:8000"
        }
    }

