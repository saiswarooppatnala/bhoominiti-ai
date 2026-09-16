import sqlite3
import hashlib
import secrets
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "bhoominiti.db"

LAND_CSV = DATA_DIR / "land_data.csv"
RESEARCH_CSV = DATA_DIR / "research_data.csv"


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _now():
    return datetime.now(timezone.utc).isoformat()


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT,
    role TEXT NOT NULL CHECK (role IN ('Public', 'Researcher', 'Official', 'Admin')),
    salt TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS land_data (
    State TEXT PRIMARY KEY,
    Land_Governance_Index REAL,
    Urban_Expansion REAL,
    Agri_Land_Percent REAL,
    Climate_Vulnerability REAL,
    Dispute_Density REAL,
    Infrastructure_Pressure REAL
);

CREATE TABLE IF NOT EXISTS research_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Title TEXT NOT NULL,
    Type TEXT,
    Theme TEXT,
    Region TEXT,
    Year INTEGER,
    Summary TEXT,
    submitted_by TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS innovation_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL CHECK (category IN ('Hackathon', 'Grant', 'Pilot Project', 'Knowledge Competition')),
    title TEXT NOT NULL,
    description TEXT,
    organization TEXT,
    deadline TEXT,
    status TEXT NOT NULL DEFAULT 'Open' CHECK (status IN ('Open', 'Ongoing', 'Closed')),
    created_by TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS innovation_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER REFERENCES innovation_items(id),
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    submitted_by TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Submitted' CHECK (status IN ('Submitted', 'Under Review', 'Accepted', 'Rejected')),
    created_at TEXT NOT NULL
);
"""


def init_db():
    first_run = not DB_PATH.exists()
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()

    if first_run:
        _seed_land_data(conn)
        _seed_research_data(conn)
        _seed_innovation_items(conn)
        _seed_default_accounts(conn)

    conn.close()


def _seed_land_data(conn):
    if not LAND_CSV.exists():
        return
    df = pd.read_csv(LAND_CSV)
    df.to_sql("land_data", conn, if_exists="replace", index=False)
    conn.commit()


def _seed_research_data(conn):
    if not RESEARCH_CSV.exists():
        return
    df = pd.read_csv(RESEARCH_CSV)
    df["submitted_by"] = "seed_data"
    df["created_at"] = _now()
    df.to_sql("research_data", conn, if_exists="append", index=False)
    conn.commit()


def _seed_innovation_items(conn):
    items = [
        ("Hackathon", "Smart India Hackathon 2026 — Land Governance Track",
         "National hackathon track focused on AI-enabled land governance, GIS analytics and policy simulation tools.",
         "Ministry of Rural Development (DoLR)", "2026-12-15", "Open"),
        ("Grant", "Applied Research Grant: Climate-Resilient Land Use Planning",
         "Seed funding for research proposals studying climate vulnerability and adaptive land-use zoning at district scale.",
         "Dept of Land Resources", "2027-01-31", "Open"),
        ("Pilot Project", "Drone-Based Cadastral Resurvey Pilot — Phase II",
         "Expansion of the drone cadastral survey pilot to five additional districts, seeking implementation partners.",
         "State Revenue Department", "2026-11-30", "Ongoing"),
        ("Knowledge Competition", "National Land Data Visualization Challenge",
         "Open competition inviting dashboards and visual analytics built on public land governance indicators.",
         "NIC / DoLR", "2026-10-20", "Open"),
        ("Grant", "Fellowship: Digital Land Records and Financial Inclusion",
         "Fellowship supporting research on the link between land title digitization and access to formal agricultural credit.",
         "Dept of Land Resources", "2027-02-28", "Open"),
    ]
    now = _now()
    conn.executemany(
        """INSERT INTO innovation_items
           (category, title, description, organization, deadline, status, created_by, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        [(c, t, d, o, dl, st, "seed_data", now) for c, t, d, o, dl, st in items],
    )
    conn.commit()


def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000).hex()
    return salt, digest


def _seed_default_accounts(conn):
    demo_users = [
        ("official_demo", "Demo Official", "official@example.gov.in", "Official", "Demo@1234"),
        ("researcher_demo", "Demo Researcher", "researcher@example.org", "Researcher", "Demo@1234"),
    ]
    now = _now()
    for username, full_name, email, role, password in demo_users:
        salt, digest = hash_password(password)
        conn.execute(
            """INSERT OR IGNORE INTO users
               (username, full_name, email, role, salt, password_hash, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (username, full_name, email, role, salt, digest, now),
        )
    conn.commit()


def get_user(username):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_user(username, full_name, email, role, password):
    if get_user(username):
        return False, "Username already exists."

    salt, digest = hash_password(password)
    conn = get_connection()
    conn.execute(
        """INSERT INTO users (username, full_name, email, role, salt, password_hash, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (username, full_name, email, role, salt, digest, _now()),
    )
    conn.commit()
    conn.close()
    return True, "Account created."


def verify_user(username, password):
    user = get_user(username)
    if not user:
        return None
    _, digest = hash_password(password, user["salt"])
    if secrets.compare_digest(digest, user["password_hash"]):
        return user
    return None


def load_land_df():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM land_data", conn)
    conn.close()
    return df


def load_research_df():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM research_data ORDER BY Year DESC", conn)
    conn.close()
    return df


def add_research_record(title, doc_type, theme, region, year, summary, submitted_by):
    conn = get_connection()
    conn.execute(
        """INSERT INTO research_data (Title, Type, Theme, Region, Year, Summary, submitted_by, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (title, doc_type, theme, region, year, summary, submitted_by, _now()),
    )
    conn.commit()
    conn.close()


def load_innovation_items():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM innovation_items ORDER BY created_at DESC", conn)
    conn.close()
    return df


def add_innovation_item(category, title, description, organization, deadline, created_by):
    conn = get_connection()
    conn.execute(
        """INSERT INTO innovation_items (category, title, description, organization, deadline, status, created_by, created_at)
           VALUES (?, ?, ?, ?, ?, 'Open', ?, ?)""",
        (category, title, description, organization, deadline, created_by, _now()),
    )
    conn.commit()
    conn.close()


def update_innovation_item_status(item_id, status):
    conn = get_connection()
    conn.execute("UPDATE innovation_items SET status = ? WHERE id = ?", (status, item_id))
    conn.commit()
    conn.close()


def load_innovation_submissions(item_id=None):
    conn = get_connection()
    if item_id is None:
        df = pd.read_sql_query("SELECT * FROM innovation_submissions ORDER BY created_at DESC", conn)
    else:
        df = pd.read_sql_query(
            "SELECT * FROM innovation_submissions WHERE item_id = ? ORDER BY created_at DESC",
            conn, params=(item_id,),
        )
    conn.close()
    return df


def add_innovation_submission(item_id, title, description, category, submitted_by):
    conn = get_connection()
    conn.execute(
        """INSERT INTO innovation_submissions (item_id, title, description, category, submitted_by, status, created_at)
           VALUES (?, ?, ?, ?, ?, 'Submitted', ?)""",
        (item_id, title, description, category, submitted_by, _now()),
    )
    conn.commit()
    conn.close()


def update_submission_status(submission_id, status):
    conn = get_connection()
    conn.execute("UPDATE innovation_submissions SET status = ? WHERE id = ?", (status, submission_id))
    conn.commit()
    conn.close()
