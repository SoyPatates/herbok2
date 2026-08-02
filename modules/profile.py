import sqlite3
from datetime import datetime
from pathlib import Path


CATEGORY_TABLES = {
    "interests": ("interests", "interest"),
    "projects": ("projects", "project"),
    "preferences": ("preferences", "preference"),
    "facts": ("facts", "fact"),
}


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

    def _get_list_with_ids(
        self,
        table: str,
        column: str,
        user_id: int,
    ):
        """
        Ayni liste ama her deger, o satirin gercek/kalici DB id'siyle
        birlikte doner: [(id, deger), ...]. Bu id, silme/duzenleme
        icin kullanilir -- kategori icinde sirali (1,2,3...) bir
        numaralama DEGIL, satir silinip eklendikce kaymayan, sabit
        bir kimliktir.
        """

        cursor = self.conn.cursor()

        cursor.execute(
            f"""
            SELECT id, {column}
            FROM {table}
            WHERE user_id = ?
            ORDER BY id
            """,
            (user_id,)
        )

        return [
            (row["id"], row[column])
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

    def get_profile_detailed(self, user_id: int):
        """
        get_profile ile ayni ama her kategori [(id, deger), ...]
        seklinde doner -- yonetim (bilgi/sil/duzenle) komutlari
        icin kullanilir.
        """

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

            "interests": self._get_list_with_ids(
                "interests", "interest", user_id
            ),

            "projects": self._get_list_with_ids(
                "projects", "project", user_id
            ),

            "preferences": self._get_list_with_ids(
                "preferences", "preference", user_id
            ),

            "facts": self._get_list_with_ids(
                "facts", "fact", user_id
            ),
        }

    # --------------------------------------------------

    def add_entry(
        self,
        category: str,
        user_id: int,
        value: str,
    ) -> bool:
        """
        "facts"/"projects"/"interests"/"preferences" kategorilerinden
        birine yeni bir kayit ekler. Basarisiz olursa (gecersiz
        kategori) False doner.
        """

        if category not in CATEGORY_TABLES:
            return False

        table, column = CATEGORY_TABLES[category]

        self._add_unique(table, column, user_id, value)

        return True

    # --------------------------------------------------

    def update_entry(
        self,
        category: str,
        row_id: int,
        user_id: int,
        new_value: str,
    ) -> bool:
        """
        Belirli bir kaydin metnini gunceller. Satirin GERCEKTEN o
        user_id'ye ait oldugunu da kontrol eder (baskasinin
        kaydini yanlislikla/kotu niyetle degistirmeyi engeller).
        Basarili olursa True, satir bulunamazsa/ait degilse False.
        """

        if category not in CATEGORY_TABLES:
            return False

        new_value = new_value.strip()

        if not new_value:
            return False

        table, column = CATEGORY_TABLES[category]

        cursor = self.conn.cursor()

        cursor.execute(
            f"""
            UPDATE {table}
            SET {column} = ?
            WHERE id = ? AND user_id = ?
            """,
            (new_value, row_id, user_id),
        )

        self.conn.commit()

        return cursor.rowcount > 0

    # --------------------------------------------------

    def delete_entry(
        self,
        category: str,
        row_id: int,
        user_id: int,
    ) -> bool:
        """
        Belirli bir kaydi siler. Satirin GERCEKTEN o user_id'ye ait
        oldugunu kontrol eder. Basarili olursa True, bulunamazsa/
        ait degilse False.
        """

        if category not in CATEGORY_TABLES:
            return False

        table, column = CATEGORY_TABLES[category]

        cursor = self.conn.cursor()

        cursor.execute(
            f"""
            DELETE FROM {table}
            WHERE id = ? AND user_id = ?
            """,
            (row_id, user_id),
        )

        self.conn.commit()

        return cursor.rowcount > 0

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