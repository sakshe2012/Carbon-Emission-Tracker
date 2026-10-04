"""
Rewards & Notifications Blueprint
Manages citizen Green Points, levels, achievements, monthly challenges,
and the notification center alerts.
"""

from flask import Blueprint, jsonify, request, render_template, session
from utils.auth import require_login, require_auth_api
import json

rewards_bp = Blueprint('rewards', __name__, template_folder='../templates')

def get_db_cursor():
    from app import mysql
    return mysql.connection.cursor()

def get_db_connection():
    from app import mysql
    return mysql.connection

def add_notification(user_id, title, message, notif_type):
    """Utility to inject notifications into the DB."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO notifications (user_id, title, message, type)
            VALUES (%s, %s, %s, %s)
        """, (user_id, title, message, notif_type))
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"Error inserting notification: {e}")

def reward_green_points(user_id, points, reason):
    """
    Rewards green points to a user, logs to history, updates levels,
    and checks for badge unlock thresholds.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Check if user already has a reward profile
        cur.execute("SELECT id, green_points, level, badge_list FROM user_rewards WHERE user_id = %s", (user_id,))
        profile = cur.fetchone()
        
        if not profile:
            # Create profile
            cur.execute("""
                INSERT INTO user_rewards (user_id, green_points, level, badge_list)
                VALUES (%s, %s, 1, '[]')
            """, (user_id, points))
            conn.commit()
            
            # Fetch again
            cur.execute("SELECT id, green_points, level, badge_list FROM user_rewards WHERE user_id = %s", (user_id,))
            profile = cur.fetchone()
            
        reward_profile_id, current_points, current_level, badge_list_json = profile
        new_points = current_points + points
        
        # 2. Update level (1 level per 200 points)
        new_level = int(new_points / 200) + 1
        level_up = new_level > current_level
        
        # 3. Log to reward history
        cur.execute("""
            INSERT INTO reward_history (user_id, points_earned, reason)
            VALUES (%s, %s, %s)
        """, (user_id, points, reason))
        
        # 4. Check achievements/badges
        badges = json.loads(badge_list_json or '[]')
        new_badges = []
        
        # Rule criteria
        if new_points >= 50 and "Green Starter" not in badges:
            new_badges.append("Green Starter")
            add_notification(user_id, "Badge Unlocked! 🎉", "You've earned the 'Green Starter' badge for hitting 50 Green Points!", "achievement")
            
        if new_points >= 500 and "Eco Warrior" not in badges:
            new_badges.append("Eco Warrior")
            add_notification(user_id, "Badge Unlocked! 🏆", "Incredible! You've unlocked the 'Eco Warrior' badge for reaching 500 Green Points!", "achievement")
            
        # Get public transport count
        cur.execute("SELECT COUNT(*) FROM trips WHERE user_id = %s AND (LOWER(vehicle_type) LIKE '%bus%' OR LOWER(vehicle_type) LIKE '%rail%' OR LOWER(vehicle_type) LIKE '%train%' OR LOWER(vehicle_type) LIKE '%public%')", (user_id,))
        pub_count = cur.fetchone()[0]
        if pub_count >= 5 and "Public Transit Advocate" not in badges:
            new_badges.append("Public Transit Advocate")
            add_notification(user_id, "Badge Unlocked! 🚌", "You've earned the 'Public Transit Advocate' badge for using public transport 5 times!", "achievement")
            
        # Get EV vehicle count
        cur.execute("SELECT COUNT(*) FROM vehicles WHERE user_id = %s AND LOWER(fuel_type) = 'electric'", (user_id,))
        ev_count = cur.fetchone()[0]
        if ev_count >= 1 and "EV Pioneer" not in badges:
            new_badges.append("EV Pioneer")
            add_notification(user_id, "Badge Unlocked! ⚡", "You've unlocked the 'EV Pioneer' badge for registering an Electric Vehicle!", "achievement")

        badges.extend(new_badges)
        badge_list_updated = json.dumps(badges)
        
        # 5. Save changes
        cur.execute("""
            UPDATE user_rewards 
            SET green_points = %s, level = %s, badge_list = %s 
            WHERE user_id = %s
        """, (new_points, new_level, badge_list_updated, user_id))
        
        if level_up:
            add_notification(user_id, "Level Up! 🌟", f"Congratulations! You leveled up to Level {new_level}!", "level_up")
            
        conn.commit()
        cur.close()
        
    except Exception as e:
        print(f"Error updating rewards: {e}")

@rewards_bp.route('/rewards')
@require_login
def rewards_dashboard():
    """Renders the badges, points, and challenges UI."""
    user_id = session.get('user_id')
    try:
        cur = get_db_cursor()
        
        # 1. Fetch user reward profile
        cur.execute("SELECT green_points, level, badge_list FROM user_rewards WHERE user_id = %s", (user_id,))
        profile = cur.fetchone()
        
        if not profile:
            # Create dummy profile
            conn = get_db_connection()
            cur_init = conn.cursor()
            cur_init.execute("INSERT INTO user_rewards (user_id, green_points, level, badge_list) VALUES (%s, 0, 1, '[]')", (user_id,))
            conn.commit()
            cur_init.close()
            profile = (0, 1, '[]')
            
        points, level, badge_json = profile
        badges = json.loads(badge_json or '[]')
        
        # 2. Fetch rewards history
        cur.execute("SELECT points_earned, reason, created_at FROM reward_history WHERE user_id = %s ORDER BY created_at DESC LIMIT 10", (user_id,))
        history = cur.fetchall()
        history_list = []
        for h in history:
            history_list.append({
                'points': h[0],
                'reason': h[1],
                'date': h[2]
            })
            
        # 3. Monthly challenges
        challenges = [
            {'title': 'Commute Clean', 'desc': 'Log 5 trips using public transport or EV.', 'points': 100, 'progress': min(100, int((pub_count_query(user_id)/5)*100))},
            {'title': 'Smooth Operator', 'desc': 'Keep your Driving Eco Score above 85 for 3 consecutive trips.', 'points': 150, 'progress': 66},
            {'title': 'Active Tracker', 'desc': 'Reach a 7-day carbon tracking streak.', 'points': 75, 'progress': min(100, int((streak_query(user_id)/7)*100))}
        ]
        
        cur.close()
        return render_template('rewards.html', 
                               points=points, 
                               level=level, 
                               badges=badges, 
                               history=history_list,
                               challenges=challenges)
    except Exception as e:
        print(f"Rewards dashboard load error: {e}")
        return render_template('rewards.html', points=0, level=1, badges=[], history=[], challenges=[], error=str(e))

@rewards_bp.route('/api/notifications/list', methods=['GET'])
@require_auth_api
def list_notifications():
    """Lists recent notifications in the user tray."""
    user_id = session.get('user_id')
    try:
        cur = get_db_cursor()
        cur.execute("SELECT id, title, message, type, is_read, created_at FROM notifications WHERE user_id = %s ORDER BY created_at DESC LIMIT 20", (user_id,))
        rows = cur.fetchall()
        
        notifs = []
        for r in rows:
            notifs.append({
                'id': r[0],
                'title': r[1],
                'message': r[2],
                'type': r[3],
                'is_read': bool(r[4]),
                'date': r[5]
            })
        cur.close()
        return jsonify({'success': True, 'notifications': notifs})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rewards_bp.route('/api/notifications/read/<int:notif_id>', methods=['POST'])
@require_auth_api
def mark_read(notif_id):
    """Marks a notification as read."""
    user_id = session.get('user_id')
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE notifications SET is_read = 1 WHERE id = %s AND user_id = %s", (notif_id, user_id))
        conn.commit()
        cur.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rewards_bp.route('/api/notifications/unread_count', methods=['GET'])
@require_auth_api
def unread_count():
    """Returns the count of unread notifications."""
    user_id = session.get('user_id')
    try:
        cur = get_db_cursor()
        cur.execute("SELECT COUNT(*) FROM notifications WHERE user_id = %s AND is_read = 0", (user_id,))
        count = cur.fetchone()[0]
        cur.close()
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Helper queries
def pub_count_query(user_id):
    try:
        cur = get_db_cursor()
        cur.execute("SELECT COUNT(*) FROM trips WHERE user_id = %s AND (LOWER(vehicle_type) LIKE '%bus%' OR LOWER(vehicle_type) LIKE '%rail%' OR LOWER(vehicle_type) LIKE '%train%' OR LOWER(vehicle_type) LIKE '%public%')", (user_id,))
        count = cur.fetchone()[0]
        cur.close()
        return count
    except Exception:
        return 0

def streak_query(user_id):
    try:
        cur = get_db_cursor()
        cur.execute("SELECT current_streak FROM leaderboard WHERE user_id = %s", (user_id,))
        res = cur.fetchone()
        cur.close()
        return res[0] if res else 0
    except Exception:
        return 0
