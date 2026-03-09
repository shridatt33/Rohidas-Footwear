from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
import config
from utils import generate_slug, hash_password, generate_password

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_type' not in session or session['user_type'] != 'admin':
            flash('Please log in as admin to access this page.', 'error')
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def create_default_data(shop_id, conn):
    """Create default website_settings and categories for new shop"""
    cursor = conn.cursor()
    try:
        # Create default website_settings
        cursor.execute("""
            INSERT INTO website_settings (shop_id, banner_title, banner_subtitle, footer_text)
            VALUES (%s, %s, %s, %s)
        """, (shop_id, 'Welcome to Our Store', 'Discover amazing products', '© 2024 All rights reserved.'))
        
        # Create default categories
        default_categories = ['Sports Shoes', 'Formal Shoes', 'Sandals', 'Casual Shoes']
        for category in default_categories:
            cursor.execute("INSERT INTO categories (shop_id, category_name) VALUES (%s, %s)", (shop_id, category))
        
        # Create shop_stats record
        cursor.execute("INSERT INTO shop_stats (shop_id) VALUES (%s)", (shop_id,))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error creating default data: {e}")

# Shop List Route
@admin_bp.route('/shops')
@admin_required
def list_shops():
    """List all shops with statistics"""
    try:
        conn = config.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get all shops with statistics
        cursor.execute("""
            SELECT s.*, 
                   COALESCE(ss.total_products, 0) as total_products,
                   COALESCE(ss.total_revenue, 0) as total_revenue
            FROM shops s
            LEFT JOIN shop_stats ss ON s.id = ss.shop_id
            ORDER BY s.created_at DESC
        """)
        shops = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('admin/shops.html', shops=shops)
    except Exception as e:
        flash(f'Error loading shops: {str(e)}', 'error')
        return redirect(url_for('auth.admin_dashboard'))

# Add Shop Routes
@admin_bp.route('/shops/add', methods=['GET', 'POST'])
@admin_required
def add_shop():
    """Add new shop"""
    if request.method == 'POST':
        shop_name = request.form.get('shop_name', '').strip()
        owner_name = request.form.get('owner_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        auto_generate = request.form.get('auto_generate_password') == 'on'
        
        # Validation
        if not shop_name or not owner_name or not email:
            flash('Shop name, owner name, and email are required', 'error')
            return redirect(request.url)
        
        # Generate or get password
        if auto_generate:
            password = generate_password()
            generated_password = password  # Store for display
        else:
            password = request.form.get('password', '').strip()
            generated_password = None
            if not password or len(password) < 8:
                flash('Password must be at least 8 characters', 'error')
                return redirect(request.url)
        
        # Generate slug
        shop_slug = generate_slug(shop_name)
        
        # Hash password
        password_hash = hash_password(password)
        
        try:
            conn = config.get_db_connection()
            cursor = conn.cursor()
            
            # Insert shop
            cursor.execute("""
                INSERT INTO shops (shop_name, shop_slug, owner_name, email, phone, password_hash, address, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'Active')
            """, (shop_name, shop_slug, owner_name, email, phone, password_hash, address))
            
            shop_id = cursor.lastrowid
            
            # Create default data
            create_default_data(shop_id, conn)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            if generated_password:
                flash(f'Shop created successfully! Generated Password: {generated_password} (Save this - it will not be shown again)', 'success')
            else:
                flash('Shop created successfully!', 'success')
            
            return redirect(url_for('admin.list_shops'))
            
        except Exception as e:
            if 'Duplicate entry' in str(e):
                if 'email' in str(e):
                    flash('This email is already registered', 'error')
                elif 'shop_slug' in str(e):
                    flash('A shop with this name already exists', 'error')
            else:
                flash(f'Error creating shop: {str(e)}', 'error')
            return redirect(request.url)
    
    return render_template('admin/add_shop.html')

# Edit Shop Routes
@admin_bp.route('/shops/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_shop(id):
    """Edit existing shop"""
    conn = config.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        shop_name = request.form.get('shop_name', '').strip()
        owner_name = request.form.get('owner_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        status = request.form.get('status', 'Active')
        password = request.form.get('password', '').strip()
        
        # Validation
        if not shop_name or not owner_name or not email:
            flash('Shop name, owner name, and email are required', 'error')
            return redirect(request.url)
        
        # Generate slug
        shop_slug = generate_slug(shop_name)
        
        try:
            # Update shop
            if password:
                # Update with new password
                password_hash = hash_password(password)
                cursor.execute("""
                    UPDATE shops 
                    SET shop_name=%s, shop_slug=%s, owner_name=%s, email=%s, phone=%s, address=%s, status=%s, password_hash=%s
                    WHERE id=%s
                """, (shop_name, shop_slug, owner_name, email, phone, address, status, password_hash, id))
            else:
                # Update without changing password
                cursor.execute("""
                    UPDATE shops 
                    SET shop_name=%s, shop_slug=%s, owner_name=%s, email=%s, phone=%s, address=%s, status=%s
                    WHERE id=%s
                """, (shop_name, shop_slug, owner_name, email, phone, address, status, id))
            
            conn.commit()
            flash('Shop updated successfully!', 'success')
            return redirect(url_for('admin.list_shops'))
            
        except Exception as e:
            conn.rollback()
            if 'Duplicate entry' in str(e):
                if 'email' in str(e):
                    flash('This email is already registered', 'error')
                elif 'shop_slug' in str(e):
                    flash('A shop with this name already exists', 'error')
            else:
                flash(f'Error updating shop: {str(e)}', 'error')
            return redirect(request.url)
        finally:
            cursor.close()
            conn.close()
    
    # GET request - load shop data
    cursor.execute("SELECT * FROM shops WHERE id = %s", (id,))
    shop = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not shop:
        flash('Shop not found', 'error')
        return redirect(url_for('admin.list_shops'))
    
    return render_template('admin/edit_shop.html', shop=shop)

# View Shop Details
@admin_bp.route('/shops/view/<int:id>')
@admin_required
def view_shop(id):
    """View shop details with products, categories, and statistics"""
    try:
        conn = config.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get shop info
        cursor.execute("SELECT * FROM shops WHERE id = %s", (id,))
        shop = cursor.fetchone()
        
        if not shop:
            flash('Shop not found', 'error')
            return redirect(url_for('admin.list_shops'))
        
        # Get statistics
        cursor.execute("SELECT * FROM shop_stats WHERE shop_id = %s", (id,))
        stats = cursor.fetchone()
        if not stats:
            stats = {'total_products': 0, 'total_orders': 0, 'total_revenue': 0}
        
        # Get products
        cursor.execute("SELECT * FROM products WHERE shop_id = %s ORDER BY created_at DESC LIMIT 10", (id,))
        products = cursor.fetchall()
        
        # Get categories
        cursor.execute("SELECT * FROM categories WHERE shop_id = %s", (id,))
        categories = cursor.fetchall()
        
        # Get website settings
        cursor.execute("SELECT * FROM website_settings WHERE shop_id = %s", (id,))
        settings = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return render_template('admin/view_shop.html', 
                             shop=shop, 
                             stats=stats, 
                             products=products, 
                             categories=categories,
                             settings=settings)
    except Exception as e:
        flash(f'Error loading shop details: {str(e)}', 'error')
        return redirect(url_for('admin.list_shops'))

# Toggle Shop Status
@admin_bp.route('/shops/toggle-status/<int:id>', methods=['POST'])
@admin_required
def toggle_status(id):
    """Toggle shop status between Active and Inactive"""
    try:
        conn = config.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get current status
        cursor.execute("SELECT status FROM shops WHERE id = %s", (id,))
        shop = cursor.fetchone()
        
        if not shop:
            flash('Shop not found', 'error')
            return redirect(url_for('admin.list_shops'))
        
        # Toggle status
        new_status = 'Inactive' if shop['status'] == 'Active' else 'Active'
        cursor.execute("UPDATE shops SET status = %s WHERE id = %s", (new_status, id))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        flash(f'Shop status changed to {new_status}', 'success')
    except Exception as e:
        flash(f'Error toggling status: {str(e)}', 'error')
    
    return redirect(url_for('admin.list_shops'))

# Delete Shop
@admin_bp.route('/shops/delete/<int:id>', methods=['POST'])
@admin_required
def delete_shop(id):
    """Delete shop and all related data"""
    try:
        conn = config.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get shop info
        cursor.execute("SELECT * FROM shops WHERE id = %s", (id,))
        shop = cursor.fetchone()
        
        if not shop:
            flash('Shop not found', 'error')
            return redirect(url_for('admin.list_shops'))
        
        # Delete shop (CASCADE will handle related data)
        cursor.execute("DELETE FROM shops WHERE id = %s", (id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        flash(f'Shop "{shop["shop_name"]}" deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting shop: {str(e)}', 'error')
    
    return redirect(url_for('admin.list_shops'))
