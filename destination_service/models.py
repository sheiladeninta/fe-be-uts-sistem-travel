import sqlite3
from flask import g

DATABASE = 'destinations.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def close_db(e=None):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

class Destination:
    @staticmethod
    def create_table():
        db = sqlite3.connect(DATABASE)
        cursor = db.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS destinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            duration TEXT NOT NULL,
            image_url TEXT NOT NULL
        )
        ''')
        db.commit()
        db.close()
    
    @staticmethod
    def get_all():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM destinations")
        destinations = [dict(row) for row in cursor.fetchall()]
        return destinations
    
    @staticmethod
    def get_by_id(destination_id):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM destinations WHERE id=?", (destination_id,))
        destination = cursor.fetchone()
        return dict(destination) if destination else None
    
    @staticmethod
    def create(name, description, price, duration, image_url):
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO destinations (name, description, price, duration, image_url) VALUES (?, ?, ?, ?, ?)",
            (name, description, price, duration, image_url)
        )
        db.commit()
        return cursor.lastrowid
    
    @staticmethod
    def create_sample_data():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM destinations")
        count = cursor.fetchone()[0]
        
        if count == 0:
            sample_destinations = [
                ('Bali Paradise Tour', 'Enjoy the beautiful beaches and cultural experiences in Bali.', 
                 2500000, '3 days 2 nights', 'https://via.placeholder.com/300x200?text=Bali'),
                ('Yogyakarta Heritage Tour', 'Explore ancient temples and traditional arts in Yogyakarta.', 
                 1800000, '2 days 1 night', 'https://via.placeholder.com/300x200?text=Yogyakarta'),
                ('Bandung Highland Tour', 'Experience cool weather and tea plantations in Bandung.', 
                 1500000, '2 days 1 night', 'https://via.placeholder.com/300x200?text=Bandung'),
                ('Raja Ampat Diving Tour', 'Discover the underwater paradise of Raja Ampat.', 
                 5000000, '4 days 3 nights', 'https://via.placeholder.com/300x200?text=Raja+Ampat'),
                ('Lombok Island Tour', 'Visit beautiful beaches and explore local culture in Lombok.', 
                 2200000, '3 days 2 nights', 'https://via.placeholder.com/300x200?text=Lombok')
            ]
            cursor.executemany(
                "INSERT INTO destinations (name, description, price, duration, image_url) VALUES (?, ?, ?, ?, ?)",
                sample_destinations
            )
            db.commit()
            return True
        return False