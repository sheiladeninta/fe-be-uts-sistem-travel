from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import requests
import json
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'travely_secret_key'

# Service URLs
USER_SERVICE_URL = "http://localhost:5001/api"
DESTINATION_SERVICE_URL = "http://localhost:5002/api"
BOOKING_SERVICE_URL = "http://localhost:5003/api"

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads', 'images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'jfif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Pastikan folder uploads ada
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Tambahkan timestamp untuk menghindari nama file yang sama
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        # Return path relatif untuk akses melalui web
        return f"/static/uploads/images/{filename}"
    return None

@app.route('/')
def index():
    try:
        response = requests.get(f"{DESTINATION_SERVICE_URL}/destinations")
        destinations = response.json()['destinations'] if response.status_code == 200 else []
    except requests.RequestException:
        destinations = []
        flash('Unable to connect to destination service', 'danger')
    
    return render_template('index.html', destinations=destinations)

@app.route('/destinations')
def destinations():
    try:
        response = requests.get(f"{DESTINATION_SERVICE_URL}/destinations")
        destinations = response.json()['destinations'] if response.status_code == 200 else []
    except requests.RequestException:
        destinations = []
        flash('Unable to connect to destination service', 'danger')
    
    return render_template('destinations.html', destinations=destinations)

@app.route('/destinations/<int:destination_id>')
def destination_detail(destination_id):
    try:
        response = requests.get(f"{DESTINATION_SERVICE_URL}/destinations/{destination_id}")
        if response.status_code == 200:
            destination = response.json()
        else:
            flash('Destination not found', 'danger')
            return redirect(url_for('destinations'))
    except requests.RequestException:
        flash('Unable to connect to destination service', 'danger')
        return redirect(url_for('destinations'))
    
    return render_template('destination_detail.html', destination=destination)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email_or_username = request.form['email_or_username']
        password = request.form['password']

        # Step 1: Coba login sebagai User
        try:
            user_response = requests.post(
                f"{USER_SERVICE_URL}/users/auth",
                json={"email": email_or_username, "password": password}
            )

            if user_response.status_code == 200 and user_response.json().get('success'):
                session['user'] = user_response.json()['user']
                flash('Login successful as User', 'success')
                return redirect(url_for('index'))
        except requests.RequestException:
            flash('Unable to connect to user service', 'danger')
            return render_template('login.html', error="Service unavailable.")

        # Step 2: Kalau gagal login User, coba login Admin
        try:
            admin_response = requests.post(
                f"{USER_SERVICE_URL}/admins/auth",
                json={"username": email_or_username, "password": password}
            )

            if admin_response.status_code == 200 and admin_response.json().get('success'):
                session['admin'] = admin_response.json()['admin']
                flash('Login successful as Admin', 'success')
                return redirect(url_for('admin_dashboard'))
        except requests.RequestException:
            flash('Unable to connect to admin service', 'danger')
            return render_template('login.html', error="Service unavailable.")

        # Kalau dua-duanya gagal
        error = "Invalid email/username or password."

    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        
        try:
            response = requests.post(
                f"{USER_SERVICE_URL}/users", 
                json={
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "password": password
                }
            )
            
            if response.status_code == 201:
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
            else:
                flash(f'Registration failed: {response.json().get("error", "Unknown error")}', 'danger')
        except requests.RequestException:
            flash('Unable to connect to user service', 'danger')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    if 'user' in session:
        session.pop('user', None)
        flash('You have been logged out', 'success')
    elif 'admin' in session:
        session.pop('admin', None)
        flash('Admin logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/book/<int:destination_id>', methods=['GET', 'POST'])
def booking(destination_id):
    if 'user' not in session:
        flash('Please login to book a trip', 'warning')
        return redirect(url_for('login'))
    
    try:
        dest_response = requests.get(f"{DESTINATION_SERVICE_URL}/destinations/{destination_id}")
        if dest_response.status_code != 200:
            flash('Destination not found', 'danger')
            return redirect(url_for('destinations'))
        destination = dest_response.json()
    except requests.RequestException:
        flash('Unable to connect to destination service', 'danger')
        return redirect(url_for('destinations'))
    
    if request.method == 'POST':
        travel_date = request.form['travel_date']
        passengers = int(request.form['passengers'])
        
        booking_data = {
            "user_id": session['user']['id'],
            "destination_id": destination_id,
            "travel_date": travel_date,
            "passengers": passengers
        }
        
        try:
            response = requests.post(
                f"{BOOKING_SERVICE_URL}/bookings", 
                json=booking_data
            )
            
            if response.status_code == 201:
                flash('Booking successful!', 'success')
                return redirect(url_for('user_bookings'))
            else:
                flash(f'Booking failed: {response.json().get("error", "Unknown error")}', 'danger')
        except requests.RequestException:
            flash('Unable to connect to booking service', 'danger')
    
    # Calculate minimum date (tomorrow)
    min_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    return render_template('booking.html', destination=destination, min_date=min_date)

@app.route('/profile')
def user_profile():
    if 'user' not in session:
        flash('Please login to view your profile', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    
    try:
        user_response = requests.get(f"{USER_SERVICE_URL}/users/{user_id}")
        if user_response.status_code == 200:
            user_data = user_response.json()
        else:
            flash('Unable to retrieve user data', 'danger')
            return redirect(url_for('index'))
    except requests.RequestException:
        flash('Unable to connect to user service', 'danger')
        return redirect(url_for('index'))
    
    return render_template('user_profile.html', user=user_data)

@app.route('/bookings')
def user_bookings():
    if 'user' not in session:
        flash('Please login to view your bookings', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    
    try:
        bookings_response = requests.get(f"{BOOKING_SERVICE_URL}/bookings/user/{user_id}")
        if bookings_response.status_code == 200:
            bookings = bookings_response.json()['bookings']
            # Hitung total bookings dengan status Confirmed
            confirmed_count = sum(1 for booking in bookings if booking.get('status', '').lower() == 'confirmed')

            # Simpan ke session
            session['user_stats'] = {
                'total_bookings': confirmed_count
            }
            session.modified = True
        else:
            bookings = []
            flash('Unable to retrieve booking data', 'danger')
    except requests.RequestException:
        bookings = []
        flash('Unable to connect to booking service', 'danger')
    
    return render_template('user_bookings.html', bookings=bookings)

@app.route('/booking/<int:booking_id>')
def booking_detail(booking_id):
    if 'user' not in session:
        flash('Please login to view booking details', 'warning')
        return redirect(url_for('login'))
    
    try:
        booking_response = requests.get(f"{BOOKING_SERVICE_URL}/bookings/{booking_id}")
        if booking_response.status_code == 200:
            booking = booking_response.json()
            # Verify the booking belongs to the logged-in user
            if booking['user_id'] != session['user']['id']:
                flash('Unauthorized access to booking', 'danger')
                return redirect(url_for('user_bookings'))
        else:
            flash('Booking not found', 'danger')
            return redirect(url_for('user_bookings'))
    except requests.RequestException:
        flash('Unable to connect to booking service', 'danger')
        return redirect(url_for('user_bookings'))
    
    return render_template('booking_detail.html', booking=booking)

from functools import wraps
from flask import session, redirect, url_for, flash

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin'):
            # Clear any existing user session if trying to access admin area
            if 'user' in session:
                session.pop('user')
            flash('Admin access required', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    try:
        # Ambil data dengan timeout
        users = requests.get(f"{USER_SERVICE_URL}/users").json().get('users', [])
        bookings = requests.get(f"{BOOKING_SERVICE_URL}/bookings").json().get('bookings', [])
        destinations = requests.get(f"{DESTINATION_SERVICE_URL}/destinations").json().get('destinations', [])
        
        # Sort data untuk mendapatkan yang terbaru (berdasarkan id, asumsikan id yang lebih besar = lebih baru)
        sorted_bookings = sorted(bookings, key=lambda x: x.get('id', 0), reverse=True)
        sorted_destinations = sorted(destinations, key=lambda x: x.get('id', 0), reverse=True)
        
        # Ambil hanya 3 data terbaru
        recent_bookings = sorted_bookings[:3]
        recent_destinations = sorted_destinations[:3]
        
        stats = {
            'users_count': len(users),
            'bookings_count': len(bookings),
            'destinations_count': len(destinations),
            'recent_bookings': recent_bookings,
            'recent_destinations': recent_destinations
        }
        
        return render_template('admin_dashboard.html', stats=stats)
        
    except requests.RequestException as e:
        app.logger.error(f"Service error: {str(e)}")
        flash("Failed to load data from services", "danger")
        return render_template('admin_dashboard.html', stats=None)
    
@app.route('/admin/bookings')
@admin_required
def admin_bookings():
    try:
        users = requests.get(f"{USER_SERVICE_URL}/users").json().get('users', [])
        bookings = requests.get(f"{BOOKING_SERVICE_URL}/bookings").json().get('bookings', [])
        destinations = requests.get(f"{DESTINATION_SERVICE_URL}/destinations").json().get('destinations', [])

        # Bikin dictionary buat lookup cepat
        user_dict = {user['id']: user for user in users}
        destination_dict = {dest['id']: dest for dest in destinations}

        # Update setiap booking supaya punya user_name dan destination_name
        for booking in bookings:
            booking['user_name'] = user_dict.get(booking['user_id'], {}).get('name', 'Unknown User')
            booking['destination_name'] = destination_dict.get(booking['destination_id'], {}).get('name', 'Unknown Destination')

        return render_template('admin_manage_booking.html', bookings=bookings, users=users, destinations=destinations)
    except requests.RequestException as e:
        app.logger.error(f"Service error: {str(e)}")
        flash("Failed to load bookings data", "danger")
        return render_template('admin_manage_booking.html', bookings=[])

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    # If already logged in as admin
    if session.get('admin'):
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Please fill all fields', 'danger')
            return render_template('login.html')

        try:
            response = requests.post(
                f"{USER_SERVICE_URL}/admins/auth",
                json={"username": username, "password": password},
                timeout=5
            )

            if response.status_code == 200 and response.json().get('success'):
                # Clear any existing user session
                session.clear()
                session['admin'] = response.json()['admin']
                flash('Admin login successful', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid admin credentials', 'danger')
        except requests.RequestException as e:
            app.logger.error(f"Auth service error: {str(e)}")
            flash('Unable to connect to authentication service', 'danger')
    
    return render_template('login.html')

@app.route('/api/update_profile/<int:user_id>', methods=['PUT'])
def update_profile(user_id):
    if 'user' not in session or session['user']['id'] != user_id:
        return jsonify({'success': False, 'error': 'Unauthorized access'}), 403
    
    data = request.json
    
    # Validasi data
    if not all(key in data for key in ['name', 'email', 'phone']):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    # Siapkan data untuk update
    update_data = {
        'name': data['name'],
        'email': data['email'],
        'phone': data['phone']
    }
    
    # Tambahkan password jika ada
    if 'password' in data and data['password']:
        update_data['password'] = data['password']
    
    try:
        # Kirim request update ke user service
        response = requests.put(
            f"{USER_SERVICE_URL}/users/{user_id}",
            json=update_data
        )
        
        if response.status_code == 200:
            # Update session data juga
            session['user']['name'] = data['name']
            session['user']['email'] = data['email']
            session['user']['phone'] = data['phone']
            
            session.modified = True
            
            return jsonify({'success': True, 'message': 'Profile updated successfully'})
        else:
            return jsonify({'success': False, 'error': response.json().get('error', 'Update failed')}), response.status_code
    except requests.RequestException:
        return jsonify({'success': False, 'error': 'Unable to connect to user service'}), 500

@app.route('/admin/destinations')
def admin_destinations():
    if 'admin' not in session:
        flash('Admin access required', 'danger')
        return redirect(url_for('admin_login'))
    
    try:
        # Ambil semua destinasi
        response = requests.get(f"{DESTINATION_SERVICE_URL}/destinations")
        destinations = response.json()['destinations'] if response.status_code == 200 else []
        
        # Ambil 5 destinasi terbaru (sort berdasarkan ID secara descending)
        recent_destinations = sorted(destinations, key=lambda x: x['id'], reverse=True)[:5]
        
    except requests.RequestException:
        destinations = []
        recent_destinations = []
        flash('Unable to connect to destination service', 'danger')
    
    return render_template('admin_destinations.html', destinations=destinations, recent_destinations=recent_destinations)

@app.route('/admin/destinations/add', methods=['GET', 'POST'])
def admin_add_destination():
    if 'admin' not in session:
        flash('Admin access required', 'danger')
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        # Handle file upload
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file.filename == '':
                flash('No image selected', 'danger')
                return render_template('admin_add_destination.html')
            
            image_url = save_image(file)
            if not image_url:
                flash('Invalid image file. Please upload a valid image (JPG, PNG, or GIF).', 'danger')
                return render_template('admin_add_destination.html')
        
        destination_data = {
            'name': request.form['name'],
            'description': request.form['description'],
            'price': float(request.form['price']),
            'duration': request.form['duration'],
            'image_url': image_url
        }
        
        try:
            response = requests.post(
                f"{DESTINATION_SERVICE_URL}/destinations", 
                json=destination_data
            )
            
            if response.status_code == 201:
                flash('Destination added successfully', 'success')
                return redirect(url_for('admin_destinations'))
            else:
                flash(f'Failed to add destination: {response.json().get("error", "Unknown error")}', 'danger')
        except requests.RequestException:
            flash('Unable to connect to destination service', 'danger')
    
    return render_template('admin_add_destination.html')

@app.route('/admin/destinations/edit/<int:destination_id>', methods=['GET', 'POST'])
def admin_edit_destination(destination_id):
    if 'admin' not in session:
        flash('Admin access required', 'danger')
        return redirect(url_for('admin_login'))
    
    try:
        if request.method == 'POST':
            # Get current destination data
            dest_response = requests.get(f"{DESTINATION_SERVICE_URL}/destinations/{destination_id}")
            if dest_response.status_code != 200:
                flash('Destination not found', 'danger')
                return redirect(url_for('admin_destinations'))
            current_destination = dest_response.json()
            
            # Handle file upload
            image_url = current_destination['image_url']
            if 'image' in request.files:
                file = request.files['image']
                if file.filename != '':  # Only process if a new file was uploaded
                    new_image_url = save_image(file)
                    if new_image_url:
                        image_url = new_image_url
                    else:
                        flash('Invalid image file. Please upload a valid image (JPG, PNG, or GIF).', 'danger')
                        return render_template('admin_edit_destination.html', destination=current_destination)
            
            destination_data = {
                'name': request.form['name'],
                'description': request.form['description'],
                'price': float(request.form['price']),
                'duration': request.form['duration'],
                'image_url': image_url
            }
            
            response = requests.put(
                f"{DESTINATION_SERVICE_URL}/destinations/{destination_id}", 
                json=destination_data
            )
            
            if response.status_code == 200:
                flash('Destination updated successfully', 'success')
                return redirect(url_for('admin_destinations'))
            else:
                flash(f'Failed to update destination: {response.json().get("error", "Unknown error")}', 'danger')
        
        # Get destination data for form
        dest_response = requests.get(f"{DESTINATION_SERVICE_URL}/destinations/{destination_id}")
        if dest_response.status_code == 200:
            destination = dest_response.json()
        else:
            flash('Destination not found', 'danger')
            return redirect(url_for('admin_destinations'))
    except requests.RequestException:
        flash('Unable to connect to destination service', 'danger')
        return redirect(url_for('admin_destinations'))
    
    return render_template('admin_edit_destination.html', destination=destination)

@app.route('/admin/destinations/delete/<int:destination_id>', methods=['POST'])
def admin_delete_destination(destination_id):
    if 'admin' not in session:
        flash('Admin access required', 'danger')
        return redirect(url_for('admin_login'))
    
    try:
        response = requests.delete(f"{DESTINATION_SERVICE_URL}/destinations/{destination_id}")
        
        if response.status_code == 200:
            flash('Destination deleted successfully', 'success')
        else:
            flash(f'Failed to delete destination: {response.json().get("error", "Unknown error")}', 'danger')
    except requests.RequestException:
        flash('Unable to connect to destination service', 'danger')
    
    return redirect(url_for('admin_destinations'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)

