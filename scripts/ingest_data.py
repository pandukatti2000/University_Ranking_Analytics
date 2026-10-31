import os
import sys
import csv
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "Pandu@18052000")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_DB = os.getenv("POSTGRES_DB", "university_ranking_db")

# Path to CSV directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_DIR = os.path.join(BASE_DIR, "university_ranking-main", "Data", "CSV")

def get_connection():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        dbname=POSTGRES_DB,
        connect_timeout=5
    )

def read_csv(filename):
    filepath = os.path.join(CSV_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Source file not found at: {filepath}")
    with open(filepath, mode="r", encoding="utf-8-sig") as fp:
        reader = csv.DictReader(fp)
        return list(reader)

def ingest_countries(cur):
    print("Ingesting country.csv...")
    rows = read_csv("country.csv")
    data = [(int(r['id']), r['country_name'].strip()) for r in rows]
    query = """
    INSERT INTO country (id, country_name)
    VALUES %s
    ON CONFLICT (id) DO UPDATE SET country_name = EXCLUDED.country_name;
    """
    execute_values(cur, query, data)
    print(f"  Ingested {len(data)} countries.")

def ingest_ranking_systems(cur):
    print("Ingesting ranking_system.csv...")
    rows = read_csv("ranking_system.csv")
    data = [(int(r['id']), r['system_name'].strip()) for r in rows]
    query = """
    INSERT INTO ranking_system (id, system_name)
    VALUES %s
    ON CONFLICT (id) DO UPDATE SET system_name = EXCLUDED.system_name;
    """
    execute_values(cur, query, data)
    print(f"  Ingested {len(data)} ranking systems.")

def ingest_ranking_criteria(cur):
    print("Ingesting ranking_criteria.csv...")
    rows = read_csv("ranking_criteria.csv")
    data = [(int(r['id']), int(r['ranking_system_id']), r['criteria_name'].strip()) for r in rows]
    query = """
    INSERT INTO ranking_criteria (id, ranking_system_id, criteria_name)
    VALUES %s
    ON CONFLICT (id) DO UPDATE 
    SET ranking_system_id = EXCLUDED.ranking_system_id,
        criteria_name = EXCLUDED.criteria_name;
    """
    execute_values(cur, query, data)
    print(f"  Ingested {len(data)} ranking criteria.")

def ingest_universities(cur):
    print("Ingesting university.csv...")
    rows = read_csv("university.csv")
    data = [(int(r['id']), int(r['country_id']), r['university_name'].strip()) for r in rows]
    query = """
    INSERT INTO university (id, country_id, university_name)
    VALUES %s
    ON CONFLICT (id) DO UPDATE 
    SET country_id = EXCLUDED.country_id,
        university_name = EXCLUDED.university_name;
    """
    execute_values(cur, query, data, page_size=1000)
    print(f"  Ingested {len(data)} universities.")

def ingest_university_ranking_year(cur):
    print("Ingesting university_ranking_year.csv...")
    rows = read_csv("university_ranking_year.csv")
    data = []
    null_scores = 0
    for r in rows:
        uid = int(r['university_id'])
        cid = int(r['ranking_criteria_id'])
        yr = int(r['year'])
        score_raw = r['score'].strip()
        if score_raw == "":
            score = None
            null_scores += 1
        else:
            score = float(score_raw)
        data.append((uid, cid, yr, score))
    
    query = """
    INSERT INTO university_ranking_year (university_id, ranking_criteria_id, year, score)
    VALUES %s
    ON CONFLICT (university_id, ranking_criteria_id, year) DO UPDATE 
    SET score = EXCLUDED.score;
    """
    execute_values(cur, query, data, page_size=5000)
    print(f"  Ingested {len(data)} ranking year records (with {null_scores} explicit NULL scores).")

def ingest_university_year(cur):
    print("Ingesting university_year.csv...")
    rows = read_csv("university_year.csv")
    data = []
    null_female = 0
    for r in rows:
        uid = int(r['university_id'])
        yr = int(r['year'])
        num_students = int(r['num_students'])
        student_staff_ratio = float(r['student_staff_ratio'])
        pct_intl = int(r['pct_international_students'])
        
        female_raw = r['pct_female_students'].strip()
        if female_raw == "":
            pct_female = None
            null_female += 1
        else:
            pct_female = float(female_raw)
        data.append((uid, yr, num_students, student_staff_ratio, pct_intl, pct_female))

    query = """
    INSERT INTO university_year (university_id, year, num_students, student_staff_ratio, pct_international_students, pct_female_students)
    VALUES %s
    ON CONFLICT (university_id, year) DO UPDATE 
    SET num_students = EXCLUDED.num_students,
        student_staff_ratio = EXCLUDED.student_staff_ratio,
        pct_international_students = EXCLUDED.pct_international_students,
        pct_female_students = EXCLUDED.pct_female_students;
    """
    execute_values(cur, query, data, page_size=1000)
    print(f"  Ingested {len(data)} university year demographic records (with {null_female} NULL female percentage values).")

def reconcile_and_validate(cur):
    print("\n--- RECONCILIATION & VALIDATION ---")
    tables = [
        ("country", 74),
        ("ranking_system", 3),
        ("ranking_criteria", 21),
        ("university", 1247),
        ("university_ranking_year", 29612),
        ("university_year", 1085)
    ]
    
    all_passed = True
    for tbl, expected in tables:
        cur.execute(f"SELECT COUNT(*) FROM {tbl};")
        actual = cur.fetchone()[0]
        status = "PASSED" if actual == expected else "FAILED"
        if status == "FAILED":
            all_passed = False
        print(f"  Table '{tbl:24s}': Expected={expected:5d} | Actual={actual:5d} | [{status}]")

    # Specific null checks
    cur.execute("SELECT COUNT(*) FROM university_ranking_year WHERE score IS NULL;")
    actual_null_scores = cur.fetchone()[0]
    expected_null_scores = 130
    status_null_s = "PASSED" if actual_null_scores == expected_null_scores else "FAILED"
    print(f"  Null Scores (Criterion 5): Expected={expected_null_scores:5d} | Actual={actual_null_scores:5d} | [{status_null_s}]")
    if status_null_s == "FAILED":
        all_passed = False

    cur.execute("SELECT COUNT(*) FROM university_year WHERE pct_female_students IS NULL;")
    actual_null_female = cur.fetchone()[0]
    expected_null_female = 96
    status_null_f = "PASSED" if actual_null_female == expected_null_female else "FAILED"
    print(f"  Null Female Students Pct : Expected={expected_null_female:5d} | Actual={actual_null_female:5d} | [{status_null_f}]")
    if status_null_f == "FAILED":
        all_passed = False

    if not all_passed:
        raise ValueError("Reconciliation failed! Counts do not match expected values.")
    print("Reconciliation successfully verified! All tables 100% matched.")

def main():
    print(f"Starting CSV ingestion into '{POSTGRES_DB}' from: {CSV_DIR}")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            ingest_countries(cur)
            ingest_ranking_systems(cur)
            ingest_ranking_criteria(cur)
            ingest_universities(cur)
            ingest_university_ranking_year(cur)
            ingest_university_year(cur)
            conn.commit()
            reconcile_and_validate(cur)
    except Exception as e:
        conn.rollback()
        print(f"Ingestion failed with error: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
