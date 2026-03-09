from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import config
import os
from werkzeug.utils import secure_filename

shop_bp = Blueprint('shop', __name__)

UPLOAD_FOLDER = 'static/uploads'
PRODUCT_UPLOAD_FOLDER = 'static/uploads/products'
CATEGORY_UPLOAD_FOLDER = 'static/uploads/categories'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Shop Dashboard - Products Management
@shop_bp.route('/shop/dashboard/products')
def manage_products():
    if 'user_type' not in session or session['user_type'] != 'shop':
        return redirect(url_for('auth.shop_login'))
    
    shop_id = session['user_id']
    conn = config.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT p.*, c.category_name 
        FROM products p 
        LEFT JOIN categories c ON p.category_id = c.id 
        WHERE p.shop_id = %s 
        ORDER BY p.created_at DESC
    """, (shop_id,))
    products = cursor.fetchall()
    
    # Get images and variants for each product
    for product in products:
        cursor.execute("SELECT image_path FROM product_images WHERE product_id = %s", (product['id'],))
        product['images'] = cursor.fetchall()
        
        cursor.execute("SELECT size, price, stock FROM product_variants WHERE product_id = %s ORDER BY size", (product['id'],))
        product['variants'] = cursor.fetchall()
    
    cursor.execute("SELECT * FROM categories WHERE shop_id = %s", (shop_id,))
    categories = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('dashboard/manage_products.html', products=products, categories=categories)

@shop_bp.route('/shop/dashboard/products/add', methods=['POST'])
def add_product():
    if 'user_type' not in session or session['user_type'] != 'shop':
        return redirect(url_for('auth.shop_login'))
    
    shop_id = session['user_id']
    name = request.form.get('name')
    description = request.form.get('description')
    category_id = request.form.get('category_id')
    is_featured = 1 if request.form.get('is_featured') else 0
    
    # Get variants data (sizes with prices and stock)
    sizes = request.form.getlist('sizes[]')
    prices = request.form.getlist('prices[]')
    stocks = request.form.getlist('stocks[]')
    
    conn = config.get_db_connection()
    cursor = conn.cursor()
    
    # Insert product without price and stock (will use variants)
    cursor.execute("""
        INSERT INTO products (shop_id, name, description, price, stock, category_id, is_featured)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (shop_id, name, description, 0, 0, category_id, is_featured))
    product_id = cursor.lastrowid
    
    # Handle multiple image uploads
    if 'images' in request.files:
        files = request.files.getlist('images')
        os.makedirs(PRODUCT_UPLOAD_FOLDER, exist_ok=True)
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                import time
                filename = f"{int(time.time())}_{filename}"
                file.save(os.path.join(PRODUCT_UPLOAD_FOLDER, filename))
                
                cursor.execute("""
                    INSERT INTO product_images (product_id, image_path)
                    VALUES (%s, %s)
                """, (product_id, filename))
    
    # Insert variants (size-based pricing)
    if sizes and prices and stocks:
        for i in range(len(sizes)):
            if sizes[i].strip() and prices[i] and stocks[i]:
                cursor.execute("""
                    INSERT INTO product_variants (product_id, size, price, stock)
                    VALUES (%s, %s, %s, %s)
                """, (product_id, sizes[i].strip(), prices[i], stocks[i]))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Product added successfully!', 'success')
    return redirect(url_for('shop.manage_products'))

@shop_bp.route('/shop/dashboard/products/delete/<int:id>')
def delete_product(id):
    if 'user_type' not in session or session['user_type'] != 'shop':
        return redirect(url_for('auth.shop_login'))
    
    shop_id = session['user_id']
    conn = config.get_db_connection()
    cursor = conn.cursor()
    
    # Delete images from filesystem
    cursor.execute("SELECT image_path FROM product_images WHERE product_id = %s", (id,))
    images = cursor.fetchall()
    for img in images:
        try:
            os.remove(os.path.join(PRODUCT_UPLOAD_FOLDER, img[0]))
        except:
            pass
    
    # Delete product (cascade will delete images and sizes from DB)
    cursor.execute("DELETE FROM products WHERE id = %s AND shop_id = %s", (id, shop_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('shop.manage_products'))

@shop_bp.route('/shop/dashboard/products/edit/<int:id>')
def edit_product(id):
    if 'user_type' not in session or session['user_type'] != 'shop':
        return redirect(url_for('auth.shop_login'))
    
    shop_id = session['user_id']
    conn = config.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT p.*, c.category_name 
        FROM products p 
        LEFT JOIN categories c ON p.category_id = c.id 
        WHERE p.id = %s AND p.shop_id = %s
    """, (id, shop_id))
    product = cursor.fetchone()
    
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('shop.manage_products'))
    
    # Get images
    cursor.execute("SELECT * FROM product_images WHERE product_id = %s", (id,))
    product['images'] = cursor.fetchall()
    
    # Get variants (size-based pricing)
    cursor.execute("SELECT size, price, stock FROM product_variants WHERE product_id = %s ORDER BY size", (id,))
    product['variants'] = cursor.fetchall()
    
    # Get categories
    cursor.execute("SELECT * FROM categories WHERE shop_id = %s", (shop_id,))
    categories = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('dashboard/edit_product.html', product=product, categories=categories)

@shop_bp.route('/shop/dashboard/products/update/<int:id>', methods=['POST'])
def update_product(id):
    if 'user_type' not in session or session['user_type'] != 'shop':
        return redirect(url_for('auth.shop_login'))
    
    shop_id = session['user_id']
    name = request.form.get('name')
    description = request.form.get('description')
    category_id = request.form.get('category_id')
    is_featured = 1 if request.form.get('is_featured') else 0
    
    # Get variants data
    sizes = request.form.getlist('sizes[]')
    prices = request.form.getlist('prices[]')
    stocks = request.form.getlist('stocks[]')
    
    conn = config.get_db_connection()
    cursor = conn.cursor()
    
    # Update product (price and stock set to 0 as we use variants)
    cursor.execute("""
        UPDATE products 
        SET name=%s, description=%s, price=%s, stock=%s, category_id=%s, is_featured=%s
        WHERE id=%s AND shop_id=%s
    """, (name, description, 0, 0, category_id, is_featured, id, shop_id))
    
    # Handle new image uploads
    if 'images' in request.files:
        files = request.files.getlist('images')
        os.makedirs(PRODUCT_UPLOAD_FOLDER, exist_ok=True)
        
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                import time
                filename = f"{int(time.time())}_{filename}"
                file.save(os.path.join(PRODUCT_UPLOAD_FOLDER, filename))
                
                cursor.execute("""
                    INSERT INTO product_images (product_id, image_path)
                    VALUES (%s, %s)
                """, (id, filename))
    
    # Update variants - delete old and insert new
    cursor.execute("DELETE FROM product_variants WHERE product_id = %s", (id,))
    if sizes and prices and stocks:
        for i in range(len(sizes)):
            if sizes[i].strip() and prices[i] and stocks[i]:
                cursor.execute("""
                    INSERT INTO product_variants (product_id, size, price, stock)
                    VALUES (%s, %s, %s, %s)
                """, (id, sizes[i].strip(), prices[i], stocks[i]))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Product updated successfully!', 'success')
    return redirect(url_for('shop.manage_products'))

@shop_bp.route('/shop/dashboard/products/delete-image/<int:image_id>')
def delete_product_image(image_id):
    if 'user_type' not in session or session['user_type'] != 'shop':
        return redirect(url_for('auth.shop_login'))
    
    shop_id = session['user_id']
    conn = config.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Verify ownership
    cursor.execute("""
        SELECT pi.*, p.shop_id 
        FROM product_images pi
        JOIN products p ON pi.product_id = p.id
        WHERE pi.id = %s
    """, (image_id,))
    image = cursor.fetchone()
    
    if image and image['shop_id'] == shop_id:
        # Delete from filesystem
        try:
            os.remove(os.path.join(PRODUCT_UPLOAD_FOLDER, image['image_path']))
        except:
            pass
        
        # Delete from database
        cursor.execute("DELETE FROM product_images WHERE id = %s", (image_id,))
        conn.commit()
        flash('Image deleted successfully!', 'success')
    else:
        flash('Image not found', 'error')
    
    cursor.close()
    conn.close()
    
    return redirect(request.referrer or url_for('shop.manage_products'))

# Categories Management
@shop_bp.route('/shop/dashboard/categories')
def manage_categories():
    if 'user_type' not in session or session['user_type'] != 'shop':
        return redirect(url_for('auth.shop_login'))
    
    shop_id = session['user_id']
    conn = config.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM categories WHERE shop_id = %s", (shop_id,))
    categories = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('dashboard/manage_categories.html', categories=categories)

@shop_bp.route('/shop/dashboard/categories/add', methods=['POST'])
def add_category():
    if 'user_type' not in session or session['user_type'] != 'shop':
        return redirect(url_for('auth.shop_login'))
    
    shop_id = session['user_id']
    category_name = request.form.get('category_name')
    
    # Handle image upload
    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            import time
            filename = f"{int(time.time())}_{filename}"
            os.makedirs(CATEGORY_UPLOAD_FOLDER, exist_ok=True)
            file.save(os.path.join(CATEGORY_UPLOAD_FOLDER, filename))
            image_filename = filename
    
    conn = config.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO categories (shop_id, category_name, image) VALUES (%s, %s, %s)", (shop_id, category_name, image_filename))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Category added successfully!', 'success')
    return redirect(url_for('shop.manage_categories'))

@shop_bp.route('/shop/dashboard/categories/edit/<int:id>')
def edit_category(id):
    if 'user_type' not in session or session['user_type'] != 'shop':
        return redirect(url_for('auth.shop_login'))
    
    shop_id = session['user_id']
    conn = config.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM categories WHERE id = %s AND shop_id = %s", (id, shop_id))
    category = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not category:
        flash('Category not found', 'error')
        return redirect(url_for('shop.manage_categories'))
    
    return render_template('dashboard/edit_category.html', category=category)

@shop_bp.route('/shop/dashboard/categories/update/<int:id>', methods=['POST'])
def update_category(id):
    if 'user_type' not in session or session['user_type'] != 'shop':
        return redirect(url_for('auth.shop_login'))
    
    shop_id = session['user_id']
    category_name = request.form.get('category_name')
    
    conn = config.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get existing category
    cursor.execute("SELECT image FROM categories WHERE id = %s AND shop_id = %s", (id, shop_id))
    existing = cursor.fetchone()
    
    if not existing:
        flash('Category not found', 'error')
        return redirect(url_for('shop.manage_categories'))
    
    image_filename = existing['image']
    
    # Handle new image upload
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            # Delete old image
            if image_filename:
                try:
                    os.remove(os.path.join(CATEGORY_UPLOAD_FOLDER, image_filename))
                except:
                    pass
            
            filename = secure_filename(file.filename)
            import time
            filename = f"{int(time.time())}_{filename}"
            os.makedirs(CATEGORY_UPLOAD_FOLDER, exist_ok=True)
            file.save(os.path.join(CATEGORY_UPLOAD_FOLDER, filename))
            image_filename = filename
    
    cursor.execute("UPDATE categories SET category_name = %s, image = %s WHERE id = %s AND shop_id = %s", 
                   (category_name, image_filename, id, shop_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Category updated successfully!', 'success')
    return redirect(url_for('shop.manage_categories'))

@shop_bp.route('/shop/dashboard/categories/delete/<int:id>')
def delete_category(id):
    if 'user_type' not in session or session['user_type'] != 'shop':
        return redirect(url_for('auth.shop_login'))
    
    shop_id = session['user_id']
    conn = config.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get category image
    cursor.execute("SELECT image FROM categories WHERE id = %s AND shop_id = %s", (id, shop_id))
    category = cursor.fetchone()
    
    if category and category['image']:
        try:
            os.remove(os.path.join(CATEGORY_UPLOAD_FOLDER, category['image']))
        except:
            pass
    
    # Set products category_id to NULL
    cursor.execute("UPDATE products SET category_id = NULL WHERE category_id = %s AND shop_id = %s", (id, shop_id))
    
    # Delete category
    cursor.execute("DELETE FROM categories WHERE id = %s AND shop_id = %s", (id, shop_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('shop.manage_categories'))

# Website Settings
@shop_bp.route('/shop/dashboard/settings', methods=['GET', 'POST'])
def website_settings():
    if 'user_type' not in session or session['user_type'] != 'shop':
        return redirect(url_for('auth.shop_login'))
    
    shop_id = session['user_id']
    
    if request.method == 'POST':
        try:
            banner_title = request.form.get('banner_title')
            banner_subtitle = request.form.get('banner_subtitle')
            contact_number = request.form.get('contact_number')
            whatsapp_number = request.form.get('whatsapp_number')
            address = request.form.get('address')
            footer_text = request.form.get('footer_text')
            facebook_url = request.form.get('facebook_url')
            instagram_url = request.form.get('instagram_url')
            twitter_url = request.form.get('twitter_url')
            
            # Handle logo upload
            logo_filename = None
            if 'logo' in request.files:
                file = request.files['logo']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                    file.save(os.path.join(UPLOAD_FOLDER, filename))
                    logo_filename = filename
            
            # Handle hero image upload
            hero_image_filename = None
            if 'hero_image' in request.files:
                file = request.files['hero_image']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                    file.save(os.path.join(UPLOAD_FOLDER, filename))
                    hero_image_filename = filename
            
            conn = config.get_db_connection()
            cursor = conn.cursor()
            
            # Check if settings exist
            cursor.execute("SELECT logo, hero_image FROM website_settings WHERE shop_id = %s", (shop_id,))
            existing = cursor.fetchone()
            
            if existing:
                # Update with new images only if uploaded
                if not logo_filename:
                    logo_filename = existing[0]
                if not hero_image_filename:
                    hero_image_filename = existing[1]
            
            cursor.execute("""
                INSERT INTO website_settings 
                (shop_id, logo, hero_image, banner_title, banner_subtitle, contact_number, whatsapp_number, address, footer_text, facebook_url, instagram_url, twitter_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                logo=%s, hero_image=%s, banner_title=%s, banner_subtitle=%s, contact_number=%s, whatsapp_number=%s, address=%s, footer_text=%s, facebook_url=%s, instagram_url=%s, twitter_url=%s
            """, (shop_id, logo_filename, hero_image_filename, banner_title, banner_subtitle, contact_number, whatsapp_number, address, footer_text, facebook_url, instagram_url, twitter_url,
                  logo_filename, hero_image_filename, banner_title, banner_subtitle, contact_number, whatsapp_number, address, footer_text, facebook_url, instagram_url, twitter_url))
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Settings updated successfully!', 'success')
            return redirect(url_for('shop.website_settings'))
        except Exception as e:
            print(f"Error updating settings: {str(e)}")
            import traceback
            traceback.print_exc()
            flash(f'Error updating settings: {str(e)}', 'error')
            return redirect(url_for('shop.website_settings'))
    
    try:
        conn = config.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM website_settings WHERE shop_id = %s", (shop_id,))
        settings = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return render_template('dashboard/website_settings.html', settings=settings)
    except Exception as e:
        print(f"Error loading settings: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Error loading settings: {str(e)}", 500

# Offers Management
@shop_bp.route('/shop/dashboard/offers')
def manage_offers():
    if 'user_type' not in session or session['user_type'] != 'shop':
        return redirect(url_for('auth.shop_login'))
    
    shop_id = session['user_id']
    conn = config.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM offers WHERE shop_id = %s ORDER BY created_at DESC", (shop_id,))
    offers = cursor.fetchall()
    cursor.close()
    conn.close()
    
    from datetime import date
    today = date.today()
    
    return render_template('dashboard/manage_offers.html', offers=offers, today=today)

@shop_bp.route('/shop/dashboard/offers/add', methods=['POST'])
def add_offer():
    if 'user_type' not in session or session['user_type'] != 'shop':
        return redirect(url_for('auth.shop_login'))
    
    shop_id = session['user_id']
    title = request.form.get('title')
    discount_percent = request.form.get('discount_percent')
    valid_till = request.form.get('valid_till')
    
    conn = config.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO offers (shop_id, title, discount_percent, valid_till) VALUES (%s, %s, %s, %s)",
                   (shop_id, title, discount_percent, valid_till))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Offer added successfully!', 'success')
    return redirect(url_for('shop.manage_offers'))

# PUBLIC WEBSITE ROUTES
@shop_bp.route('/shop/<path:shop_name>')
def public_website(shop_name):
    try:
        conn = config.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # URL decode the shop name
        from urllib.parse import unquote
        shop_name = unquote(shop_name)
        
        print(f"DEBUG: Looking for shop_name: '{shop_name}'")
        
        cursor.execute("SELECT * FROM shops WHERE shop_name = %s", (shop_name,))
        shop = cursor.fetchone()
        
        print(f"DEBUG: Found shop: {shop}")
        
        if not shop:
            cursor.close()
            conn.close()
            return "Shop not found", 404
        
        shop_id = shop['id']
        
        cursor.execute("SELECT * FROM website_settings WHERE shop_id = %s", (shop_id,))
        settings = cursor.fetchone()
        
        cursor.execute("SELECT * FROM categories WHERE shop_id = %s", (shop_id,))
        categories = cursor.fetchall()
        
        cursor.execute("""
            SELECT p.*, c.category_name 
            FROM products p 
            LEFT JOIN categories c ON p.category_id = c.id 
            WHERE p.shop_id = %s AND p.is_featured = 1 
            ORDER BY p.created_at DESC LIMIT 6
        """, (shop_id,))
        featured_products = cursor.fetchall()
        
        # Get first image and variants for each featured product
        for product in featured_products:
            cursor.execute("SELECT image_path FROM product_images WHERE product_id = %s LIMIT 1", (product['id'],))
            img = cursor.fetchone()
            product['image'] = img['image_path'] if img else None
            
            cursor.execute("SELECT size, price, stock FROM product_variants WHERE product_id = %s ORDER BY size", (product['id'],))
            product['variants'] = cursor.fetchall()
        
        cursor.execute("""
            SELECT p.*, c.category_name 
            FROM products p 
            LEFT JOIN categories c ON p.category_id = c.id 
            WHERE p.shop_id = %s 
            ORDER BY p.created_at DESC
        """, (shop_id,))
        all_products = cursor.fetchall()
        
        # Get first image and variants for each product
        for product in all_products:
            cursor.execute("SELECT image_path FROM product_images WHERE product_id = %s LIMIT 1", (product['id'],))
            img = cursor.fetchone()
            product['image'] = img['image_path'] if img else None
            
            cursor.execute("SELECT size, price, stock FROM product_variants WHERE product_id = %s ORDER BY size", (product['id'],))
            product['variants'] = cursor.fetchall()
        
        cursor.execute("""
            SELECT * FROM offers 
            WHERE shop_id = %s AND valid_till >= CURDATE() AND is_active = 1 
            ORDER BY created_at DESC LIMIT 1
        """, (shop_id,))
        offer = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return render_template('public/shop_home.html', 
                             shop=shop, 
                             settings=settings, 
                             categories=categories,
                             featured_products=featured_products,
                             all_products=all_products,
                             offer=offer)
    except Exception as e:
        print(f"Error in public_website route: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Internal Server Error: {str(e)}", 500

@shop_bp.route('/shop/<shop_name>/products')
def public_products(shop_name):
    try:
        conn = config.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        from urllib.parse import unquote
        shop_name = unquote(shop_name)
        
        cursor.execute("SELECT * FROM shops WHERE shop_name = %s", (shop_name,))
        shop = cursor.fetchone()
        
        if not shop:
            cursor.close()
            conn.close()
            return "Shop not found", 404
        
        shop_id = shop['id']
        
        cursor.execute("SELECT * FROM website_settings WHERE shop_id = %s", (shop_id,))
        settings = cursor.fetchone()
        
        cursor.execute("SELECT p.*, c.category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE p.shop_id = %s", (shop_id,))
        products = cursor.fetchall()
        
        cursor.execute("SELECT * FROM categories WHERE shop_id = %s", (shop_id,))
        categories = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('public/shop_products.html', shop=shop, settings=settings, 
                             products=products, categories=categories)
    except Exception as e:
        print(f"Error in public_products route: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Internal Server Error: {str(e)}", 500

@shop_bp.route('/shop/<shop_name>/product/<int:product_id>')
def public_product_detail(shop_name, product_id):
    try:
        conn = config.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        from urllib.parse import unquote
        shop_name = unquote(shop_name)
        
        cursor.execute("SELECT * FROM shops WHERE shop_name = %s", (shop_name,))
        shop = cursor.fetchone()
        
        if not shop:
            cursor.close()
            conn.close()
            return "Shop not found", 404
        
        shop_id = shop['id']
        
        cursor.execute("SELECT * FROM website_settings WHERE shop_id = %s", (shop_id,))
        settings = cursor.fetchone()
        
        cursor.execute("SELECT p.*, c.category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE p.id = %s AND p.shop_id = %s", (product_id, shop_id))
        product = cursor.fetchone()
        
        if not product:
            cursor.close()
            conn.close()
            return "Product not found", 404
        
        # Get all images for the product
        cursor.execute("SELECT * FROM product_images WHERE product_id = %s", (product_id,))
        product['images'] = cursor.fetchall()
        
        # Get all variants (size-based pricing)
        cursor.execute("SELECT size, price, stock FROM product_variants WHERE product_id = %s ORDER BY size", (product_id,))
        variants_raw = cursor.fetchall()
        
        # Convert Decimal to float for JSON serialization
        product['variants'] = []
        for variant in variants_raw:
            product['variants'].append({
                'size': variant['size'],
                'price': float(variant['price']),
                'stock': variant['stock']
            })
        
        cursor.close()
        conn.close()
        
        import json
        variants_json = json.dumps(product['variants'])
        
        return render_template('public/product_detail.html', shop=shop, settings=settings, product=product, variants_json=variants_json)
    except Exception as e:
        print(f"Error in public_product_detail route: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Internal Server Error: {str(e)}", 500
