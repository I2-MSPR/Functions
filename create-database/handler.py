import mysql.connector


def handle(event, context):
    with open("/var/openfaas/secrets/password", "r") as f:
        password = f.read().strip()
    
    conn = mysql.connector.connect(
        host="mysql.openfaas-fn.svc.cluster.local",
        user="root",
        password=password,
        database="mysql"
    )
    cursor = conn.cursor()
    db_name = 'cloud-connect'
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`;")
    conn.commit()
    
    conn2 = mysql.connector.connect(
        host="mysql.openfaas-fn.svc.cluster.local",
        user="root",
        password=password,
        database=db_name
    )
    cursor2 = conn2.cursor()

    cursor2.execute("""
            CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) NOT NULL,
        password VARCHAR(255) NOT NULL,
        mfa VARCHAR(255),
        gendate DATETIME,
        expired TINYINT(1) NOT NULL DEFAULT 0
    );
        """)
    conn2.commit()
    
    return {
        "statusCode": 200,
        "body": {
            "message": "table done"
        },
    }

