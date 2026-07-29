import sqlite3
from datetime import datetime
from pathlib import Path


class ProfileManager:

    def __init__(self, db_path="data/herbokolog.db"):

        Path("data").mkdir(exist_ok=True)

        self.conn = sqlite3.connect(
            db_path,
            check_same_thread=False
        )

        self.conn.row_factory = sqlite3.Row

        self.create_tables()

    # --------------------------------------------------

    def create_tables(self):

        cursor = self.conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            user_id INTEGER PRIMARY KEY,

            username TEXT,

            display_name TEXT,

            last_seen TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS interests (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            interest TEXT,

            UNIQUE(user_id, interest)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            project TEXT,

            UNIQUE(user_id, project)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS preferences (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            preference TEXT,

            UNIQUE(user_id, preference)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS facts (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            fact TEXT,

            UNIQUE(user_id, fact)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            event_type TEXT,

            content TEXT,

            created_at TEXT
        )
        """)

        self.conn.commit()

    # --------------------------------------------------

    def ensure_user(
        self,
        user_id: int,
        username: str,
        display_name: str
    ):

        cursor = self.conn.cursor()

        cursor.execute("""
        INSERT OR IGNORE INTO users
        (
            user_id,
            username,
            display_name,
            last_seen
        )
        VALUES (?, ?, ?, ?)
        """, (
            user_id,
            username,
            display_name,
            datetime.now().isoformat()
        ))

        self.conn.commit()

    # --------------------------------------------------

    def update_last_seen(self, user_id: int):

        cursor = self.conn.cursor()

        cursor.execute("""
        UPDATE users
        SET last_seen = ?
        WHERE user_id = ?
        """, (
            datetime.now().isoformat(),
            user_id
        ))

        self.conn.commit()

    # --------------------------------------------------

    def _add_unique(
        self,
        table: str,
        column: str,
        user_id: int,
        value: str
    ):

        value = value.strip()

        if not value:
            return

        cursor = self.conn.cursor()

        cursor.execute(
            f"""
            INSERT OR IGNORE INTO {table}
            (
                user_id,
                {column}
            )
            VALUES (?, ?)
            """,
            (
                user_id,
                value
            )
        )

        self.conn.commit()

    # --------------------------------------------------

    def add_interest(
        self,
        user_id: int,
        interest: str
    ):
        self._add_unique(
            "interests",
            "interest",
            user_id,
            interest
        )

    def add_project(
        self,
        user_id: int,
        project: str
    ):
        self._add_unique(
            "projects",
            "project",
            user_id,
            project
        )

    def add_preference(
        self,
        user_id: int,
        preference: str
    ):
        self._add_unique(
            "preferences",
            "preference",
            user_id,
            preference
        )

    def add_fact(
        self,
        user_id: int,
        fact: str
    ):
        self._add_unique(
            "facts",
            "fact",
            user_id,
            fact
        )

    # --------------------------------------------------

    def add_history(
        self,
        user_id: int,
        event_type: str,
        content: str
    ):

        cursor = self.conn.cursor()

        cursor.execute("""
        INSERT INTO history
        (
            user_id,
            event_type,
            content,
            created_at
        )
        VALUES (?, ?, ?, ?)
        """, (
            user_id,
            event_type,
            content,
            datetime.now().isoformat()
        ))

        self.conn.commit()

    # --------------------------------------------------

    def _get_list(
        self,
        table: str,
        column: str,
        user_id: int
    ):

        cursor = self.conn.cursor()

        cursor.execute(
            f"""
            SELECT {column}
            FROM {table}
            WHERE user_id = ?
            """,
            (user_id,)
        )

        return [
            row[column]
            for row in cursor.fetchall()
        ]

    # --------------------------------------------------

    def get_profile(self, user_id: int):

        cursor = self.conn.cursor()

        cursor.execute("""
        SELECT *
        FROM users
        WHERE user_id = ?
        """, (user_id,))

        user = cursor.fetchone()

        if user is None:
            return None

        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "display_name": user["display_name"],
            "last_seen": user["last_seen"],

            "interests": self._get_list(
                "interests",
                "interest",
                user_id
            ),

            "projects": self._get_list(
                "projects",
                "project",
                user_id
            ),

            "preferences": self._get_list(
                "preferences",
                "preference",
                user_id
            ),

            "facts": self._get_list(
                "facts",
                "fact",
                user_id
            )
        }

    # --------------------------------------------------

    def build_profile_prompt(self, user_id: int) -> str:

        profile = self.get_profile(user_id)

        if profile is None:
            return ""

        sections = []

        if profile["interests"]:
            sections.append(
                "İlgi Alanları:\n- " +
                "\n- ".join(profile["interests"])
            )

        if profile["projects"]:
            sections.append(
                "Projeler:\n- " +
                "\n- ".join(profile["projects"])
            )

        if profile["preferences"]:
            sections.append(
                "Tercihler:\n- " +
                "\n- ".join(profile["preferences"])
            )

        if profile["facts"]:
            sections.append(
                "Bilinen Bilgiler:\n- " +
                "\n- ".join(profile["facts"])
            )

        if not sections:
            return ""

        return (
            "KULLANICI PROFİLİ\n\n"
            + "\n\n".join(sections)
            + "\n\n"
            + "Bu bilgiler önceki konuşmalardan öğrenildi. "
              "Sadece gerçekten uygun olduğunda doğal şekilde kullan. "
              "Bilgileri gereksiz yere tekrar etme."
        )

    # --------------------------------------------------

    def close(self):
        self.conn.close()