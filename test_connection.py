"""
Database Connection Test
Run this to diagnose database connection issues
"""
import mysql.connector
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

def test_connection():
    """Test database connection"""
    print("="*70)
    print("DATABASE CONNECTION TEST")
    print("="*70)
    
    print("\nConfiguration:")
    print(f"  Host: {MYSQL_HOST}")
    print(f"  User: {MYSQL_USER}")
    print(f"  Password: {'*' * len(MYSQL_PASSWORD)}")
    print(f"  Database: {MYSQL_DB}")
    
    # Test 1: Connect to MySQL server (without database)
    print("\n" + "-"*70)
    print("TEST 1: Connecting to MySQL server...")
    print("-"*70)
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        print("✅ SUCCESS: Connected to MySQL server")
        
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"   MySQL Version: {version[0]}")
        
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"❌ FAILED: {err}")
        print(f"   Error Code: {err.errno}")
        print("\nPossible solutions:")
        print("  1. Check if MySQL is running")
        print("  2. Verify username and password in config.py")
        print("  3. Check MySQL service status")
        return False
    
    # Test 2: Check if database exists
    print("\n" + "-"*70)
    print("TEST 2: Checking if database exists...")
    print("-"*70)
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        cursor = conn.cursor()
        
        cursor.execute("SHOW DATABASES")
        databases = [db[0] for db in cursor.fetchall()]
        
        if MYSQL_DB in databases:
            print(f"✅ SUCCESS: Database '{MYSQL_DB}' exists")
        else:
            print(f"⚠️  WARNING: Database '{MYSQL_DB}' does NOT exist")
            print(f"\nAvailable databases:")
            for db in databases:
                print(f"  - {db}")
            print(f"\nTo create database, run:")
            print(f"  mysql -u {MYSQL_USER} -p -e \"CREATE DATABASE {MYSQL_DB};\"")
        
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"❌ FAILED: {err}")
        return False
    
    # Test 3: Connect to specific database
    print("\n" + "-"*70)
    print("TEST 3: Connecting to specific database...")
    print("-"*70)
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB
        )
        print(f"✅ SUCCESS: Connected to database '{MYSQL_DB}'")
        
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        if tables:
            print(f"\n   Found {len(tables)} tables:")
            for table in tables:
                print(f"     - {table[0]}")
        else:
            print("\n   ⚠️  WARNING: No tables found in database")
            print("   Run: python setup_database.py")
        
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"❌ FAILED: {err}")
        print(f"   Error Code: {err.errno}")
        
        if err.errno == 1049:
            print(f"\n   Database '{MYSQL_DB}' does not exist!")
            print(f"   Run: python setup_database.py")
        return False
    
    # Test 4: Check shops table structure
    print("\n" + "-"*70)
    print("TEST 4: Checking shops table structure...")
    print("-"*70)
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB
        )
        cursor = conn.cursor()
        
        cursor.execute("DESCRIBE shops")
        columns = cursor.fetchall()
        
        print("   Shops table columns:")
        for col in columns:
            print(f"     - {col[0]} ({col[1]})")
        
        column_names = [col[0] for col in columns]
        
        if 'shop_slug' in column_names:
            print("\n   ✅ shop_slug column exists")
        else:
            print("\n   ❌ shop_slug column MISSING!")
            print("   Run: python setup_database.py")
        
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"❌ FAILED: {err}")
        if err.errno == 1146:
            print(f"   Table 'shops' does not exist!")
            print(f"   Run: python setup_database.py")
        return False
    
    # Test 5: Test get_db_connection() function
    print("\n" + "-"*70)
    print("TEST 5: Testing get_db_connection() function...")
    print("-"*70)
    try:
        from config import get_db_connection
        conn = get_db_connection()
        print("✅ SUCCESS: get_db_connection() works")
        conn.close()
    except Exception as err:
        print(f"❌ FAILED: {err}")
        return False
    
    # All tests passed
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED!")
    print("="*70)
    print("\nYour database connection is working correctly.")
    print("You can now run: python app.py")
    print("="*70)
    
    return True

if __name__ == "__main__":
    success = test_connection()
    
    if not success:
        print("\n" + "="*70)
        print("❌ SOME TESTS FAILED")
        print("="*70)
        print("\nRecommended action:")
        print("  1. Fix the errors shown above")
        print("  2. Run: python setup_database.py")
        print("  3. Run this test again")
        print("="*70)
    
    input("\nPress Enter to exit...")
