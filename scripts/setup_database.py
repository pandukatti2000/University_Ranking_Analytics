import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "Pandu@18052000")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_DB = os.getenv("POSTGRES_DB", "university_ranking_db")

READONLY_USER = os.getenv("POSTGRES_READONLY_USER", "ranking_readonly")
READONLY_PASSWORD = os.getenv("POSTGRES_READONLY_PASSWORD", "ReadOnly@Ranking2026")

def get_admin_connection():
    """Connect to default 'postgres' database to manage databases and roles."""
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        dbname="postgres",
        connect_timeout=5
    )
    conn.autocommit = True
    return conn

def get_app_connection():
    """Connect to target university_ranking_db database."""
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        dbname=POSTGRES_DB,
        connect_timeout=5
    )
    conn.autocommit = True
    return conn

def create_database_if_not_exists():
    print(f"Connecting to PostgreSQL at {POSTGRES_HOST}:{POSTGRES_PORT} as {POSTGRES_USER}...")
    conn = get_admin_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (POSTGRES_DB,))
            exists = cur.fetchone()
            if not exists:
                print(f"Creating database '{POSTGRES_DB}'...")
                cur.execute(f'CREATE DATABASE "{POSTGRES_DB}" WITH ENCODING = \'UTF8\';')
                print(f"Database '{POSTGRES_DB}' created successfully.")
            else:
                print(f"Database '{POSTGRES_DB}' already exists.")
    finally:
        conn.close()

def setup_readonly_role():
    print(f"Setting up read-only role '{READONLY_USER}'...")
    conn = get_admin_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s;", (READONLY_USER,))
            exists = cur.fetchone()
            if not exists:
                cur.execute(f"CREATE ROLE {READONLY_USER} WITH LOGIN PASSWORD %s NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;", (READONLY_PASSWORD,))
                print(f"Role '{READONLY_USER}' created.")
            else:
                cur.execute(f"ALTER ROLE {READONLY_USER} WITH PASSWORD %s;", (READONLY_PASSWORD,))
                print(f"Role '{READONLY_USER}' password updated.")
    finally:
        conn.close()

def create_schema(recreate=False):
    print(f"Applying schema to '{POSTGRES_DB}' (recreate={recreate})...")
    with get_app_connection() as conn:
        with conn.cursor() as cur:
            if recreate:
                print("Dropping existing views and tables...")
                cur.execute("DROP VIEW IF EXISTS v_ranked_universities CASCADE;")
                cur.execute("DROP VIEW IF EXISTS v_criteria_overview CASCADE;")
                cur.execute("DROP VIEW IF EXISTS v_university_overview CASCADE;")
                cur.execute("DROP TABLE IF EXISTS university_year CASCADE;")
                cur.execute("DROP TABLE IF EXISTS university_ranking_year CASCADE;")
                cur.execute("DROP TABLE IF EXISTS university CASCADE;")
                cur.execute("DROP TABLE IF EXISTS ranking_criteria CASCADE;")
                cur.execute("DROP TABLE IF EXISTS ranking_system CASCADE;")
                cur.execute("DROP TABLE IF EXISTS country CASCADE;")

            # 1. Country table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS country (
                id INTEGER PRIMARY KEY,
                country_name VARCHAR(100) NOT NULL UNIQUE
            );
            """)

            # 2. Ranking system table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS ranking_system (
                id INTEGER PRIMARY KEY,
                system_name VARCHAR(100) NOT NULL UNIQUE
            );
            """)

            # 3. Ranking criteria table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS ranking_criteria (
                id INTEGER PRIMARY KEY,
                ranking_system_id INTEGER NOT NULL REFERENCES ranking_system(id) ON DELETE RESTRICT,
                criteria_name VARCHAR(200) NOT NULL,
                CONSTRAINT uq_sys_crit UNIQUE (ranking_system_id, criteria_name)
            );
            """)

            # 4. University table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS university (
                id INTEGER PRIMARY KEY,
                country_id INTEGER NOT NULL REFERENCES country(id) ON DELETE RESTRICT,
                university_name VARCHAR(200) NOT NULL
            );
            """)

            # 5. University ranking year table (fact table)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS university_ranking_year (
                university_id INTEGER NOT NULL REFERENCES university(id) ON DELETE CASCADE,
                ranking_criteria_id INTEGER NOT NULL REFERENCES ranking_criteria(id) ON DELETE CASCADE,
                year SMALLINT NOT NULL CHECK (year BETWEEN 2000 AND 2030),
                score NUMERIC(6,2) DEFAULT NULL,
                PRIMARY KEY (university_id, ranking_criteria_id, year)
            );
            """)

            # 6. University year demographics table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS university_year (
                university_id INTEGER NOT NULL REFERENCES university(id) ON DELETE CASCADE,
                year SMALLINT NOT NULL CHECK (year BETWEEN 2000 AND 2030),
                num_students INTEGER NOT NULL CHECK (num_students > 0),
                student_staff_ratio NUMERIC(5,2) NOT NULL CHECK (student_staff_ratio > 0),
                pct_international_students SMALLINT NOT NULL CHECK (pct_international_students BETWEEN 0 AND 100),
                pct_female_students NUMERIC(5,2) DEFAULT NULL CHECK (pct_female_students BETWEEN 0 AND 100),
                PRIMARY KEY (university_id, year)
            );
            """)

            # Indexes for ultra-fast analytics querying
            cur.execute("CREATE INDEX IF NOT EXISTS idx_uni_country ON university(country_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_uni_name ON university(university_name);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_crit_sys ON ranking_criteria(ranking_system_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ury_uni_yr ON university_ranking_year(university_id, year);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ury_crit_yr ON university_ranking_year(ranking_criteria_id, year);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ury_yr_score ON university_ranking_year(year, score);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_uy_uni_yr ON university_year(university_id, year);")

            # Views for analytics and GenAI agent convenience
            cur.execute("""
            CREATE OR REPLACE VIEW v_university_overview AS
            SELECT 
                u.id AS university_id,
                u.university_name,
                c.id AS country_id,
                c.country_name
            FROM university u
            JOIN country c ON u.country_id = c.id;
            """)

            cur.execute("""
            CREATE OR REPLACE VIEW v_criteria_overview AS
            SELECT 
                rc.id AS criteria_id,
                rc.criteria_name,
                rs.id AS system_id,
                rs.system_name,
                CASE 
                    WHEN rc.id BETWEEN 14 AND 20 THEN 'rank'
                    ELSE 'score'
                END AS metric_type,
                CASE 
                    WHEN rc.id BETWEEN 14 AND 20 THEN 'asc'
                    ELSE 'desc'
                END AS optimal_sort_order
            FROM ranking_criteria rc
            JOIN ranking_system rs ON rc.ranking_system_id = rs.id;
            """)

            cur.execute("""
            CREATE OR REPLACE VIEW v_ranked_universities AS
            SELECT 
                ury.year,
                rs.id AS system_id,
                rs.id AS ranking_system_id,
                rs.system_name,
                rc.id AS criteria_id,
                rc.id AS ranking_criteria_id,
                rc.criteria_name,
                u.id AS university_id,
                u.university_name,
                c.country_name,
                ury.score,
                CASE 
                    WHEN rc.id BETWEEN 14 AND 20 THEN 'rank'
                    ELSE 'score'
                END AS metric_type
            FROM university_ranking_year ury
            JOIN university u ON ury.university_id = u.id
            JOIN country c ON u.country_id = c.id
            JOIN ranking_criteria rc ON ury.ranking_criteria_id = rc.id
            JOIN ranking_system rs ON rc.ranking_system_id = rs.id;
            """)

            # Grant read-only access to ranking_readonly
            cur.execute(f"GRANT CONNECT ON DATABASE \"{POSTGRES_DB}\" TO {READONLY_USER};")
            cur.execute(f"GRANT USAGE ON SCHEMA public TO {READONLY_USER};")
            cur.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {READONLY_USER};")
            cur.execute(f"GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO {READONLY_USER};")
            cur.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO {READONLY_USER};")

            print("Schema, indexes, views, and permissions successfully applied.")

if __name__ == "__main__":
    recreate = "--recreate" in sys.argv
    create_database_if_not_exists()
    setup_readonly_role()
    create_schema(recreate=recreate)
    print("Database setup complete.")
