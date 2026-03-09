"""
Quick Database Setup - Fixes shop_slug error
"""
import mysql.connector
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

def quick_setup():
    try:
        print("Connecting to MySQL...")
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        cursor = conn.cursor()
        
        # Create database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB}")
        cursor.execute(f"USE {MYSQL_DB}")
        print(f"✓ Using database: {MYSQL_DB}")
        
        # Disable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        print("\n✓ Disabled foreign key checks")
        
        # Drop and recreate shops table with shop_slug
        print("\nFixing shops table...")
        cursor.execute("DROP TABLE IF EXISTS customers")
        cursor.execute("DROP TABLE IF EXISTS shop_stats")
        cursor.execute("DROP TABLE IF EXISTS shops")
        
        cursor.execute("""
            CREATE TABLE shops (
                id INT AUTO_INCREMENT PRIMARY KEY,
                shop_name VARCHAR(255) NOT NULL,
                shop_slug VARCHAR(255) NOT NULL UNIQUE,
                owner_name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                phone VARCHAR(20),
                password_hash VARCHAR(255) NOT NULL,
                address TEXT,
                status ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_email (email),
                INDEX idx_shop_slug (shop_slug),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✓ Created shops table with shop_slug")
        
        # Create shop_stats
        cursor.execute("""
            CREATE TABLE shop_stats (
                id INT AUTO_INCREMENT PRIMARY KEY,
                shop_id INT NOT NULL UNIQUE,
                total_products INT DEFAULT 0,
                total_orders INT DEFAULT 0,
                total_revenue DECIMAL(10, 2) DEFAULT 0.00,
                FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✓ Created shop_stats table")
        
        # Create customers table
        cursor.execute("""
            CREATE TABLE customers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                shop_id INT NOT NULL,
                name VARCHAR(255) NOT NULL,
                phone VARCHAR(20) NOT NULL,
                source VARCHAR(50) DEFAULT 'QR',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE,
                UNIQUE KEY unique_shop_phone (shop_id, phone),
                INDEX idx_shop_id (shop_id),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✓ Created customers table")
        
        # Re-enable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        print("✓ Re-enabled foreign key checks")
        
        # Insert sample shop
        cursor.execute("""
            INSERT INTO shops (shop_name, shop_slug, owner_name, email, phone, password_hash, address, status)
            VALUES ('Main Store', 'main-store', 'Admin User', 'shop@rohidas.com', '+91 1234567890',
                    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqgdMSL3WC',
                    'Mumbai, Maharashtra', 'Active')
        """)
        shop_id = cursor.lastrowid
        print(f"✓ Created sample shop (ID: {shop_id})")
        
        # Insert shop_stats
        cursor.execute("INSERT INTO shop_stats (shop_id) VALUES (%s)", (shop_id,))
        print("✓ Created shop_stats")
        
        # Update existing products to use new shop_id
        try:
            cursor.execute("UPDATE products SET shop_id = %s WHERE shop_id IS NULL OR shop_id = 0 OR shop_id = 1", (shop_id,))
            print("✓ Updated existing products")
        except:
            pass
        
        conn.commit()
        
        # Verify
        cursor.execute("SELECT id, shop_name, shop_slug, email FROM shops")
        shops = cursor.fetchall()
        
        print("\n" + "="*60)
        print("✅ SUCCESS! Database fixed!")
        print("="*60)
        print("\nShops in database:")
        for shop in shops:
            print(f"  ID: {shop[0]}, Name: {shop[1]}, Slug: {shop[2]}, Email: {shop[3]}")
        
        print("\nLogin credentials:")
        print("  Email: shop@rohidas.com")
        print("  Password: admin123")
        print("\nRestart Flask app now!")
        print("="*60)
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    quick_setup()
    input("\nPress Enter to exit...")
