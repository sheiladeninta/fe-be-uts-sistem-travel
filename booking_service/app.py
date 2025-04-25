from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import requests
import json
import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Service URLs
USER_SERVICE_URL = "http://localhost:5001/api"
DESTINATION_SERVICE_URL = "http://localhost:5002/api"

# Initialize database
def init_db():
    conn = sqlite3.connect('bookings.db')
    cursor = conn.cursor()
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
    conn.commit()
    conn.close()

@app.route('/api/bookings', methods=['GET'])
def get_all_bookings():
    conn = sqlite3.connect('bookings.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings")
    bookings = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
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
    
    return jsonify({"bookings": enriched_bookings})

@app.route('/api/bookings/user/<int:user_id>', methods=['GET'])
def get_user_bookings(user_id):
    conn = sqlite3.connect('bookings.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE user_id=?", (user_id,))
    bookings = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
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
    
    return jsonify({"bookings": enriched_bookings})

@app.route('/api/bookings/<int:booking_id>', methods=['GET'])
def get_booking(booking_id):
    conn = sqlite3.connect('bookings.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE id=?", (booking_id,))
    booking = cursor.fetchone()
    conn.close()
    
    if not booking:
        return jsonify({"error": "Booking not found"}), 404
    
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
    
    return jsonify(booking_dict)

@app.route('/api/bookings', methods=['POST'])
def create_booking():
    data = request.json
    
    if not all(key in data for key in ['user_id', 'destination_id', 'travel_date', 'passengers']):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Validate user exists
    try:
        user_response = requests.get(f"{USER_SERVICE_URL}/users/{data['user_id']}")
        if user_response.status_code != 200:
            return jsonify({"error": "User not found"}), 404
    except requests.RequestException:
        return jsonify({"error": "User service unavailable"}), 503
    
    # Validate and get destination details
    try:
        destination_response = requests.get(f"{DESTINATION_SERVICE_URL}/destinations/{data['destination_id']}")
        if destination_response.status_code != 200:
            return jsonify({"error": "Destination not found"}), 404
        destination = destination_response.json()
    except requests.RequestException:
        return jsonify({"error": "Destination service unavailable"}), 503
    
    # Calculate total price
    total_price = destination['price'] * data['passengers']
    booking_date = datetime.datetime.now().strftime('%Y-%m-%d')
    
    conn = sqlite3.connect('bookings.db')
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO bookings (user_id, destination_id, booking_date, travel_date, 
                             passengers, total_price, status) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data['user_id'], 
            data['destination_id'], 
            booking_date, 
            data['travel_date'], 
            data['passengers'], 
            total_price, 
            'Confirmed'
        )
    )
    conn.commit()
    booking_id = cursor.lastrowid
    conn.close()
    
    return jsonify({
        "id": booking_id,
        "user_id": data['user_id'],
        "destination_id": data['destination_id'],
        "booking_date": booking_date,
        "travel_date": data['travel_date'],
        "passengers": data['passengers'],
        "total_price": total_price,
        "status": "Confirmed",
        "message": "Booking created successfully"
    }), 201

@app.route('/api/bookings/<int:booking_id>', methods=['PUT'])
def update_booking_status(booking_id):
    data = request.json
    
    if 'status' not in data:
        return jsonify({"error": "Status field is required"}), 400
    
    conn = sqlite3.connect('bookings.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM bookings WHERE id=?", (booking_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "Booking not found"}), 404
    
    cursor.execute("UPDATE bookings SET status=? WHERE id=?", (data['status'], booking_id))
    conn.commit()
    conn.close()
    
    return jsonify({"message": f"Booking status updated to {data['status']}"})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5003)