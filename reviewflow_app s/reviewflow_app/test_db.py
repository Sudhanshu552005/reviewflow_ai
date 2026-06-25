# test_db.py
import os
from database import get_db_connection

def verify_onboarding_data():
    print("⏳ Querying local 'reviewflow.db' storage engine...")
    
    if not os.path.exists("reviewflow.db"):
        print("❌ Error: 'reviewflow.db' file does not exist in this directory yet!")
        return

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Pull all registered records sorted by newest entry first
        cursor.execute("SELECT * FROM businesses ORDER BY id DESC")
        records = cursor.fetchall()
        
        if not records:
            print("⚠️ Database file found, but the 'businesses' table is empty.")
            return
            
        print(f"✅ Success! Found {len(records)} business record(s) stored locally.\n")
        print("-" * 70)
        
        for row in records:
            print(f"📍 [Tenant ID {row['id']}] - {row['name']}")
            print(f"   Category:  {row['category']}")
            print(f"   Place ID:  {row['place_id']}")
            print(f"   Threshold: {row['threshold']} Stars")
            print(f"   Alert to:  {row['alert_recipient']}")
            print(f"   Registered: {row['created_at']}")
            print("-" * 70)
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Internal Test Failure: {str(e)}")

if __name__ == "__main__":
    verify_onboarding_data()