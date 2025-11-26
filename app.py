#!/usr/bin/env python3
"""
ThaparGPT Flask API with Admin Panel & Password Reset
------------------------------------------------------
Admin credentials: username=admin, password=123
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime
import hashlib
import secrets

# Import your existing ThaparGpt logic
try:
    from ThaparGpt import init_assistant, chat, chat_with_image, chat_with_pdf, chat_with_file
except ImportError:
    print("ERROR: Cannot import ThaparGpt.py")
    exit(1)

app = Flask(__name__)
CORS(app)

# Admin credentials (fixed)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "123"

# Initialize database
def init_db():
    conn = sqlite3.connect('thapargpt.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  created_at TEXT,
                  last_login TEXT,
                  reset_token TEXT)''')
    
    # Chat history table
    c.execute('''CREATE TABLE IF NOT EXISTS chat_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  message TEXT,
                  response TEXT,
                  timestamp TEXT,
                  file_name TEXT,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    conn.commit()
    conn.close()

# Password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Initialize
print("Initializing ThaparGPT...")
init_db()
init_assistant()
print("ThaparGPT Ready! ✅")
print(f"Admin Login: {ADMIN_USERNAME} / {ADMIN_PASSWORD}")


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})


@app.route('/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400
        
        if len(password) < 4:
            return jsonify({"error": "Password must be at least 4 characters"}), 400
        
        # Block admin username for regular users
        if username.lower() == ADMIN_USERNAME:
            return jsonify({"error": "This username is reserved"}), 400
        
        conn = sqlite3.connect('thapargpt.db')
        c = conn.cursor()
        
        try:
            c.execute("INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)",
                     (username, hash_password(password), datetime.now().isoformat()))
            conn.commit()
            user_id = c.lastrowid
            conn.close()
            
            return jsonify({
                "success": True,
                "user_id": user_id,
                "username": username
            })
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({"error": "Username already exists"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/login', methods=['POST'])
def login():
    """Login user or admin"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400
        
        # Check if admin login
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            return jsonify({
                "success": True,
                "is_admin": True,
                "username": ADMIN_USERNAME
            })
        
        # Regular user login
        conn = sqlite3.connect('thapargpt.db')
        c = conn.cursor()
        c.execute("SELECT id, username FROM users WHERE username=? AND password=?",
                 (username, hash_password(password)))
        user = c.fetchone()
        
        if user:
            # Update last login
            c.execute("UPDATE users SET last_login=? WHERE id=?",
                     (datetime.now().isoformat(), user[0]))
            conn.commit()
            conn.close()
            
            return jsonify({
                "success": True,
                "is_admin": False,
                "user_id": user[0],
                "username": user[1]
            })
        else:
            conn.close()
            return jsonify({"error": "Invalid username or password"}), 401
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Generate password reset token"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        
        if not username:
            return jsonify({"error": "Username required"}), 400
        
        conn = sqlite3.connect('thapargpt.db')
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username=?", (username,))
        user = c.fetchone()
        
        if user:
            # Generate simple 6-digit reset code
            reset_token = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
            c.execute("UPDATE users SET reset_token=? WHERE id=?", (reset_token, user[0]))
            conn.commit()
            conn.close()
            
            return jsonify({
                "success": True,
                "reset_code": reset_token,
                "message": "Save this code to reset your password"
            })
        else:
            conn.close()
            return jsonify({"error": "Username not found"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password using token"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        reset_code = data.get('reset_code', '').strip()
        new_password = data.get('new_password', '').strip()
        
        if not username or not reset_code or not new_password:
            return jsonify({"error": "All fields required"}), 400
        
        if len(new_password) < 4:
            return jsonify({"error": "Password must be at least 4 characters"}), 400
        
        conn = sqlite3.connect('thapargpt.db')
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username=? AND reset_token=?",
                 (username, reset_code))
        user = c.fetchone()
        
        if user:
            c.execute("UPDATE users SET password=?, reset_token=NULL WHERE id=?",
                     (hash_password(new_password), user[0]))
            conn.commit()
            conn.close()
            
            return jsonify({
                "success": True,
                "message": "Password reset successful"
            })
        else:
            conn.close()
            return jsonify({"error": "Invalid username or reset code"}), 401
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/admin/users', methods=['GET'])
def admin_get_users():
    """Get all users (admin only)"""
    try:
        conn = sqlite3.connect('thapargpt.db')
        c = conn.cursor()
        c.execute("""SELECT id, username, created_at, last_login 
                     FROM users 
                     ORDER BY created_at DESC""")
        rows = c.fetchall()
        conn.close()
        
        users = []
        for row in rows:
            users.append({
                "id": row[0],
                "username": row[1],
                "created_at": row[2],
                "last_login": row[3]
            })
        
        return jsonify({"success": True, "users": users})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/admin/user-history', methods=['POST'])
def admin_get_user_history():
    """Get specific user's chat history (admin only)"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        conn = sqlite3.connect('thapargpt.db')
        c = conn.cursor()
        
        # Get user info
        c.execute("SELECT username FROM users WHERE id=?", (user_id,))
        user = c.fetchone()
        
        if not user:
            conn.close()
            return jsonify({"error": "User not found"}), 404
        
        # Get chat history
        c.execute("""SELECT message, response, timestamp, file_name 
                     FROM chat_history 
                     WHERE user_id=? 
                     ORDER BY timestamp DESC""", (user_id,))
        rows = c.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                "message": row[0],
                "response": row[1],
                "timestamp": row[2],
                "file_name": row[3]
            })
        
        return jsonify({
            "success": True,
            "username": user[0],
            "history": history
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/admin/delete-user', methods=['POST'])
def admin_delete_user():
    """Delete user and their chat history (admin only)"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        conn = sqlite3.connect('thapargpt.db')
        c = conn.cursor()
        
        # Delete chat history first
        c.execute("DELETE FROM chat_history WHERE user_id=?", (user_id,))
        
        # Delete user
        c.execute("DELETE FROM users WHERE id=?", (user_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "User and chat history deleted"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/admin/clear-history', methods=['POST'])
def admin_clear_history():
    """Clear specific user's chat history (admin only)"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        conn = sqlite3.connect('thapargpt.db')
        c = conn.cursor()
        c.execute("DELETE FROM chat_history WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Chat history cleared"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/history', methods=['POST'])
def get_history():
    """Get user's chat history"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        conn = sqlite3.connect('thapargpt.db')
        c = conn.cursor()
        c.execute("""SELECT message, response, timestamp, file_name 
                     FROM chat_history 
                     WHERE user_id=? 
                     ORDER BY timestamp ASC""", (user_id,))
        rows = c.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                "message": row[0],
                "response": row[1],
                "timestamp": row[2],
                "file_name": row[3]
            })
        
        return jsonify({"success": True, "history": history})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def save_to_history(user_id, message, response, file_name=None):
    """Save chat to database"""
    try:
        conn = sqlite3.connect('thapargpt.db')
        c = conn.cursor()
        c.execute("""INSERT INTO chat_history 
                     (user_id, message, response, timestamp, file_name) 
                     VALUES (?, ?, ?, ?, ?)""",
                 (user_id, message, response, datetime.now().isoformat(), file_name))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving history: {e}")


@app.route('/text', methods=['POST'])
def text_chat():
    """Text chat with history saving"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({"error": "Missing 'message' field"}), 400
        
        message = data['message']
        user_id = data.get('user_id')
        
        if not message.strip():
            return jsonify({"error": "Empty message"}), 400
        
        response = chat(message)
        
        if user_id:
            save_to_history(user_id, message, response)
        
        return jsonify({
            "success": True,
            "response": response
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/file', methods=['POST'])
def file_upload():
    """File upload with history saving"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        message = request.form.get('message', '')
        user_id = request.form.get('user_id')
        
        if file.filename == '':
            return jsonify({"error": "Empty filename"}), 400
        
        file_bytes = file.read()
        mime_type = file.content_type or 'application/octet-stream'
        
        if mime_type.startswith('image/'):
            response = chat_with_image(file_bytes, message, mime_type)
        elif mime_type == 'application/pdf':
            response = chat_with_pdf(file_bytes, message)
        else:
            response = chat_with_file(file_bytes, mime_type, message)
        
        if user_id:
            save_to_history(user_id, message or "File uploaded", response, file.filename)
        
        return jsonify({
            "success": True,
            "response": response
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)