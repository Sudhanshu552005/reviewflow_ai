import sqlite3

DATABASE_NAME = "reviewflow.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Businesses Profile Mapping
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS businesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            custom_category TEXT,
            place_id TEXT NOT NULL,
            threshold REAL NOT NULL DEFAULT 4.0,
            primary_alert TEXT NOT NULL,
            alternate_alert TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Authenticated Accounts Access Controls
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            FOREIGN KEY(business_id) REFERENCES businesses(id)
        )
    ''')
    
    # 3. Customer Submissions & Service Recovery Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL,
            overall_rating INTEGER NOT NULL,
            sub_rating_1 INTEGER,
            sub_rating_2 INTEGER,
            complaint_text TEXT,
            improvement_tags TEXT,
            customer_contact TEXT,
            selected_draft_text TEXT,
            is_read INTEGER DEFAULT 0,
            status TEXT DEFAULT 'New',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(business_id) REFERENCES businesses(id)
        )
    ''')

    # 4. FIXED: Added Device Fingerprint Tracking Table for 24-Hour Cool-down Protection
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fingerprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL,
            device_hash TEXT NOT NULL,
            last_scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(business_id) REFERENCES businesses(id),
            UNIQUE(business_id, device_hash)
        )
    ''')
    
    try:
        cursor.execute("INSERT INTO accounts (username, password, role) VALUES ('dbs_admin', 'dbs_secure2026', 'super_admin')")
    except sqlite3.IntegrityError:
        pass
        
    conn.commit()
    conn.close()
    print("🚀 Master Database successfully upgraded with 24-hour cool-down and verification telemetry tracking.")

if __name__ == "__main__":
    init_db()