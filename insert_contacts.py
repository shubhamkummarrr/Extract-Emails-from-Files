
import mysql.connector
import json

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="SHUB@@1234",
    database="emails_db"
)

cursor = conn.cursor()

# Create table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS contact_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    folder VARCHAR(255),
    file VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT
)
""")

data = json.load(open("extracted_results.json"))

def file_exists(folder, file):
    cursor.execute(
        "SELECT 1 FROM contact_data WHERE folder=%s AND file=%s LIMIT 1",
        (folder, file)
    )
    return cursor.fetchone() is not None

def insert_row(folder, file, email=None, phone=None, address=None):
    cursor.execute("""
        INSERT INTO contact_data (folder, file, email, phone, address)
        VALUES (%s, %s, %s, %s, %s)
    """, (folder, file, email, phone, address))

for folder_obj in data["folders"]:
    folder = folder_obj["folder"]

    for file_obj in folder_obj["files"]:
        file = file_obj["file_name"]

        if file_exists(folder, file):
            print("Skipping duplicate:", folder, file)
            continue

        emails = file_obj["emails"]
        phones = file_obj["phones"]
        addresses = file_obj["addresses"]

        for e in emails:
            insert_row(folder, file, email=e)

        for p in phones:
            insert_row(folder, file, phone=p)

        for a in addresses:
            insert_row(folder, file, address=a)

conn.commit()
cursor.close()
conn.close()

print("Insert complete!")
