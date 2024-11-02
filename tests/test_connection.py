import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="hackathon_user",
        password="password123",
        database="hackathon_db",
    )
    if conn.is_connected():
        print("Connected to MySQL database")
except mysql.connector.Error as err:
    print(f"Error: {err}")
finally:
    if conn.is_connected():
        conn.close()
