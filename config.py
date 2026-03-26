import os

# Directory and filename for the single, canonical SQLite DB used by the whole project.
DB_DIR = 'instance'
DB_NAME = 'seats.db'

# Ensure the directory exists so that sqlite3 can create/open the DB without errors.
os.makedirs(DB_DIR, exist_ok=True)

# Absolute/relative path that application code should import and use.
DATABASE_PATH = os.path.join(DB_DIR, DB_NAME) 