import sqlite3
from pathlib import Path


DB_PATH = Path("data/appointments.db")


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def book_appointment(name, date, time):

    init_db()

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.execute(
        """
        INSERT INTO appointments (name, date, time)
        VALUES (?, ?, ?)
        """,
        (name, date, time)
    )

    appointment_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {
        "success": True,
        "appointment_id": appointment_id,
        "name": name,
        "date": date,
        "time": time
    }


def get_appointments():

    init_db()

    conn = sqlite3.connect(DB_PATH)

    rows = conn.execute(
        """
        SELECT id, name, date, time
        FROM appointments
        ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "date": row[2],
            "time": row[3]
        }
        for row in rows
    ]


def get_business_hours():

    return {
        "monday_friday": "9:00 AM - 6:00 PM",
        "saturday": "10:00 AM - 2:00 PM",
        "sunday": "Closed"
    }


def get_services():

    return [
        "Web application development",
        "Mobile application development",
        "AI automation",
        "Cloud solutions",
        "Software consulting"
    ]
    
init_db()