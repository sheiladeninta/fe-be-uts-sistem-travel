from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize database
def init_db():
    conn = sqlite3.connect('destinations.db')
    cursor = conn.cursor()
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
    conn.commit()
    conn.close()

# Create sample destinations if DB is empty
def create_sample_destinations():
    conn = sqlite3.connect('destinations.db')
    cursor = conn.cursor()
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
        conn.commit()
    
    conn.close()

@app.route('/api/destinations', methods=['GET'])
def get_destinations():
    conn = sqlite3.connect('destinations.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM destinations")
    destinations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"destinations": destinations})

@app.route('/api/destinations/<int:destination_id>', methods=['GET'])
def get_destination(destination_id):
    conn = sqlite3.connect('destinations.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM destinations WHERE id=?", (destination_id,))
    destination = cursor.fetchone()
    conn.close()
    
    if destination:
        return jsonify(dict(destination))
    return jsonify({"error": "Destination not found"}), 404

@app.route('/api/destinations', methods=['POST'])
def add_destination():
    data = request.json
    
    if not all(key in data for key in ['name', 'description', 'price', 'duration', 'image_url']):
        return jsonify({"error": "Missing required fields"}), 400
    
    conn = sqlite3.connect('destinations.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO destinations (name, description, price, duration, image_url) VALUES (?, ?, ?, ?, ?)",
        (data['name'], data['description'], data['price'], data['duration'], data['image_url'])
    )
    conn.commit()
    destination_id = cursor.lastrowid
    conn.close()
    
    return jsonify({"id": destination_id, "message": "Destination added successfully"}), 201

if __name__ == '__main__':
    init_db()
    create_sample_destinations()
    app.run(debug=True, port=5002)