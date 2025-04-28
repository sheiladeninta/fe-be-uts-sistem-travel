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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
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
    """
    Get all users (excluding passwords)
    ---
    responses:
      200:
        description: List of users
    """
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, phone FROM users")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"users": users})

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """
    Get a specific user by ID
    ---
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID of the user
    responses:
      200:
        description: User details
      404:
        description: User not found
    """
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
    """
    Create a new user
    ---
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
            - email
            - phone
            - password
          properties:
            name:
              type: string
              example: Alice
            email:
              type: string
              example: alice@example.com
            phone:
              type: string
              example: 08111111111
            password:
              type: string
              example: secret123
    responses:
      201:
        description: User created successfully
      400:
        description: Missing fields or email already exists
    """
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
    """
    Authenticate a user
    ---
    parameters:
      - in: body
        name: credentials
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: john@example.com
            password:
              type: string
              example: password123
    responses:
      200:
        description: Authentication successful
      401:
        description: Invalid credentials
    """
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

# create a sample admin user
def create_sample_admins():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Mengecek apakah sudah ada data admin
    cursor.execute("SELECT COUNT(*) FROM admins")
    count = cursor.fetchone()[0]
    
    if count == 0:
        sample_admins = [
            ('superadmin', 'superpassword'),
            ('admin1', 'adminpassword1'),
            ('admin2', 'adminpassword2')
        ]
        cursor.executemany(
            "INSERT INTO admins (username, password) VALUES (?, ?)",
            sample_admins
        )
        conn.commit()
    
    conn.close()

@app.route('/api/admins/auth', methods=['POST'])
def authenticate_admin():
    data = request.json
    if not all(key in data for key in ['username', 'password']):
        return jsonify({"error": "Missing username or password"}), 400
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username FROM admins WHERE username=? AND password=?",
        (data['username'], data['password'])
    )
    admin = cursor.fetchone()
    conn.close()
    
    if admin:
        return jsonify({
            "success": True,
            "admin": {"id": admin[0], "username": admin[1]}
        })
    return jsonify({"success": False, "error": "Invalid credentials"}), 401

@app.route('/api/admins', methods=['GET'])
def get_admins():
    conn = sqlite3.connect('users.db')  # Ganti dengan DB_PATH
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password FROM admins")
    admins = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"admins": admins})

@app.route('/api/admins/<int:admin_id>', methods=['GET'])
def get_admin(admin_id):
    conn = sqlite3.connect('users.db')  # Ganti dengan DB_PATH
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password FROM admins WHERE id=?", (admin_id,))
    admin = cursor.fetchone()
    conn.close()
    
    if admin:
        return jsonify(dict(admin))
    return jsonify({"error": "Admin not found"}), 404

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """
    Update a user's information
    ---
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID of the user
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              example: Alice Updated
            email:
              type: string
              example: alice_updated@example.com
            phone:
              type: string
              example: 08222222222
            password:
              type: string
              example: newpassword123
    responses:
      200:
        description: User updated successfully
      404:
        description: User not found
      400:
        description: Email already exists
    """
    data = request.json
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify({"error": "User not found"}), 404
    
    # Prepare update fields and values
    update_fields = []
    update_values = []
    
    if 'name' in data:
        update_fields.append("name = ?")
        update_values.append(data['name'])
    
    if 'email' in data:
        # Check if email is already used by another user
        if data['email'] != user[2]:  # Check if email is different from current
            cursor.execute("SELECT id FROM users WHERE email=? AND id!=?", (data['email'], user_id))
            if cursor.fetchone():
                conn.close()
                return jsonify({"error": "Email already exists"}), 400
        update_fields.append("email = ?")
        update_values.append(data['email'])
    
    if 'phone' in data:
        update_fields.append("phone = ?")
        update_values.append(data['phone'])
    
    if 'password' in data:
        update_fields.append("password = ?")
        update_values.append(data['password'])
    
    if not update_fields:
        conn.close()
        return jsonify({"error": "No fields to update"}), 400
    
    # Construct and execute the update query
    update_query = f"UPDATE users SET {', '.join(update_fields)} WHERE id=?"
    update_values.append(user_id)
    
    try:
        cursor.execute(update_query, update_values)
        conn.commit()
        
        # Get updated user info
        cursor.execute("SELECT id, name, email, phone FROM users WHERE id=?", (user_id,))
        updated_user = cursor.fetchone()
        conn.close()
        
        if updated_user:
            return jsonify({
                "id": updated_user[0],
                "name": updated_user[1],
                "email": updated_user[2],
                "phone": updated_user[3],
                "message": "User updated successfully"
            })
        return jsonify({"error": "Failed to retrieve updated user"}), 500
    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({"error": f"Database error: {str(e)}"}), 400
    except Exception as e:
        conn.close()
        return jsonify({"error": f"Update failed: {str(e)}"}), 500

if __name__ == '__main__':
    init_db()
    create_sample_users()
    create_sample_admins()
    app.run(debug=True, port=5001)
