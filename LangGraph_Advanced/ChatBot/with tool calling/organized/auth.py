import sqlite3
import bcrypt
from datetime import date

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def register_user(conn: sqlite3.Connection, username: str, password: str) -> dict:
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE username=?", (username,))
    if cursor.fetchone():
        return {"success": False, "error": "Username already exists"}
    
    cursor.execute(
        "INSERT INTO users (username, password_hash, ai_count, last_reset) VALUES (?, ?, 0, ?)",
        (username, hash_password(password), date.today())
    )
    conn.commit()
    return {"success": True}

def login_user(conn: sqlite3.Connection, username: str, password: str) -> dict:
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash, ai_count, last_reset FROM users WHERE username=?", (username,))
    row = cursor.fetchone()
    if not row:
        return {"success": False, "error": "Username does not exist"}

    password_hash, ai_count, last_reset = row
    if not check_password(password, password_hash):
        return {"success": False, "error": "Incorrect password"}

    # Reset daily AI counter if new day
    if last_reset != str(date.today()):
        ai_count = 0
        cursor.execute("UPDATE users SET ai_count=0, last_reset=? WHERE username=?", (date.today(), username))
        conn.commit()

    return {"success": True, "username": username, "ai_count": ai_count}
