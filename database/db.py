"""
Uniwersalny moduł bazy danych (PostgreSQL + SQLite)
Projekt: Weimar Research Hub (Wszystkie Dziedziny Nauki)
"""

import json
import os
import sqlite3
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import SQLITE_DB_FILE, INSTITUTIONS

USE_POSTGRES = os.environ.get("USE_POSTGRES", "0") == "1"
PG_HOST = os.environ.get("PG_HOST", "localhost")
PG_PORT = os.environ.get("PG_PORT", "5432")
PG_DB = os.environ.get("PG_DB", "weimar_hub")
PG_USER = os.environ.get("PG_USER", "postgres")
PG_PASS = os.environ.get("PG_PASS", "postgres")

def get_connection():
    if USE_POSTGRES:
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=PG_HOST,
                port=PG_PORT,
                dbname=PG_DB,
                user=PG_USER,
                password=PG_PASS
            )
            return conn, "postgres"
        except Exception as e:
            print(f"[DB] Błąd PostgreSQL ({e}). Przełączenie na SQLite.")

    conn = sqlite3.connect(str(SQLITE_DB_FILE))
    conn.row_factory = sqlite3.Row
    return conn, "sqlite"

def init_db(reset=False):
    """Inicjalizuje schemat tabel w bazie danych."""
    conn, db_type = get_connection()
    cursor = conn.cursor()

    if reset:
        cursor.execute("DROP TABLE IF EXISTS publications;")
        cursor.execute("DROP TABLE IF EXISTS researchers;")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS institutions (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        short_name TEXT NOT NULL,
        country TEXT NOT NULL,
        city TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS researchers (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        orcid TEXT,
        country TEXT NOT NULL,
        affiliation TEXT NOT NULL,
        affiliation_full TEXT,
        city TEXT,
        openalex_domain TEXT,
        field TEXT,
        subfield TEXT,
        primary_domain TEXT,
        works_count INTEGER DEFAULT 0,
        cited_by_count INTEGER DEFAULT 0,
        h_index INTEGER DEFAULT 0,
        profile_summary TEXT,
        competencies TEXT,
        topics TEXT,
        coauthors TEXT,
        embedding TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Bezpieczne dodanie ewentualnych brakujących kolumn przy istniejącej bazie SQLite
    if db_type == "sqlite":
        cursor.execute("PRAGMA table_info(researchers);")
        existing_cols = {row[1] for row in cursor.fetchall()}
        for col_name in ["openalex_domain", "subfield", "primary_domain"]:
            if col_name not in existing_cols:
                cursor.execute(f"ALTER TABLE researchers ADD COLUMN {col_name} TEXT;")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS publications (
        id TEXT PRIMARY KEY,
        researcher_id TEXT NOT NULL,
        title TEXT NOT NULL,
        publication_year INTEGER,
        doi TEXT,
        abstract TEXT,
        topics TEXT,
        FOREIGN KEY (researcher_id) REFERENCES researchers(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_researcher_id TEXT NOT NULL,
        target_researcher_id TEXT NOT NULL,
        recommendation_type TEXT NOT NULL,
        score REAL NOT NULL,
        explanation TEXT,
        mutual_works TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS collaboration_proposals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        researcher_ids TEXT NOT NULL,
        researcher_names TEXT NOT NULL,
        project_title TEXT NOT NULL,
        scientific_rationale TEXT,
        competency_division TEXT,
        expected_outcomes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    for inst in INSTITUTIONS:
        cursor.execute("""
            INSERT OR REPLACE INTO institutions (id, name, short_name, country, city)
            VALUES (?, ?, ?, ?, ?)
        """, (inst["id"], inst["name"], inst["short_name"], inst["country"], inst["city"]))

    conn.commit()
    conn.close()

def save_researchers_to_db(researchers_list, reset=False):
    """Zapisuje listę naukowców i publikacji do bazy."""
    init_db(reset=reset)
    conn, _ = get_connection()
    cursor = conn.cursor()

    count_res = 0
    count_pubs = 0

    for r in researchers_list:
        r_id = r["openalex_id"]
        cursor.execute("""
            INSERT OR REPLACE INTO researchers
            (id, name, orcid, country, affiliation, affiliation_full, city,
             openalex_domain, field, subfield, primary_domain,
             works_count, cited_by_count, h_index, profile_summary, competencies,
             topics, coauthors, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r_id,
            r.get("name"),
            r.get("orcid"),
            r.get("country"),
            r.get("affiliation"),
            r.get("affiliation_full"),
            r.get("city"),
            r.get("openalex_domain", ""),
            r.get("field", ""),
            r.get("subfield", ""),
            r.get("primary_domain", r.get("field", "")),
            r.get("works_count", 0),
            r.get("cited_by_count", 0),
            r.get("h_index", 0),
            r.get("profile_summary", ""),
            json.dumps(r.get("competencies", []), ensure_ascii=False),
            json.dumps(r.get("topics", []), ensure_ascii=False),
            json.dumps(r.get("coauthors", []), ensure_ascii=False),
            json.dumps(r.get("embedding", []), ensure_ascii=False) if r.get("embedding") else None
        ))
        count_res += 1

        for p in r.get("publications", []):
            pub_id = p.get("work_id") or f"{r_id}_{count_pubs}"
            cursor.execute("""
                INSERT OR REPLACE INTO publications
                (id, researcher_id, title, publication_year, doi, abstract, topics)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                pub_id,
                r_id,
                p.get("title", "Bez tytułu"),
                p.get("publication_year"),
                p.get("doi"),
                p.get("abstract", ""),
                json.dumps(p.get("topics", []), ensure_ascii=False)
            ))
            count_pubs += 1

    conn.commit()
    conn.close()
    print(f"[DB] Zapisano do bazy: {count_res} naukowców oraz {count_pubs} publikacji.")

if __name__ == "__main__":
    init_db()
    print(f"[DB] Baza gotowa: {SQLITE_DB_FILE}")
