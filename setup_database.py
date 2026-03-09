"""
Database Setup Script
Run this to setup the complete database with all tables and sample data
"""
import mysql.connector
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

def setup_database():
    """Setup complete database from SQL file"""
    try:
        print("="*70)
        print("ROHIDAS FOOTWEAR - DATABASE SETUP")
        print("="*70)
        
        # Connect to MySQL (without database)
        print("\n1. Connecting to MySQL server...")
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        cursor = conn.cursor()
        print("   ✓ Connected successfully")
        
        # Create database if not exists
        print("\n2. Creating database...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB}")
        print(f"   ✓ Database '{MYSQL_DB}' ready")
        
        # Use database
        cursor.execute(f"USE {MYSQL_DB}")
        
        # Read SQL file
        print("\n3. Reading SQL file...")
        with open('instance/rohidas_footwear.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        print("   ✓ SQL file loaded")
        
        # Split into individual statements
        print("\n4. Executing SQL statements...")
        statements = sql_script.split(';')
        
        executed = 0
        for statement in statements:
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                    executed += 1
                except mysql.connector.Error as err:
                    # Ignore certain errors
                    if 'already exists' not in str(err).lower():
                        print(f"   ⚠ Warning: {err}")
        
        conn.commit()
        print(f"   ✓ Executed {executed} SQL statements")
        
        # Verify tables
        print("\n5. Verifying tables...")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print(f"   ✓ Created {len(tables)} tables:")
        for table in tables:
            print(f"     - {table[0]}")
        
        # Verify shops table structure
        print("\n6. Verifying shops table structure...")
        cursor.execute("DESCRIBE shops")
        columns = cursor.fetchall()
        
        column_names = [col[0] for col in columns]
        if 'shop_slug' in column_names:
            print("   ✓ shop_slug column exists")
        else:
            print("   ✗ shop_slug column MISSING!")
            return False
        
        # Check sample data
        print("\n7. Checking sample data...")
        cursor.execute("SELECT COUNT(*) FROM admins")
        admin_count = cursor.fetchone()[0]
        print(f"   ✓ Admins: {admin_count}")
        
        cursor.execute("SELECT COUNT(*) FROM shops")
        shop_count = cursor.fetchone()[0]
        print(f"   ✓ Shops: {shop_count}")
        
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        print(f"   ✓ Products: {product_count}")
        
        cursor.execute("SELECT COUNT(*) FROM categories")
        category_count = cursor.fetchone()[0]
        print(f"   ✓ Categories: {category_count}")
        
        # Show login credentials
        print("\n" + "="*70)
        print("✅ DATABASE SETUP COMPLETED SUCCESSFULLY!")
        print("="*70)
        
        print("\n📋 DEFAULT LOGIN CREDENTIALS:")
        print("\n1. ADMIN:")
        print("   Email: admin@rohidas.com")
        print("   Password: admin123")
        print("   URL: http://127.0.0.1:5001/admin/login")
        
        print("\n2. SHOP:")
        print("   Email: shop@rohidas.com")
        print("   Password: admin123")
        print("   URL: http://127.0.0.1:5001/shop/login")
        
        print("\n3. MARKETING:")
        print("   Email: marketing@rohidas.com")
        print("   Password: marketing123")
        print("   URL: http://127.0.0.1:5001/marketing/login")
        
        print("\n" + "="*70)
        print("🚀 NEXT STEPS:")
        print("   1. Run: python app.py")
        print("   2. Visit: http://127.0.0.1:5001")
        print("   3. Login with credentials above")
        print("="*70)
        
        cursor.close()
        conn.close()
        return True
        
    except mysql.connector.Error as err:
        print(f"\n❌ MySQL Error: {err}")
        print(f"   Error Code: {err.errno}")
        return False
    except FileNotFoundError:
        print("\n❌ Error: instance/rohidas_footwear.sql file not found!")
        print("   Make sure you're running this from the project root directory.")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n⚠️  WARNING: This will recreate the database!")
    print("   All existing data will be replaced with sample data.")
    
    response = input("\nDo you want to continue? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        success = setup_database()
        
        if success:
            print("\n✅ Setup completed successfully!")
        else:
            print("\n❌ Setup failed. Please check the errors above.")
    else:
        print("\n❌ Setup cancelled.")
    
    input("\nPress Enter to exit...")
