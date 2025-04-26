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
                 2500000, '3 days 2 nights', 'https://static.vecteezy.com/system/resources/thumbnails/006/933/128/small/beautiful-tropical-island-scenery-two-sun-beds-loungers-umbrella-under-palm-tree-white-sand-sea-view-with-horizon-idyllic-blue-sky-calmness-and-relaxation-inspirational-beach-resort-hotel-photo.jpg'),
                ('Yogyakarta Heritage Tour', 'Explore ancient temples and traditional arts in Yogyakarta.', 
                 1800000, '2 days 1 night', 'https://raminten.com/wp-content/uploads/2024/07/tugu-jogja-300x200.jpg'),
                ('Bandung Highland Tour', 'Experience cool weather and tea plantations in Bandung.', 
                 1500000, '2 days 1 night', 'https://static.vecteezy.com/system/resources/thumbnails/009/169/931/small/bandung-indonesia-may-23-2022-group-of-tourist-at-sky-bridge-of-nimo-highland-pangalengan-bandung-west-java-indonesia-view-of-tea-plantation-mountain-and-lake-free-photo.jpg'),
                ('Raja Ampat Diving Tour', 'Discover the underwater paradise of Raja Ampat.', 
                 5000000, '4 days 3 nights', 'https://www.papuaexplorers.com/wp-content/uploads/cache/2017/03/coral-underneath-yenbuba-jetty-raja-ampat/740619268.jpg'),
                ('Lombok Island Tour', 'Visit beautiful beaches and explore local culture in Lombok.', 
                 2200000, '3 days 2 nights', 'https://static.vecteezy.com/system/resources/thumbnails/006/821/449/small/view-of-the-hills-and-coast-and-several-sailing-boats-on-padar-island-free-photo.jpg')
            ]
            cursor.executemany(
                "INSERT INTO destinations (name, description, price, duration, image_url) VALUES (?, ?, ?, ?, ?)",
                sample_destinations
            )
            db.commit()
            return True
        return False