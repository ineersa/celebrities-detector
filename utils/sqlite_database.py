import sqlite3

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('/media/ineersa/ssd/celebrities/data/celebrities.db')

# Create a new SQLite cursor
c = conn.cursor()

# Create a new SQLite table with the specified columns
c.execute('''
          CREATE TABLE IF NOT EXISTS celebrities
          (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (name)
          )
          ''')

c.execute('''
    CREATE TABLE IF NOT EXISTS celebrities_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        celebrity_id INTEGER NOT NULL,
        image_path TEXT NOT NULL,
        face_image_path TEXT,
        face_embedding TEXT, 
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (celebrity_id) REFERENCES celebrities(id)
    );
    ''')
c.execute('CREATE INDEX idx_celebrity_id ON celebrities_images(celebrity_id);')

# Commit the changes and close the connection
conn.commit()
conn.close()