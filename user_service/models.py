import sqlite3
from flask import g

DATABASE = 'users.db'

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

class User:
    @staticmethod
    def create_table():
        db = sqlite3.connect(DATABASE)
        cursor = db.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL
        )
        ''')
        db.commit()
        db.close()
    
    @staticmethod
    def get_all():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, name, email, phone FROM users")
        users = [dict(row) for row in cursor.fetchall()]
        return users
    
    @staticmethod
    def get_by_id(user_id):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, name, email, phone FROM users WHERE id=?", (user_id,))
        user = cursor.fetchone()
        return dict(user) if user else None
    
    @staticmethod
    def create(name, email, phone, password):
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (name, email, phone, password) VALUES (?, ?, ?, ?)",
                (name, email, phone, password)
            )
            db.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    @staticmethod
    def authenticate(email, password):
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT id, name, email, phone FROM users WHERE email=? AND password=?",
            (email, password)
        )
        user = cursor.fetchone()
        return dict(user) if user else None
    
class Admin:
    @staticmethod
    def create_table():
        db = sqlite3.connect(DATABASE)
        cursor = db.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        ''')
        db.commit()
        db.close()
    
    @staticmethod
    def get_all():
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("SELECT id, username FROM admins")
            admins = [dict(row) for row in cursor.fetchall()]
            return admins
        finally:
            cursor.close()
    
    @staticmethod
    def get_by_id(admin_id):
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("SELECT id, username FROM admins WHERE id=?", (admin_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            cursor.close()

    @staticmethod
    def authenticate(username, password):
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute(
                "SELECT id, username FROM admins WHERE username=? AND password=?",
                (username, password)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            cursor.close()

    @staticmethod
    def create(username, password):
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO admins (username, password) VALUES (?, ?)",
                (username, password)
            )
            db.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            db.rollback()
            print(f"Error creating admin: {e}")
            return None
        finally:
            cursor.close()