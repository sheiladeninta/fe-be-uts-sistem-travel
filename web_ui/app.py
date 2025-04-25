from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import requests
import json
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'travely_secret_key'

# Service URLs
USER_SERVICE_URL = "http://localhost:5001/api"
DESTINATION_SERVICE_URL = "http://localhost:5002/api"
BOOKING_SERVICE_URL = "http://localhost:5003/api"

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
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            response = requests.post(
                f"{USER_SERVICE_URL}/users/auth", 
                json={"email": email, "password": password}
            )
            
            if response.status_code == 200 and response.json().get('success'):
                session['user'] = response.json()['user']
                flash('Login successful', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid email or password', 'danger')
        except requests.RequestException:
            flash('Unable to connect to user service', 'danger')
    
    return render_template('login.html')

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
    session.pop('user', None)
    flash('You have been logged out', 'success')
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)