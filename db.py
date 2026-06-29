import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Sadhana@077",
    database="community_resource_sharing"
)

cursor = db.cursor()

print("Database Connected Successfully")