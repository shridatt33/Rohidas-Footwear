from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import config

auth_bp = Blueprint('auth', __name__)

# Admin Login Routes
@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            conn = config.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM admins WHERE email = %s AND password = %s", (email, password))
            admin = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if admin:
                session['user_id'] = admin['id']
                session['user_type'] = 'admin'
                session['user_name'] = admin['name']
                return redirect(url_for('auth.admin_dashboard'))
            else:
                flash('Invalid credentials', 'danger')
        except Exception as e:
            flash('Database connection error', 'danger')
    
    return render_template('auth/admin_login.html')

@auth_bp.route('/admin/dashboard')
def admin_dashboard():
    if 'user_type' in session and session['user_type'] == 'admin':
        return render_template('dashboard/admin_dashboard.html', user_name=session.get('user_name'))
    return redirect(url_for('auth.admin_login'))

# Shop Login Routes
@auth_bp.route('/shop/login', methods=['GET', 'POST'])
def shop_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            conn = config.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM shops WHERE email = %s", (email,))
            shop = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if shop:
                # Check if shop is active
                if shop['status'] != 'Active':
                    flash('Your shop is temporarily disabled. Contact Admin.', 'error')
                    return redirect(url_for('auth.shop_login'))
                
                # Verify password (assuming bcrypt hashed passwords)
                import bcrypt
                if bcrypt.checkpw(password.encode('utf-8'), shop['password_hash'].encode('utf-8')):
                    session['user_id'] = shop['id']
                    session['shop_id'] = shop['id']
                    session['user_type'] = 'shop'
                    session['user_name'] = shop['owner_name']
                    session['shop_slug'] = shop['shop_slug']
                    return redirect(url_for('auth.shop_dashboard'))
                else:
                    flash('Invalid email or password', 'error')
            else:
                flash('Invalid email or password', 'error')
        except Exception as e:
            flash('Database connection error', 'error')
    
    return render_template('auth/shop_login.html')

@auth_bp.route('/shop/dashboard')
def shop_dashboard():
    if 'user_type' in session and session['user_type'] == 'shop':
        shop_id = session['user_id']
        
        conn = config.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) as total FROM products WHERE shop_id = %s", (shop_id,))
        total_products = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM categories WHERE shop_id = %s", (shop_id,))
        total_categories = cursor.fetchone()['total']
        
        cursor.execute("SELECT * FROM products WHERE shop_id = %s ORDER BY created_at DESC LIMIT 5", (shop_id,))
        recent_products = cursor.fetchall()
        
        cursor.execute("SELECT shop_name FROM shops WHERE id = %s", (shop_id,))
        shop_info = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return render_template('dashboard/shop_dashboard.html', 
                             user_name=session.get('user_name'),
                             total_products=total_products,
                             total_categories=total_categories,
                             recent_products=recent_products,
                             shop_name=shop_info['shop_name'] if shop_info else None)
    return redirect(url_for('auth.shop_login'))

# Marketing Login Routes
@auth_bp.route('/marketing/login', methods=['GET', 'POST'])
def marketing_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            conn = config.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM marketing_users WHERE email = %s AND password = %s", (email, password))
            marketing = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if marketing:
                session['user_id'] = marketing['id']
                session['user_type'] = 'marketing'
                session['user_name'] = marketing['name']
                return redirect(url_for('auth.marketing_dashboard'))
            else:
                flash('Invalid credentials', 'danger')
        except Exception as e:
            flash('Database connection error', 'danger')
    
    return render_template('auth/marketing_login.html')

@auth_bp.route('/marketing/dashboard')
def marketing_dashboard():
    if 'user_type' in session and session['user_type'] == 'marketing':
        return render_template('dashboard/marketing_dashboard.html', user_name=session.get('user_name'))
    return redirect(url_for('auth.marketing_login'))

# Logout Route
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.home'))
