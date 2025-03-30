import sqlite3

# Connect to the database (creates the file if it doesn't exist)
conn = sqlite3.connect('payments.db')
cursor = conn.cursor()

# Create the payments table if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT NOT NULL,
    amount REAL NOT NULL,
    mobile TEXT NOT NULL,
    email TEXT NOT NULL,
    order_id TEXT NOT NULL,
    utr TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()

print("Database and table created successfully!")
