"""
Add lead_form_settings table
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
    
    print("Creating lead_form_settings table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lead_form_settings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            shop_id INT NOT NULL UNIQUE,
            form_title VARCHAR(255) DEFAULT 'Join Our Exclusive Offers',
            form_description TEXT,
            show_email BOOLEAN DEFAULT FALSE,
            whatsapp_optin BOOLEAN DEFAULT TRUE,
            thank_you_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE,
            INDEX idx_shop_id (shop_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    conn.commit()
    print("✓ Table created")
    
    print("\nInserting default settings for existing shops...")
    cursor.execute("""
        INSERT IGNORE INTO lead_form_settings (shop_id, form_description, thank_you_message)
        SELECT id, 
               'Register now to receive special offers and updates',
               'Thank you for registering! You will receive exclusive offers soon.'
        FROM shops
    """)
    conn.commit()
    print(f"✓ Added settings for {cursor.rowcount} shops")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Migration completed successfully!")
    print("Restart your Flask app now.")
    
except Exception as e:
    print(f"\n❌ Error: {e}")

input("\nPress Enter to exit...")
