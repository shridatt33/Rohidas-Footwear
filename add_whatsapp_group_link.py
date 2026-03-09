"""
Add WhatsApp Group Invite Link column to lead_form_settings table
"""
import mysql.connector
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

try:
    print("Connecting to database...")
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )
    cursor = conn.cursor()
    
    print("Adding whatsapp_group_link column...")
    
    # Check if column already exists
    cursor.execute("SHOW COLUMNS FROM lead_form_settings LIKE 'whatsapp_group_link'")
    if cursor.fetchone():
        print("✓ Column already exists")
    else:
        cursor.execute("""
            ALTER TABLE lead_form_settings 
            ADD COLUMN whatsapp_group_link VARCHAR(500) NULL
            AFTER thank_you_message
        """)
        conn.commit()
        print("✓ Column added successfully")
    
    # Verify
    cursor.execute("DESCRIBE lead_form_settings")
    columns = cursor.fetchall()
    
    print("\nCurrent columns in lead_form_settings:")
    for col in columns:
        print(f"  - {col[0]} ({col[1]})")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Migration completed successfully!")
    print("Restart your Flask app now.")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

input("\nPress Enter to exit...")
