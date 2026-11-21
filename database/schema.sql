-- ====================================================================
-- Weimar Research Hub — Database Schema (PostgreSQL + pgvector / SQLite)
-- Obsługuje wszystkie dziedziny nauki (Polska, Niemcy, Francja)
-- ====================================================================

-- Włączenie rozszerzenia pgvector (dla PostgreSQL):
-- CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS institutions (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    short_name VARCHAR(64) NOT NULL,
    country VARCHAR(8) NOT NULL,
    city VARCHAR(128) NOT NULL
);

CREATE TABLE IF NOT EXISTS researchers (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    orcid VARCHAR(64),
    country VARCHAR(8) NOT NULL,
    affiliation VARCHAR(64) NOT NULL,
    affiliation_full VARCHAR(255),
    city VARCHAR(128),
    openalex_domain VARCHAR(128),
    field VARCHAR(128),
    subfield VARCHAR(128),
    primary_domain VARCHAR(128),
    works_count INT DEFAULT 0,
    cited_by_count INT DEFAULT 0,
    h_index INT DEFAULT 0,
    profile_summary TEXT,
    competencies TEXT,
    topics TEXT,
    coauthors TEXT,
    embedding TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS publications (
    id VARCHAR(64) PRIMARY KEY,
    researcher_id VARCHAR(64) NOT NULL,
    title TEXT NOT NULL,
    publication_year INT,
    doi TEXT,
    abstract TEXT,
    topics TEXT,
    FOREIGN KEY (researcher_id) REFERENCES researchers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_researcher_id VARCHAR(64) NOT NULL,
    target_researcher_id VARCHAR(64) NOT NULL,
    recommendation_type VARCHAR(32) NOT NULL,
    score REAL NOT NULL,
    explanation TEXT,
    mutual_works TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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

CREATE INDEX IF NOT EXISTS idx_researchers_country ON researchers(country);
CREATE INDEX IF NOT EXISTS idx_researchers_affiliation ON researchers(affiliation);
CREATE INDEX IF NOT EXISTS idx_researchers_field ON researchers(field);
CREATE INDEX IF NOT EXISTS idx_publications_researcher ON publications(researcher_id);
