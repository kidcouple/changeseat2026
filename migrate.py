import sqlite3
import os

db_path = 'instance/seats.db'
if not os.path.exists(db_path):
    # Try root if instance doesn't work (for older setups)
    if os.path.exists('seats.db'):
        db_path = 'seats.db'
    else:
        print(f"Database seats.db not found in root or instance.")
else:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        # Check if column exists
        c.execute("PRAGMA table_info(student)")
        columns = [col[1] for col in c.fetchall()]
        if 'is_transferred' not in columns:
            c.execute('ALTER TABLE student ADD COLUMN is_transferred BOOLEAN DEFAULT 0')
            conn.commit()
            print("Column 'is_transferred' added successfully.")
        else:
            print("Column 'is_transferred' already exists.")
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        conn.close()
