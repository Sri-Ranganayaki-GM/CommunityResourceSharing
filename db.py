import mysql.connector

db = mysql.connector.connect(
    host="reseau.proxy.rlwy.net",
    port=17012,
    user="root",
    password="xRckqqToQlAsGyMlQWdCDxjVxGVIEGZn",
    database="railway"
)

cursor = db.cursor()

print("Database Connected Successfully")