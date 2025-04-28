from flask import Flask, request, jsonify
from flask_cors import CORS
from flasgger import Swagger
import sqlite3
import json
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
swagger = Swagger(app)

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
        conn.commit()
    
    conn.close()

@app.route('/api/destinations', methods=['GET'])
def get_destinations():
    """
    Get all destinations
    ---
    responses:
      200:
        description: A list of all destinations
    """
    conn = sqlite3.connect('destinations.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM destinations")
    destinations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"destinations": destinations})

@app.route('/api/destinations/<int:destination_id>', methods=['GET'])
def get_destination(destination_id):
    """
    Get a specific destination by ID
    ---
    parameters:
      - name: destination_id
        in: path
        type: integer
        required: true
        description: ID of the destination
    responses:
      200:
        description: Destination details
      404:
        description: Destination not found
    """
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
    """
    Add a new destination
    ---
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
            - description
            - price
            - duration
            - image_url
          properties:
            name:
              type: string
            description:
              type: string
            price:
              type: number
            duration:
              type: string
            image_url:
              type: string
    responses:
      201:
        description: Destination added successfully
      400:
        description: Missing required fields
    """
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

@app.route('/api/destinations/<int:destination_id>', methods=['PUT'])
def update_destination(destination_id):
    data = request.json
    
    if not all(key in data for key in ['name', 'description', 'price', 'duration', 'image_url']):
        return jsonify({"error": "Missing required fields"}), 400
    
    conn = sqlite3.connect('destinations.db')
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE destinations SET name=?, description=?, price=?, duration=?, image_url=? WHERE id=?",
        (data['name'], data['description'], data['price'], data['duration'], data['image_url'], destination_id)
    )
    conn.commit()
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"error": "Destination not found"}), 404
    
    conn.close()
    return jsonify({"message": "Destination updated successfully"})

@app.route('/api/destinations/<int:destination_id>', methods=['DELETE'])
def delete_destination(destination_id):
    conn = sqlite3.connect('destinations.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM destinations WHERE id=?", (destination_id,))
    conn.commit()
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"error": "Destination not found"}), 404
    
    conn.close()
    return jsonify({"message": "Destination deleted successfully"})

if __name__ == '__main__':
    init_db()
    create_sample_destinations()
    app.run(debug=True, port=5002)