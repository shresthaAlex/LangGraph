import aiosqlite
import bcrypt
from datetime import date

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

async def register_user(conn: aiosqlite.Connection, username: str, password: str) -> dict:
    async with conn.execute("SELECT username FROM users WHERE username=?", (username,)) as cursor:
        if await cursor.fetchone():
            return {"success": False, "error": "Username already exists"}
    
    await conn.execute(
        "INSERT INTO users (username, password_hash, ai_count, last_reset) VALUES (?, ?, 0, ?)",
        (username, hash_password(password), date.today())
    )
    await conn.commit()
    return {"success": True}

async def login_user(conn: aiosqlite.Connection, username: str, password: str) -> dict:
    async with conn.execute("SELECT password_hash, ai_count, last_reset FROM users WHERE username=?", (username,)) as cursor:
        row = await cursor.fetchone()
    
    if not row:
        return {"success": False, "error": "Username does not exist"}

    password_hash, ai_count, last_reset = row
    if not check_password(password, password_hash):
        return {"success": False, "error": "Incorrect password"}

    # Reset daily AI counter if new day
    if last_reset != str(date.today()):
        ai_count = 0
        await conn.execute("UPDATE users SET ai_count=0, last_reset=? WHERE username=?", (date.today(), username))
        await conn.commit()

    return {"success": True, "username": username, "ai_count": ai_count}
