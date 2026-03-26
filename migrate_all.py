import sqlite3
import os

# Find all .db files
db_files = []
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.db'):
            db_files.append(os.path.join(root, file))

print(f"Found databases: {db_files}")

for db_path in db_files:
    print(f"Migrating {db_path}...")
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        # Check if student table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student'")
        if not c.fetchone():
            print(f"Skipping {db_path}: No 'student' table.")
            continue
            
        c.execute("PRAGMA table_info(student)")
        columns = [col[1] for col in c.fetchall()]
        if 'is_transferred' not in columns:
            c.execute('ALTER TABLE student ADD COLUMN is_transferred BOOLEAN DEFAULT 0')
            conn.commit()
            print(f"Successfully added 'is_transferred' to {db_path}")
        else:
            print(f"Column already exists in {db_path}")
        conn.close()
    except Exception as e:
        print(f"Error migrating {db_path}: {e}")
