import sqlite3
import datetime
from flask import g
import requests

DATABASE = 'bookings.db'
USER_SERVICE_URL = "http://localhost:5001/api"
DESTINATION_SERVICE_URL = "http://localhost:5002/api"

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

class Booking:
    @staticmethod
    def create_table():
        db = sqlite3.connect(DATABASE)
        cursor = db.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            destination_id INTEGER NOT NULL,
            booking_date TEXT NOT NULL,
            travel_date TEXT NOT NULL,
            passengers INTEGER NOT NULL,
            total_price REAL NOT NULL,
            status TEXT NOT NULL
        )
        ''')
        db.commit()
        db.close()
    
    @staticmethod
    def get_all():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM bookings")
        bookings = [dict(row) for row in cursor.fetchall()]
        
        # Enrich booking data with user and destination details
        enriched_bookings = []
        for booking in bookings:
            # Get user details
            try:
                user_response = requests.get(f"{USER_SERVICE_URL}/users/{booking['user_id']}")
                user_data = user_response.json() if user_response.status_code == 200 else {"name": "Unknown User"}
            except requests.RequestException:
                user_data = {"name": "User Service Unavailable"}
            
            # Get destination details
            try:
                destination_response = requests.get(f"{DESTINATION_SERVICE_URL}/destinations/{booking['destination_id']}")
                destination_data = destination_response.json() if destination_response.status_code == 200 else {"name": "Unknown Destination"}
            except requests.RequestException:
                destination_data = {"name": "Destination Service Unavailable"}
            
            enriched_booking = booking.copy()
            enriched_booking["user"] = user_data
            enriched_booking["destination"] = destination_data
            enriched_bookings.append(enriched_booking)
        
        return enriched_bookings
    
    @staticmethod
    def get_by_id(booking_id):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM bookings WHERE id=?", (booking_id,))
        booking = cursor.fetchone()
        
        if not booking:
            return None
        
        booking_dict = dict(booking)
        
        # Get user details
        try:
            user_response = requests.get(f"{USER_SERVICE_URL}/users/{booking_dict['user_id']}")
            if user_response.status_code == 200:
                booking_dict["user"] = user_response.json()
            else:
                booking_dict["user"] = {"name": "Unknown User"}
        except requests.RequestException:
            booking_dict["user"] = {"name": "User Service Unavailable"}
        
        # Get destination details
        try:
            destination_response = requests.get(f"{DESTINATION_SERVICE_URL}/destinations/{booking_dict['destination_id']}")
            if destination_response.status_code == 200:
                booking_dict["destination"] = destination_response.json()
            else:
                booking_dict["destination"] = {"name": "Unknown Destination"}
        except requests.RequestException:
            booking_dict["destination"] = {"name": "Destination Service Unavailable"}
        
        return booking_dict
    
    @staticmethod
    def get_by_user(user_id):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM bookings WHERE user_id=?", (user_id,))
        bookings = [dict(row) for row in cursor.fetchall()]
        
        # Enrich booking data with destination details
        enriched_bookings = []
        for booking in bookings:
            # Get destination details
            try:
                destination_response = requests.get(f"{DESTINATION_SERVICE_URL}/destinations/{booking['destination_id']}")
                destination_data = destination_response.json() if destination_response.status_code == 200 else {"name": "Unknown Destination"}
            except requests.RequestException:
                destination_data = {"name": "Destination Service Unavailable"}
            
            enriched_booking = booking.copy()
            enriched_booking["destination"] = destination_data
            enriched_bookings.append(enriched_booking)
        
        return enriched_bookings
    
    @staticmethod
    def create(user_id, destination_id, travel_date, passengers):
        # Validate user exists
        try:
            user_response = requests.get(f"{USER_SERVICE_URL}/users/{user_id}")
            if user_response.status_code != 200:
                return None, "User not found"
        except requests.RequestException:
            return None, "User service unavailable"
        
        # Validate and get destination details
        try:
            destination_response = requests.get(f"{DESTINATION_SERVICE_URL}/destinations/{destination_id}")
            if destination_response.status_code != 200:
                return None, "Destination not found"
            destination = destination_response.json()
        except requests.RequestException:
            return None, "Destination service unavailable"
        
        # Calculate total price
        total_price = destination['price'] * passengers
        booking_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO bookings (user_id, destination_id, booking_date, travel_date, 
                                passengers, total_price, status) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id, 
                destination_id, 
                booking_date, 
                travel_date, 
                passengers, 
                total_price, 
                'Confirmed'
            )
        )
        db.commit()
        booking_id = cursor.lastrowid
        
        return booking_id, "Booking created successfully"
    
    @staticmethod
    def update_status(booking_id, status):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM bookings WHERE id=?", (booking_id,))
        if not cursor.fetchone():
            return False, "Booking not found"
        
        cursor.execute("UPDATE bookings SET status=? WHERE id=?", (status, booking_id))
        db.commit()
        
        return True, f"Booking status updated to {status}"