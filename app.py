"""
Carbon Footprint Tracker - Main Flask Application
PHASE 1: Authentication & Core Routes
"""

from flask import Flask, render_template, request, redirect, session, jsonify
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import datetime
import os
import config

from utils.auth import (
    generate_jwt_token, verify_jwt_token, require_login, require_auth_api,
    get_current_user, validate_email, validate_password, validate_name,
    ValidationError
)
from utils.emission import load_emission_data, build_emission_map, calculate_co2, load_traffic_data, calculate_route_co2
from utils.route_optimizer import get_tomtom_routes, format_duration, calculate_fuel_consumption
from utils.recommendation import generate_recommendations
from utils.calculator import calculate_trip_details
from utils.smart_calculator import assess_vehicle_health
from utils.streaks_budget import get_monthly_emissions, update_user_streak


# Initialize traffic map globally
try:
    traffic_map = load_traffic_data()
except Exception as e:
    traffic_map = {'Default': 1.1}

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(config)
app.config['SESSION_COOKIE_SECURE'] = True if not config.DEBUG else False
app.config['PERMANENT_SESSION_LIFETIME'] = config.PERMANENT_SESSION_LIFETIME

# Initialize extensions
mysql = MySQL(app)
bcrypt = Bcrypt(app)
CORS(app)

# Register Blueprints for Advanced Features
from blueprints.rewards_notifications import rewards_bp, add_notification, reward_green_points
from utils.anomaly_detector import detect_trip_anomaly
from utils.eco_coach import compute_eco_score

app.register_blueprint(rewards_bp)

# Load emission data
try:
    df = load_emission_data()
    emission_map = build_emission_map(df)
    print("✓ Emission data loaded successfully")
except Exception as e:
    print(f"⚠ Error loading emission data: {e}")
    emission_map = {
        "car": 0.19,
        "bus": 0.075,
        "bike": 0.05,
        "2wheeler": 0.05,
        "flight": 0.255
    }

# ============================================================================
# PHASE 1: AUTHENTICATION ROUTES
# ============================================================================

@app.route('/')
def home():
    """Home page - redirect to dashboard if logged in, else to login"""
    if session.get('token') and verify_jwt_token(session['token']):
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration endpoint"""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            city = request.form.get('city', 'Unknown').strip()
            
            # Validate inputs
            validate_name(name)
            validate_email(email)
            validate_password(password)
            
            if password != confirm_password:
                cities = ['Delhi', 'Mumbai', 'Bangalore', 'Hyderabad', 'Pune', 'Kolkata', 'Chennai', 'Other']
                return render_template('register.html', error="Passwords do not match", cities=cities)
            
            # Check if user already exists
            cur = mysql.connection.cursor()
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                cur.close()
                cities = ['Delhi', 'Mumbai', 'Bangalore', 'Hyderabad', 'Pune', 'Kolkata', 'Chennai', 'Other']
                return render_template('register.html', error="Email already registered", cities=cities)
            
            # Hash password with bcrypt (12 rounds)
            hashed_password = bcrypt.generate_password_hash(password, rounds=12).decode('utf-8')
            
            # Insert user
            cur.execute(
                "INSERT INTO users (name, email, password, city) VALUES (%s, %s, %s, %s)",
                (name, email, hashed_password, city)
            )
            mysql.connection.commit()
            user_id = cur.lastrowid
            cur.close()
            
            # Create leaderboard entry
            cur = mysql.connection.cursor()
            cur.execute(
                "INSERT INTO leaderboard (user_id, city, total_distance, total_co2, trips_count) VALUES (%s, %s, 0, 0, 0)",
                (user_id, city)
            )
            mysql.connection.commit()
            cur.close()
            
            print(f"✓ User registered: {email}")
            return redirect('/login')
            
        except ValidationError as e:
            cities = ['Delhi', 'Mumbai', 'Bangalore', 'Hyderabad', 'Pune', 'Kolkata', 'Chennai', 'Other']
            return render_template('register.html', error=str(e), cities=cities)
        except Exception as e:
            print(f"✗ Registration error: {e}")
            cities = ['Delhi', 'Mumbai', 'Bangalore', 'Hyderabad', 'Pune', 'Kolkata', 'Chennai', 'Other']
            return render_template('register.html', error="Registration failed. Please try again.", cities=cities)
    
    # GET request - show registration form
    cities = ['Delhi', 'Mumbai', 'Bangalore', 'Hyderabad', 'Pune', 'Kolkata', 'Chennai', 'Other']
    return render_template('register.html', cities=cities)
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login endpoint"""
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            remember_me = request.form.get('remember_me') == 'on'
            
            if not email or not password:
                return render_template('login.html', error="Email and password required")
            
            # Find user
            cur = mysql.connection.cursor()
            cur.execute(
                "SELECT id, name, email, password, city FROM users WHERE email = %s",
                (email,)
            )
            user = cur.fetchone()
            cur.close()
            
            # Verify password
            if user and bcrypt.check_password_hash(user[3], password):
                # Generate JWT token
                token = generate_jwt_token(user[0], remember_me=remember_me)
                session['token'] = token
                session['user_id'] = user[0]
                session['user_name'] = user[1]
                session['user_city'] = user[4]
                
                # Fetch streak for session
                cur = mysql.connection.cursor()
                cur.execute("SELECT current_streak FROM leaderboard WHERE user_id = %s", (user[0],))
                streak_row = cur.fetchone()
                cur.close()
                session['current_streak'] = streak_row[0] if streak_row else 0
                
                print(f"✓ User logged in: {email}")
                return redirect('/dashboard')
            else:
                return render_template('login.html', error="Invalid email or password")
                
        except Exception as e:
            print(f"✗ Login error: {e}")
            return render_template('login.html', error="Login failed. Please try again.")
    
    # GET request - show login form
    return render_template('login.html')
@app.route('/logout')
def logout():
    """Logout endpoint - clear session"""
    session.clear()
    return redirect('/login')

@app.route('/dashboard')
@require_login
def dashboard():
    """Main dashboard - shows user stats and recent trips"""
    try:
        user_id = get_current_user()
        if not user_id:
            return redirect('/login')
        
        cur = mysql.connection.cursor()
        
        # Get user info
        cur.execute("SELECT name, email, city, co2_monthly_budget FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        co2_monthly_budget = user[3] if user and len(user) > 3 and user[3] is not None else None
        
        # Get user stats from leaderboard
        cur.execute(
            """SELECT total_distance, total_co2, trips_count, 
                      (SELECT COUNT(*) + 1 FROM leaderboard l2 WHERE l2.city = l.city AND l2.total_co2 < l.total_co2) as `rank`, 
                      current_streak, max_streak 
               FROM leaderboard l 
               WHERE user_id = %s""",
            (user_id,)
        )
        stats = cur.fetchone()
        total_distance = stats[0] if stats else 0
        total_co2 = stats[1] if stats else 0
        trips_count = stats[2] if stats else 0
        rank = stats[3] if stats else None
        current_streak = stats[4] if stats else 0
        max_streak = stats[5] if stats else 0
        
        # Get current month emissions
        monthly_co2 = get_monthly_emissions(cur, user_id)
        
        # Get recent trips
        cur.execute(
            "SELECT id, vehicle_type, distance, co2_emissions, created_at FROM trips WHERE user_id = %s ORDER BY created_at DESC LIMIT 5",
            (user_id,)
        )
        recent_trips = cur.fetchall()
        
        # Get recent daily entries
        cur.execute(
            "SELECT date, vehicle_type, distance, co2_emissions FROM daily_entries WHERE user_id = %s ORDER BY date DESC LIMIT 5",
            (user_id,)
        )
        recent_entries = cur.fetchall()
        
        cur.close()
        
        return render_template(
            'dashboard.html',
            user_name=user[0] if user else "User",
            user_city=user[2] if user else "Unknown",
            total_distance=round(total_distance, 2),
            total_co2=round(total_co2, 3),
            trips_count=trips_count,
            rank=rank,
            recent_trips=recent_trips,
            recent_entries=recent_entries,
            co2_monthly_budget=round(co2_monthly_budget, 1) if co2_monthly_budget is not None else None,
            current_streak=current_streak,
            max_streak=max_streak,
            monthly_co2=round(monthly_co2, 3)
        )
        
    except Exception as e:
        print(f"✗ Dashboard error: {e}")
        import traceback
        traceback.print_exc()
        return redirect('/login')

@app.route('/settings', methods=['GET', 'POST'])
@require_login
def settings():
    """User profile and budget settings"""
    user_id = get_current_user()
    if not user_id:
        return redirect('/login')

    cur = mysql.connection.cursor()
    
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            city = request.form.get('city', '').strip()
            budget_str = request.form.get('co2_monthly_budget', '').strip()
            
            cities = ['Delhi', 'Mumbai', 'Bangalore', 'Hyderabad', 'Pune', 'Kolkata', 'Chennai', 'Other']
            
            if not name:
                cur.close()
                return render_template('settings.html', error="Name cannot be empty", name=name, city=city, budget=budget_str, cities=cities)
                
            if budget_str == "":
                budget = None
            else:
                try:
                    budget = float(budget_str)
                    if budget <= 0:
                        raise ValueError()
                except ValueError:
                    cur.close()
                    return render_template('settings.html', error="Carbon budget must be greater than 0", name=name, city=city, budget=budget_str, cities=cities)

            # Update users table
            cur.execute(
                """UPDATE users 
                   SET name = %s, city = %s, co2_monthly_budget = %s 
                   WHERE id = %s""",
                (name, city, budget, user_id)
            )
            
            # Update leaderboard city as well for ranking correctness
            cur.execute(
                """UPDATE leaderboard 
                   SET city = %s 
                   WHERE user_id = %s""",
                (city, user_id)
            )
            
            mysql.connection.commit()
            session['user_name'] = name
            session['user_city'] = city
            
            cur.close()
            return render_template('settings.html', success="Settings updated successfully!", name=name, city=city, budget=budget_str, cities=cities)
            
        except Exception as e:
            print(f"✗ Settings update error: {e}")
            cur.close()
            cities = ['Delhi', 'Mumbai', 'Bangalore', 'Hyderabad', 'Pune', 'Kolkata', 'Chennai', 'Other']
            return render_template('settings.html', error="Failed to update settings. Please try again.", name='', city='', budget='', cities=cities)
            
    # GET request - load user info
    cur.execute("SELECT name, city, co2_monthly_budget FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    
    cities = ['Delhi', 'Mumbai', 'Bangalore', 'Hyderabad', 'Pune', 'Kolkata', 'Chennai', 'Other']
    
    return render_template(
        'settings.html',
        name=user[0] if user else "",
        city=user[1] if user else "",
        budget=round(user[2], 1) if user and user[2] is not None else "",
        cities=cities
    )


@app.route('/daily_entry', methods=['GET', 'POST'])
@require_login
def daily_entry():
    """Manual entry for daily travel"""
    user_id = get_current_user()
    if not user_id:
        return redirect('/login')

    if request.method == 'POST':
        try:
            date_str = request.form.get('date')
            vehicle_type = request.form.get('vehicle_type')
            distance = float(request.form.get('distance', 0))
            notes = request.form.get('notes', '')

            if distance <= 0:
                return render_template('daily_input.html', error="Distance must be greater than 0")

            # Calculate CO2 using Smart Assessment
            data_form = request.form.to_dict()
            data_form['distance'] = distance
            data_form['vehicle_type'] = vehicle_type
            
            result = assess_vehicle_health(data_form)
            co2 = result['adjusted_co2']

            # 1. Run Anomaly / Fraud Detection
            is_anomaly, anomaly_reason = detect_trip_anomaly(user_id, {
                'distance': distance,
                'idle_time_mins': result['idle_time_mins'],
                'co2_emissions': co2
            })

            vehicle_id = None

            cur = mysql.connection.cursor()
            
            # Insert entry
            cur.execute(
                """INSERT INTO daily_entries (
                    user_id, date, vehicle_type, vehicle_model, vehicle_age,
                    seating_capacity, transmission, ac_usage, traffic_conditions,
                    idle_time_mins, last_service_months, tire_condition, engine_health,
                    health_score, efficiency_score, sustainability_rating,
                    distance, co2_emissions, notes
                   )
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (user_id, date_str, vehicle_type, result['vehicle_model'], result['vehicle_age'],
                 result['seating_capacity'], result['transmission'], result['ac_usage'], result['traffic_conditions'],
                 result['idle_time_mins'], result['last_service_months'], result['tire_condition'], result['engine_health'],
                 result['health_score'], result['efficiency_score'], result['sustainability_rating'],
                 distance, co2, notes)
            )
            
            # Update leaderboard
            cur.execute(
                """UPDATE leaderboard
                   SET total_distance = total_distance + %s,
                       total_co2 = total_co2 + %s,
                       trips_count = trips_count + 1
                   WHERE user_id = %s""",
                (distance, co2, user_id)
            )
            
            # Update user streak
            session['current_streak'] = update_user_streak(cur, user_id)
            
            # 3. Award Green Points & Badges
            if not is_anomaly:
                points_earned = 10
                reasons = ["Logging daily commute footprint"]
                
                if co2 < 5.0:
                    points_earned += 20
                    reasons.append("keeping emissions under 5kg CO2")
                if vehicle_type in ['electric', 'bus', 'bike', '2wheeler']:
                    points_earned += 15
                    reasons.append("using low-carbon transit mode")
                    
                reward_green_points(user_id, points_earned, " & ".join(reasons))
            else:
                add_notification(user_id, "Daily Log Flagged ⚠️", f"Your logged daily entry on {date_str} was flagged: {anomaly_reason}", "anomaly")
            
            mysql.connection.commit()
            cur.close()
            
            print(f"✓ Daily entry saved: {user_id} - {date_str} - {co2:.3f}kg CO2")
            return redirect('/dashboard')
            
        except Exception as e:
            print(f"✗ Daily entry error: {e}")
            return render_template('daily_input.html', error="Failed to save entry.")

    # Fetch history for GET request
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT date, vehicle_type, distance, co2_emissions, notes FROM daily_entries WHERE user_id = %s ORDER BY date DESC",
        (user_id,)
    )
    history = cur.fetchall()
    cur.close()

    return render_template('daily_input.html', history=history)

@app.route('/live_tracking')
@require_login
def live_tracking():
    """Live GPS tracking interface"""
    user_id = get_current_user()
    if not user_id:
        return redirect('/login')
        
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT start_location, end_location, vehicle_type, distance, co2_emissions, DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i') as time FROM trips WHERE user_id = %s ORDER BY created_at DESC",
        (user_id,)
    )
    history = cur.fetchall()
    cur.close()
    
    return render_template('live_tracking.html', history=history)

@app.route('/route_optimizer')
@require_login
def route_optimizer():
    """Route optimizer interface"""
    user_id = get_current_user()
    if not user_id:
        return redirect('/login')
        
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT source, destination, vehicle_type, route_option_1_distance, route_option_1_co2, DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i') as time FROM routes WHERE user_id = %s ORDER BY created_at DESC",
        (user_id,)
    )
    history = cur.fetchall()
    cur.close()
    
    return render_template('route_optimizer.html', history=history)

@app.route('/recommendations')
@require_login
def recommendations():
    """Smart recommendation engine"""
    user_id = get_current_user()
    if not user_id:
        return redirect('/login')
        
    cur = mysql.connection.cursor()
    
    # Get recent trips
    cur.execute("SELECT distance, vehicle_type FROM trips WHERE user_id = %s ORDER BY created_at DESC LIMIT 20", (user_id,))
    recent_trips = cur.fetchall()
    
    # Get recent entries
    cur.execute("SELECT distance, vehicle_type FROM daily_entries WHERE user_id = %s ORDER BY created_at DESC LIMIT 20", (user_id,))
    recent_entries = cur.fetchall()
    
    cur.close()
    
    recs = generate_recommendations(recent_trips, recent_entries)
    
    return render_template('recommendation.html', recommendations=recs)



@app.route('/api/calculate_routes', methods=['POST'])
@require_auth_api
def calculate_routes():
    """Calculate routes via TomTom API and compute CO2"""
    try:
        data = request.get_json()
        src = data.get('src')
        dest = data.get('dest')
        vehicle = data.get('vehicle', 'car')
        
        if not src or not dest:
            return jsonify({'error': 'Missing source or destination'}), 400
        
        # Get routes from TomTom (or OSRM fallback)
        routes_data = get_tomtom_routes(src['lon'], src['lat'], dest['lon'], dest['lat'], vehicle)
        
        if not routes_data:
            return jsonify({'error': 'No routes found'}), 404
        
        # Format routes with CO2 and fuel consumption
        formatted_routes = []
        
        for idx, route in enumerate(routes_data):
            dist_km = route.get('distance', 0)
            duration_sec = route.get('duration', 0)
            geometry = route.get('geometry', {}).get('coordinates', [])
            fuel_liters = route.get('fuel_consumption', 0)
            
            # Calculate fuel consumption if not provided
            if fuel_liters <= 0:
                fuel_liters = calculate_fuel_consumption(dist_km, vehicle)
            
            # Calculate CO2 emissions
            # Using emission factor × distance (in kg CO2)
            emission_factor = emission_map.get(vehicle.lower(), 0.19)
            
            # Apply traffic factor if available
            area = dest.get('name', 'Default')
            traffic_factor = traffic_map.get(area, 1.0)
            
            co2 = calculate_route_co2(dist_km, vehicle, emission_map, traffic_map, area)
            
            formatted_routes.append({
                'id': idx,
                'distance': round(dist_km, 2),
                'duration': duration_sec,
                'duration_text': format_duration(duration_sec),
                'co2': round(co2, 3),
                'fuel': round(fuel_liters, 2),
                'geometry': geometry,
                'is_eco': idx == 0,  # Best route (first = lowest CO2)
                'emission_factor': emission_factor,
                'traffic_factor': round(traffic_factor, 2)
            })
        
        # Sort routes by lowest CO2 (best eco-friendly first)
        formatted_routes = sorted(formatted_routes, key=lambda x: x['co2'])
        
        # Update IDs after sorting
        for idx, route in enumerate(formatted_routes):
            route['id'] = idx
            route['is_eco'] = (idx == 0)
        
        print(f"✓ Routes calculated: {len(formatted_routes)} routes, best CO2: {formatted_routes[0]['co2']} kg")
        
        return jsonify({
            'status': 'success',
            'routes': formatted_routes,
            'source': src.get('name', 'Unknown'),
            'destination': dest.get('name', 'Unknown'),
            'vehicle': vehicle
        })
        
    except Exception as e:
        print(f"✗ Calculate routes error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/save_route', methods=['POST'])
@require_auth_api
def save_route():
    """Save an optimized route to history"""
    try:
        user_id = get_current_user()
        data = request.get_json()
        
        cur = mysql.connection.cursor()
        # simplified save to routes table (assuming route_option_1 holds the selected route for now)
        cur.execute(
            """INSERT INTO routes (user_id, source, destination, vehicle_type, selected_route, city,
                                   route_option_1_distance, route_option_1_co2, route_option_1_time)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (user_id, data.get('source'), data.get('destination'), data.get('vehicle'), 
             1, session.get('user_city', 'Unknown'), data.get('distance'), data.get('co2'), data.get('duration'))
        )
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"✗ Route save error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/save_live_trip', methods=['POST'])
@require_auth_api
def save_live_trip():
    """Save a live trip from geolocation tracking"""
    try:
        data_req = request.get_json()
        distance = float(data_req.get('distance', 0))
        vehicle = data_req.get('vehicle', 'car').lower()
        
        if distance <= 0:
            return jsonify({'status': 'error', 'message': 'Invalid distance'}), 400
        
        # Run smart assessment
        data_req['distance'] = distance
        data_req['vehicle_type'] = vehicle
        
        result = assess_vehicle_health(data_req)
        co2 = result['adjusted_co2']
        
        user_id = get_current_user()
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
        
        # 1. Run AI Eco Driving Coach Scorer
        eco_score, eco_feedback = compute_eco_score({
            'vehicle_type': vehicle,
            'vehicle_age': result['vehicle_age'],
            'ac_usage': result['ac_usage'],
            'traffic_conditions': result['traffic_conditions'],
            'idle_time_mins': result['idle_time_mins'],
            'last_service_months': result['last_service_months'],
            'tire_condition': result['tire_condition'],
            'engine_health': result['engine_health']
        })
        eco_feedback_str = "\n".join(eco_feedback)

        # 2. Run Anomaly / Fraud Detection
        is_anomaly, anomaly_reason = detect_trip_anomaly(user_id, {
            'distance': distance,
            'idle_time_mins': result['idle_time_mins'],
            'co2_emissions': co2
        })
        is_anomaly_val = 1 if is_anomaly else 0

        vehicle_id = None

        # Save trip
        cur = mysql.connection.cursor()
        cur.execute(
            """INSERT INTO trips (
                user_id, start_location, end_location, vehicle_type, vehicle_model, vehicle_age,
                seating_capacity, transmission, ac_usage, traffic_conditions, idle_time_mins,
                last_service_months, tire_condition, engine_health, health_score, efficiency_score,
                sustainability_rating, distance, co2_emissions, city,
                driving_efficiency_score, coach_feedback, is_anomaly, anomaly_reason, vehicle_id
               )
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (user_id, data_req.get('start_location', 'Unknown'), data_req.get('end_location', 'Unknown'),
             vehicle, result['vehicle_model'], result['vehicle_age'], result['seating_capacity'],
             result['transmission'], result['ac_usage'], result['traffic_conditions'], result['idle_time_mins'],
             result['last_service_months'], result['tire_condition'], result['engine_health'],
             result['health_score'], result['efficiency_score'], result['sustainability_rating'],
             distance, co2, session.get('user_city', 'Unknown'),
             eco_score, eco_feedback_str, is_anomaly_val, anomaly_reason, vehicle_id)
        )
        mysql.connection.commit()
        
        # Update leaderboard
        cur.execute(
            """UPDATE leaderboard
               SET total_distance = total_distance + %s,
                   total_co2 = total_co2 + %s,
                   trips_count = trips_count + 1
               WHERE user_id = %s""",
            (distance, co2, user_id)
        )
        
        # Update user streak
        session['current_streak'] = update_user_streak(cur, user_id)
        
        # 4. Award Green Points & Badges
        if not is_anomaly:
            points_earned = 10
            reasons = ["Logging active travel trip"]
            
            if co2 < 5.0:
                points_earned += 20
                reasons.append("keeping trip emissions under 5kg CO2")
            if vehicle in ['electric', 'bus', 'bike', '2wheeler']:
                points_earned += 15
                reasons.append("using low-carbon/EV transit mode")
                
            reward_green_points(user_id, points_earned, " & ".join(reasons))
        else:
            add_notification(user_id, "Suspicious Activity Detected ⚠️", f"Your recent trip of {distance}km was flagged for: {anomaly_reason}", "anomaly")
            
        mysql.connection.commit()
        cur.close()
        
        print(f"✓ Trip saved: {user_id} - {distance}km - {co2:.3f}kg CO2")
        
        return jsonify({
            'status': 'saved',
            'co2': round(co2, 3),
            'distance': round(distance, 2)
        })
        
    except Exception as e:
        print(f"✗ Save trip error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400

# ============================================================================
# CALCULATOR ROUTES
# ============================================================================

@app.route('/calculator')
@require_login
def calculator():
    """Calculator interface for Fuel + CO2 Emissions"""
    return render_template('calculator.html')

@app.route('/api/calculate_trip', methods=['POST'])
@require_auth_api
def calculate_trip():
    """API to calculate trip details and save to history"""
    try:
        data = request.get_json()
        distance = float(data.get('distance', 0))
        vehicle_type = data.get('vehicle_type', '')
        
        if distance <= 0 or not vehicle_type:
            return jsonify({'status': 'error', 'message': 'Invalid input data'}), 400
            
        # Calculate using Pandas
        result = calculate_trip_details(distance, vehicle_type)
        
        user_id = get_current_user()
        
        # Save to database
        cur = mysql.connection.cursor()
        cur.execute(
            """INSERT INTO trip_history 
               (user_id, distance, vehicle_type, mileage, fuel_required, fuel_cost, co2_generated)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (user_id, result['distance'], result['vehicle_type'], result['mileage_used'], 
             result['fuel_required'], result['fuel_cost'], result['co2_generated'])
        )
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'status': 'success', 'data': result})
        
    except Exception as e:
        print(f"✗ Calculate trip error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/trip_history', methods=['GET'])
@require_auth_api
def get_trip_history():
    """API to get user's trip history"""
    try:
        user_id = get_current_user()
        
        cur = mysql.connection.cursor()
        cur.execute(
            """SELECT id, distance, vehicle_type, fuel_required, fuel_cost, co2_generated, DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i:%%s') as date
               FROM trip_history 
               WHERE user_id = %s 
               ORDER BY created_at DESC""",
            (user_id,)
        )
        
        columns = [desc[0] for desc in cur.description]
        history = [dict(zip(columns, row)) for row in cur.fetchall()]
        cur.close()
        
        return jsonify({'status': 'success', 'data': history})
        
    except Exception as e:
        print(f"✗ Get history error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/trip_history/<int:trip_id>', methods=['DELETE'])
@require_auth_api
def delete_trip_history(trip_id):
    """API to delete a specific trip history record"""
    try:
        user_id = get_current_user()
        
        cur = mysql.connection.cursor()
        cur.execute(
            "DELETE FROM trip_history WHERE id = %s AND user_id = %s",
            (trip_id, user_id)
        )
        mysql.connection.commit()
        
        if cur.rowcount == 0:
            cur.close()
            return jsonify({'status': 'error', 'message': 'Record not found'}), 404
            
        cur.close()
        return jsonify({'status': 'success', 'message': 'Record deleted'})
        
    except Exception as e:
        print(f"✗ Delete history error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# SMART ASSESSMENTS ROUTES
# ============================================================================

@app.route('/api/smart_assess', methods=['POST'])
@require_auth_api
def smart_assess():
    """API to run comprehensive vehicle health assessment and save to history"""
    try:
        data = request.get_json()
        
        # Run AI-style assessment
        result = assess_vehicle_health(data)
        
        user_id = get_current_user()
        
        # Save to database
        cur = mysql.connection.cursor()
        cur.execute(
            """INSERT INTO smart_assessments 
               (user_id, distance, vehicle_type, vehicle_model, vehicle_age, fuel_type, engine_cc,
                seating_capacity, transmission, ac_usage, driving_type, traffic_conditions,
                idle_time_mins, last_service_months, tire_condition, engine_health,
                base_mileage, custom_mileage, health_score, efficiency_score, sustainability_rating,
                base_co2, adjusted_co2, emission_increase_percent, fuel_required, fuel_cost, recommendation_text)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (user_id, result['distance'], result['vehicle_type'], result['vehicle_model'], result['vehicle_age'],
             result['fuel_type'], result['engine_cc'], result['seating_capacity'], result['transmission'],
             result['ac_usage'], result['driving_type'], result['traffic_conditions'], result['idle_time_mins'],
             result['last_service_months'], result['tire_condition'], result['engine_health'],
             result['base_mileage'], result['custom_mileage'], result['health_score'], result['efficiency_score'],
             result['sustainability_rating'], result['base_co2'], result['adjusted_co2'],
             result['emission_increase_percent'], result['fuel_required'], result['fuel_cost'], result['recommendation_text'])
        )
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'status': 'success', 'data': result})
        
    except Exception as e:
        print(f"✗ Smart assess error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/smart_history', methods=['GET'])
@require_auth_api
def get_smart_history():
    """API to get user's smart assessment history"""
    try:
        user_id = get_current_user()
        
        cur = mysql.connection.cursor()
        cur.execute(
            """SELECT id, distance, vehicle_type, vehicle_model, health_score, efficiency_score, 
                      sustainability_rating, adjusted_co2, fuel_cost, DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i:%%s') as date
               FROM smart_assessments 
               WHERE user_id = %s 
               ORDER BY created_at DESC""",
            (user_id,)
        )
        
        columns = [desc[0] for desc in cur.description]
        history = [dict(zip(columns, row)) for row in cur.fetchall()]
        cur.close()
        
        return jsonify({'status': 'success', 'data': history})
        
    except Exception as e:
        print(f"✗ Get smart history error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/smart_history/<int:assess_id>', methods=['DELETE'])
@require_auth_api
def delete_smart_history(assess_id):
    """API to delete a smart assessment record"""
    try:
        user_id = get_current_user()
        
        cur = mysql.connection.cursor()
        cur.execute(
            "DELETE FROM smart_assessments WHERE id = %s AND user_id = %s",
            (assess_id, user_id)
        )
        mysql.connection.commit()
        
        if cur.rowcount == 0:
            return jsonify({'status': 'error', 'message': 'Record not found'}), 404
            
        return jsonify({'status': 'success', 'message': 'Record deleted'})
        
    except Exception as e:
        print(f"✗ Delete smart history error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/smart_analytics', methods=['GET'])
@require_auth_api
def get_smart_analytics():
    """API to get analytics for Smart Assessment dashboard"""
    try:
        user_id = get_current_user()
        cur = mysql.connection.cursor()
        
        # 1. Age vs CO2 (Scatter)
        cur.execute("SELECT vehicle_age, adjusted_co2, vehicle_model FROM smart_assessments WHERE user_id = %s", (user_id,))
        age_data = cur.fetchall()
        
        # 2. Maintenance Impact (Pie - count of sustainability ratings)
        cur.execute("SELECT sustainability_rating, COUNT(*) as cnt FROM smart_assessments WHERE user_id = %s GROUP BY sustainability_rating", (user_id,))
        rating_data = cur.fetchall()
        
        # 3. Mileage vs Fuel (Bar)
        cur.execute("SELECT vehicle_model, custom_mileage, base_mileage, fuel_required FROM smart_assessments WHERE user_id = %s ORDER BY created_at DESC LIMIT 10", (user_id,))
        mileage_data = cur.fetchall()
        
        # 4. Vehicle Pollution (Bar - avg adjusted CO2 by vehicle type)
        cur.execute("SELECT vehicle_type, AVG(adjusted_co2) as avg_co2 FROM smart_assessments WHERE user_id = %s GROUP BY vehicle_type", (user_id,))
        pollution_data = cur.fetchall()
        
        cur.close()
        
        return jsonify({
            'status': 'success',
            'data': {
                'age_vs_co2': {
                    'ages': [row[0] for row in age_data],
                    'co2': [row[1] for row in age_data],
                    'models': [row[2] for row in age_data]
                },
                'maintenance_impact': {
                    'ratings': [row[0] for row in rating_data],
                    'counts': [row[1] for row in rating_data]
                },
                'mileage_vs_fuel': {
                    'models': [row[0] for row in mileage_data],
                    'custom_mileages': [row[1] for row in mileage_data],
                    'fuel_required': [row[3] for row in mileage_data]
                },
                'vehicle_pollution': {
                    'types': [row[0] for row in pollution_data],
                    'avg_co2': [float(row[1]) for row in pollution_data]
                }
            }
        })
        
    except Exception as e:
        print(f"✗ Smart Analytics error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/calculator_analytics', methods=['GET'])
@require_auth_api
def get_calculator_analytics():
    """API to get aggregated data for Plotly charts"""
    try:
        user_id = get_current_user()
        
        cur = mysql.connection.cursor()
        
        # Monthly fuel usage & CO2
        cur.execute(
            """SELECT DATE_FORMAT(created_at, '%%Y-%%m') as month, 
                      SUM(fuel_required) as total_fuel,
                      SUM(co2_generated) as total_co2,
                      SUM(fuel_cost) as total_cost
               FROM trip_history 
               WHERE user_id = %s 
               GROUP BY month 
               ORDER BY month ASC LIMIT 12""",
            (user_id,)
        )
        monthly_data = cur.fetchall()
        
        # Vehicle-wise emissions
        cur.execute(
            """SELECT vehicle_type, SUM(co2_generated) as total_co2, COUNT(id) as trip_count
               FROM trip_history 
               WHERE user_id = %s 
               GROUP BY vehicle_type""",
            (user_id,)
        )
        vehicle_data = cur.fetchall()
        
        cur.close()
        
        # Format for Plotly
        months = [row[0] for row in monthly_data]
        fuel_usage = [float(row[1]) for row in monthly_data]
        co2_monthly = [float(row[2]) for row in monthly_data]
        cost_monthly = [float(row[3]) for row in monthly_data]
        
        vehicles = [row[0] for row in vehicle_data]
        co2_by_vehicle = [float(row[1]) for row in vehicle_data]
        
        return jsonify({
            'status': 'success', 
            'data': {
                'monthly': {
                    'months': months,
                    'fuel': fuel_usage,
                    'co2': co2_monthly,
                    'cost': cost_monthly
                },
                'vehicle': {
                    'types': vehicles,
                    'co2': co2_by_vehicle
                }
            }
        })
        
    except Exception as e:
        print(f"✗ Analytics error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# ERROR HANDLERS & UTILITY ROUTES
# ============================================================================

@app.errorhandler(404)
def page_not_found(e):
    """404 error page"""
    return render_template('error.html', error_code=404, message="Page not found"), 404

@app.errorhandler(500)
def internal_error(e):
    """500 error page"""
    return render_template('error.html', error_code=500, message="Internal server error"), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.datetime.utcnow().isoformat()})

# ============================================================================
# LEADERBOARD ROUTE
# ============================================================================

@app.route('/leaderboard')
def leaderboard():
    """Public leaderboard page"""
    try:
        # Get city filter
        city = request.args.get('city', 'All')
        
        cur = mysql.connection.cursor()
        
        if city != 'All':
            cur.execute(
                """SELECT (SELECT COUNT(*) + 1 FROM leaderboard l2 WHERE l2.city = l.city AND l2.total_co2 < l.total_co2) as `rank`, 
                          u.name, u.city, l.total_distance, l.total_co2, l.trips_count
                   FROM leaderboard l
                   JOIN users u ON l.user_id = u.id
                   WHERE u.city = %s
                   ORDER BY l.total_co2 ASC
                   LIMIT 100""",
                (city,)
            )
        else:
            cur.execute(
                """SELECT (SELECT COUNT(*) + 1 FROM leaderboard l2 WHERE l2.total_co2 < l.total_co2) as `rank`, 
                          u.name, u.city, l.total_distance, l.total_co2, l.trips_count
                   FROM leaderboard l
                   JOIN users u ON l.user_id = u.id
                   ORDER BY l.total_co2 ASC
                   LIMIT 100"""
            )
        
        leaderboard_data = cur.fetchall()
        
        # Get unique cities
        cur.execute("SELECT DISTINCT city FROM users ORDER BY city")
        cities = [row[0] for row in cur.fetchall()]
        
        cur.close()
        
        return render_template('leaderboard.html', 
                             leaderboard=leaderboard_data,
                             cities=cities,
                             selected_city=city)
        
    except Exception as e:
        print(f"✗ Leaderboard error: {e}")
        return render_template('leaderboard.html', leaderboard=[], cities=[])

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("Carbon Footprint Tracker - Starting Server")
    print("=" * 60)
    
    # Run Database Migrations
    try:
        from scripts.migrate_phase1 import run_migration
        run_migration()
    except Exception as e:
        print(f"⚠ Migration run error on startup: {e}")
        
    print(f"Debug Mode: {config.DEBUG}")
    print(f"Database: {config.MYSQL_DB}@{config.MYSQL_HOST}")
    port = int(os.getenv('PORT', 5001))
    print(f"Server: http://localhost:{port}")
    print("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=config.DEBUG
    )


 