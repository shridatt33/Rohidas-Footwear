"""
Test WhatsApp Group Link Feature
"""
import mysql.connector
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

try:
    print("="*60)
    print("TESTING WHATSAPP GROUP LINK FEATURE")
    print("="*60)
    
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )
    cursor = conn.cursor(dictionary=True)
    
    # Test 1: Check if column exists
    print("\n1. Checking if whatsapp_group_link column exists...")
    cursor.execute("SHOW COLUMNS FROM lead_form_settings LIKE 'whatsapp_group_link'")
    if cursor.fetchone():
        print("   ✅ Column exists")
    else:
        print("   ❌ Column NOT found")
        print("   Run: python add_whatsapp_group_link.py")
    
    # Test 2: Check current settings
    print("\n2. Checking current form settings...")
    cursor.execute("""
        SELECT s.shop_name, lfs.whatsapp_group_link
        FROM shops s
        LEFT JOIN lead_form_settings lfs ON s.id = lfs.shop_id
        WHERE s.status = 'Active'
    """)
    shops = cursor.fetchall()
    
    if shops:
        for shop in shops:
            link_status = "✅ Configured" if shop['whatsapp_group_link'] else "⚠️  Not Set"
            print(f"   Shop: {shop['shop_name']}")
            print(f"   WhatsApp Link: {link_status}")
            if shop['whatsapp_group_link']:
                print(f"   Link: {shop['whatsapp_group_link']}")
    else:
        print("   ⚠️  No active shops found")
    
    # Test 3: Test link validation
    print("\n3. Testing link validation...")
    import re
    
    test_links = [
        ("https://chat.whatsapp.com/ABC123", True),
        ("https://wa.me/ABC123", True),
        ("http://chat.whatsapp.com/ABC123", True),
        ("https://example.com", False),
        ("chat.whatsapp.com/ABC123", False),
        ("", True),  # Empty is valid (optional field)
    ]
    
    pattern = r'^https?://(chat\.whatsapp\.com|wa\.me)/[a-zA-Z0-9]+$'
    
    for link, should_pass in test_links:
        if link == "":
            result = "✅ PASS (empty allowed)"
        else:
            is_valid = bool(re.match(pattern, link))
            if is_valid == should_pass:
                result = "✅ PASS"
            else:
                result = "❌ FAIL"
        print(f"   {result}: {link if link else '(empty)'}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETED")
    print("="*60)
    print("\nNext steps:")
    print("1. Restart Flask app: python app.py")
    print("2. Login as marketing manager")
    print("3. Go to QR Lead Generator")
    print("4. Click 'Edit Lead Form'")
    print("5. Add WhatsApp group link")
    print("6. Test registration form")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

input("\nPress Enter to exit...")
