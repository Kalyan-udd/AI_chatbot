import sqlite3
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

class DatabaseManipulation:
    def __init__(self) -> None:
        self.path = f"{ROOT}/src/data/Database.db"
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self)-> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions(
                    session_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages(
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                );
            """)

            conn.commit()

    def create_session(self, title:str = "New chat") -> str:
        session_id = str(uuid.uuid4())
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO sessions (session_id, title) VALUES (?,?);",(session_id,title))
            conn.commit()
        return f"Created session {session_id}"

    def save_message(self, session_id:str, role:str, content:str) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?);", (session_id, role, content))
            cursor.execute("UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?;",(session_id,))
            conn.commit()

    def load_messages(self,session_id:str)->list[dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role, content FROM messages WHERE session_id = ? ORDER BY timestamp ASC;", (session_id,))
            rows = cursor.fetchall()
        return [{"role":row[0], "content":row[1]} for row in rows]

    def get_all_sessions(self) -> list[dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT session_id, title, updated_at FROM sessions ORDER BY updated_at DESC;")
            rows = cursor.fetchall()
        return [{"session_id":row[0], "title":row[1], "updated_at":row[2]}for row in rows]


    def delete_session(self, session_id:str) -> str:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE session_id = ?;", (session_id,))
            conn.commit()
        return f"successfully Deleted the session {session_id}"
