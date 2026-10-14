import mysql.connector
from db import get_db_connection

try:
    conn = get_db_connection()
    print("Koneksi database berhasil!")

    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")

    for tabel in cursor.fetchall():
        print(tabel[0])

    cursor.close()
    conn.close()

except mysql.connector.Error as err:
    print("Koneksi gagal:", err)