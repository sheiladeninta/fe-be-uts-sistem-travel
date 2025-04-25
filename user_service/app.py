from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize database
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

# Create some sample users if DB is empty
def create_sample_users():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    
    if count == 0:
        sample_users = [
            ('John Doe', 'john@example.com', '08123456789', 'password123'),
            ('Jane Smith', 'jane@example.com', '08234567890', 'password456'),
            ('Bob Johnson', 'bob@example.com', '08345678901', 'password789')
        ]
        cursor.executemany(
            "INSERT INTO users (name, email, phone, password) VALUES (?, ?, ?, ?)",
            sample_users
        )
        conn.commit()
    
    conn.close()

@app.route('/api/users', methods=['GET'])
def get_users():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, phone FROM users")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"users": users})

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, phone FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return jsonify(dict(user))
    return jsonify({"error": "User not found"}), 404

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.json
    
    if not all(key in data for key in ['name', 'email', 'phone', 'password']):
        return jsonify({"error": "Missing required fields"}), 400
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO users (name, email, phone, password) VALUES (?, ?, ?, ?)",
            (data['name'], data['email'], data['phone'], data['password'])
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        return jsonify({"id": user_id, "message": "User created successfully"}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Email already exists"}), 400

@app.route('/api/users/auth', methods=['POST'])
def authenticate_user():
    data = request.json
    
    if not all(key in data for key in ['email', 'password']):
        return jsonify({"error": "Missing email or password"}), 400
    
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, email, phone FROM users WHERE email=? AND password=?",
        (data['email'], data['password'])
    )
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return jsonify({"success": True, "user": dict(user)})
    return jsonify({"success": False, "error": "Invalid credentials"}), 401

if __name__ == '__main__':
    init_db()
    create_sample_users()
    app.run(debug=True, port=5001)