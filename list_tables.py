import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

conn = psycopg.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    connect_timeout=10,
)

cur = conn.cursor()

cur.execute(
    "SELECT tablename FROM pg_catalog.pg_tables "
    "WHERE schemaname = 'public' ORDER BY tablename"
)

print("\nTABLES IN Expense-Policy-Agent:")
for row in cur.fetchall():
    print(row[0])

cur.close()
conn.close()