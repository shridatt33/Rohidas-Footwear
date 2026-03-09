from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file
import config
import qrcode
import io
import csv
from functools import wraps
import re

marketing_bp = Blueprint('marketing', __name__, url_prefix='/marketing')

# Marketing authentication decorator
def marketing_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_type' not in session or session['user_type'] != 'marketing':
            flash('Please log in as marketing user to access this page.', 'error')
            return redirect(url_for('auth.marketing_login'))
        return f(*args, **kwargs)
    return decorated_function

# QR Lead Generator Page
@marketing_bp.route('/qr-generator')
@marketing_required
def qr_generator():
    """Display QR code generator page with statistics"""
    try:
        conn = config.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get all active shops with statistics
        cursor.execute("""
            SELECT 
                s.id, 
                s.shop_name, 
                s.shop_slug,
                COUNT(DISTINCT c.id) as total_customers,
                COUNT(DISTINCT CASE 
                    WHEN MONTH(c.created_at) = MONTH(CURRENT_DATE()) 
                    AND YEAR(c.created_at) = YEAR(CURRENT_DATE()) 
                    THEN c.id 
                END) as customers_this_month
            FROM shops s
            LEFT JOIN customers c ON s.id = c.shop_id
            WHERE s.status = 'Active'
            GROUP BY s.id, s.shop_name, s.shop_slug
            ORDER BY s.shop_name
        """)
        shops = cursor.fetchall()
        
        # Get lead form settings for each shop
        for shop in shops:
            cursor.execute("""
                SELECT * FROM lead_form_settings WHERE shop_id = %s
            """, (shop['id'],))
            settings = cursor.fetchone()
            
            if not settings:
                # Create default settings if not exists
                cursor.execute("""
                    INSERT INTO lead_form_settings (shop_id) VALUES (%s)
                """, (shop['id'],))
                conn.commit()
                
                cursor.execute("""
                    SELECT * FROM lead_form_settings WHERE shop_id = %s
                """, (shop['id'],))
                settings = cursor.fetchone()
            
            shop['form_settings'] = settings
        
        cursor.close()
        conn.close()
        
        return render_template('marketing/qr_generator.html', shops=shops)
    except Exception as e:
        flash(f'Error loading QR generator: {str(e)}', 'error')
        return redirect(url_for('auth.marketing_dashboard'))

# Generate QR Code
@marketing_bp.route('/generate-qr/<int:shop_id>')
@marketing_required
def generate_qr(shop_id):
    """Generate QR code for shop"""
    try:
        conn = config.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get shop details
        cursor.execute("SELECT shop_slug FROM shops WHERE id = %s", (shop_id,))
        shop = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not shop:
            flash('Shop not found', 'error')
            return redirect(url_for('marketing.qr_generator'))
        
        # Generate QR code URL
        base_url = request.host_url.rstrip('/')
        join_url = f"{base_url}/shop/{shop['shop_slug']}/join"
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(join_url)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to bytes
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png', as_attachment=True, 
                        download_name=f'qr_code_{shop["shop_slug"]}.png')
    except Exception as e:
        flash(f'Error generating QR code: {str(e)}', 'error')
        return redirect(url_for('marketing.qr_generator'))

# Customer Leads Page
@marketing_bp.route('/customer-leads')
@marketing_required
def customer_leads():
    """Display customer leads"""
    try:
        conn = config.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get all customers with shop names
        cursor.execute("""
            SELECT c.*, s.shop_name 
            FROM customers c
            JOIN shops s ON c.shop_id = s.id
            ORDER BY c.created_at DESC
        """)
        customers = cursor.fetchall()
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) as total FROM customers")
        total_customers = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(DISTINCT shop_id) as total FROM customers")
        total_shops = cursor.fetchone()['total']
        
        cursor.close()
        conn.close()
        
        return render_template('marketing/customer_leads.html', 
                             customers=customers,
                             total_customers=total_customers,
                             total_shops=total_shops)
    except Exception as e:
        flash(f'Error loading customer leads: {str(e)}', 'error')
        return redirect(url_for('auth.marketing_dashboard'))

# Update Lead Form Settings
@marketing_bp.route('/update-form-settings/<int:shop_id>', methods=['POST'])
@marketing_required
def update_form_settings(shop_id):
    """Update lead form settings for a shop"""
    try:
        conn = config.get_db_connection()
        cursor = conn.cursor()
        
        # Get form data
        form_title = request.form.get('form_title', '').strip()
        form_description = request.form.get('form_description', '').strip()
        show_email = request.form.get('show_email') == 'on'
        whatsapp_optin = request.form.get('whatsapp_optin') == 'on'
        thank_you_message = request.form.get('thank_you_message', '').strip()
        whatsapp_group_link = request.form.get('whatsapp_group_link', '').strip()
        
        # Validate WhatsApp group link if provided
        if whatsapp_group_link:
            if not re.match(r'^https?://(chat\.whatsapp\.com|wa\.me)/[a-zA-Z0-9]+$', whatsapp_group_link):
                flash('Invalid WhatsApp group invite link. Must be in format: https://chat.whatsapp.com/xxxxx', 'error')
                return redirect(url_for('marketing.qr_generator'))
        
        # Update settings
        cursor.execute("""
            UPDATE lead_form_settings 
            SET form_title = %s,
                form_description = %s,
                show_email = %s,
                whatsapp_optin = %s,
                thank_you_message = %s,
                whatsapp_group_link = %s
            WHERE shop_id = %s
        """, (form_title, form_description, show_email, whatsapp_optin, thank_you_message, whatsapp_group_link, shop_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Form settings updated successfully!', 'success')
        return redirect(url_for('marketing.qr_generator'))
        
    except Exception as e:
        flash(f'Error updating form settings: {str(e)}', 'error')
        return redirect(url_for('marketing.qr_generator'))

# Export Customers to CSV
@marketing_bp.route('/export-customers')
@marketing_required
def export_customers():
    """Export customers to CSV"""
    try:
        conn = config.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get all customers
        cursor.execute("""
            SELECT c.name, c.phone, c.source, c.created_at, s.shop_name
            FROM customers c
            JOIN shops s ON c.shop_id = s.id
            ORDER BY c.created_at DESC
        """)
        customers = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Name', 'Phone', 'Shop', 'Source', 'Date'])
        
        # Write data
        for customer in customers:
            writer.writerow([
                customer['name'],
                customer['phone'],
                customer['shop_name'],
                customer['source'],
                customer['created_at'].strftime('%Y-%m-%d %H:%M') if customer['created_at'] else ''
            ])
        
        # Prepare response
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='customer_leads.csv'
        )
    except Exception as e:
        flash(f'Error exporting customers: {str(e)}', 'error')
        return redirect(url_for('marketing.customer_leads'))

# Edit Customer
@marketing_bp.route('/edit-customer/<int:customer_id>', methods=['POST'])
@marketing_required
def edit_customer(customer_id):
    """Edit customer details"""
    try:
        conn = config.get_db_connection()
        cursor = conn.cursor()
        
        # Get form data
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        
        # Validation
        if not name or not phone:
            flash('Name and phone are required', 'error')
            return redirect(url_for('marketing.customer_leads'))
        
        # Validate phone format
        if not re.match(r'^\+?[\d\s\-\(\)]{10,15}$', phone):
            flash('Invalid phone number format', 'error')
            return redirect(url_for('marketing.customer_leads'))
        
        # Update customer
        cursor.execute("""
            UPDATE customers 
            SET name = %s, phone = %s
            WHERE id = %s
        """, (name, phone, customer_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Customer updated successfully!', 'success')
        return redirect(url_for('marketing.customer_leads'))
        
    except Exception as e:
        if 'Duplicate entry' in str(e):
            flash('This phone number is already registered!', 'error')
        else:
            flash(f'Error updating customer: {str(e)}', 'error')
        return redirect(url_for('marketing.customer_leads'))

# Delete Customer
@marketing_bp.route('/delete-customer/<int:customer_id>', methods=['POST'])
@marketing_required
def delete_customer(customer_id):
    """Delete customer"""
    try:
        conn = config.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get customer info before deleting
        cursor.execute("SELECT name FROM customers WHERE id = %s", (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            flash('Customer not found', 'error')
            return redirect(url_for('marketing.customer_leads'))
        
        # Delete customer
        cursor.execute("DELETE FROM customers WHERE id = %s", (customer_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        flash(f'Customer "{customer["name"]}" deleted successfully!', 'success')
        return redirect(url_for('marketing.customer_leads'))
        
    except Exception as e:
        flash(f'Error deleting customer: {str(e)}', 'error')
        return redirect(url_for('marketing.customer_leads'))

# Public Join Form (No authentication required)
# This route is registered without the /marketing prefix
from flask import Blueprint as FlaskBlueprint

# Create a separate blueprint for public routes
public_bp = FlaskBlueprint('public', __name__)

@public_bp.route('/shop/<shop_slug>/join', methods=['GET', 'POST'])
def join_shop(shop_slug):
    """Public form for customers to join shop offers"""
    try:
        conn = config.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get shop details
        cursor.execute("SELECT * FROM shops WHERE shop_slug = %s AND status = 'Active'", (shop_slug,))
        shop = cursor.fetchone()
        
        if not shop:
            cursor.close()
            conn.close()
            return render_template('public/shop_not_found.html'), 404
        
        # Get form settings
        cursor.execute("SELECT * FROM lead_form_settings WHERE shop_id = %s", (shop['id'],))
        form_settings = cursor.fetchone()
        
        if not form_settings:
            # Create default settings
            cursor.execute("""
                INSERT INTO lead_form_settings (shop_id) VALUES (%s)
            """, (shop['id'],))
            conn.commit()
            cursor.execute("SELECT * FROM lead_form_settings WHERE shop_id = %s", (shop['id'],))
            form_settings = cursor.fetchone()
        
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip()
            email = request.form.get('email', '').strip() if form_settings['show_email'] else None
            whatsapp_consent = request.form.get('whatsapp_consent') == 'on' if form_settings['whatsapp_optin'] else True
            
            # Validation
            errors = []
            if not name:
                errors.append('Name is required')
            if not phone:
                errors.append('Phone number is required')
            elif not re.match(r'^\+?[\d\s\-\(\)]{10,15}$', phone):
                errors.append('Invalid phone number format')
            
            if form_settings['show_email'] and email:
                if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                    errors.append('Invalid email format')
            
            if errors:
                for error in errors:
                    flash(error, 'error')
                return render_template('public/join_form.html', shop=shop, form_settings=form_settings)
            
            try:
                # Insert customer
                cursor.execute("""
                    INSERT INTO customers (shop_id, name, phone, source)
                    VALUES (%s, %s, %s, 'QR')
                """, (shop['id'], name, phone))
                conn.commit()
                
                # Check if WhatsApp group link exists
                if form_settings and form_settings.get('whatsapp_group_link'):
                    # Redirect to WhatsApp group
                    whatsapp_link = form_settings['whatsapp_group_link']
                    cursor.close()
                    conn.close()
                    return redirect(whatsapp_link)
                else:
                    # Show success page
                    cursor.execute("SELECT whatsapp_number FROM website_settings WHERE shop_id = %s", (shop['id'],))
                    settings = cursor.fetchone()
                    whatsapp_number = settings['whatsapp_number'] if settings else None
                    
                    cursor.close()
                    conn.close()
                    
                    return render_template('public/join_success.html', 
                                         shop=shop, 
                                         form_settings=form_settings,
                                         whatsapp_number=whatsapp_number)
            except Exception as e:
                conn.rollback()
                if 'Duplicate entry' in str(e):
                    flash('This phone number is already registered!', 'error')
                else:
                    flash(f'Error saving data: {str(e)}', 'error')
                return render_template('public/join_form.html', shop=shop, form_settings=form_settings)
        
        cursor.close()
        conn.close()
        return render_template('public/join_form.html', shop=shop, form_settings=form_settings)
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template('public/shop_not_found.html'), 500
