# Rohidas Footwear - Multi-Tenant SaaS Shop Management System

A production-ready Flask application for managing multiple footwear shops with QR-based customer lead capture system.

## Features

- **Multi-Tenant Architecture**: Manage multiple shops from a single admin panel
- **Three User Roles**: Admin, Shop Manager, Marketing Manager
- **QR Lead Capture**: Generate QR codes for customer registration
- **Product Management**: Categories, products, offers, and inventory
- **Website Customization**: Per-shop website settings and branding
- **Shop Statistics**: Track products, orders, and revenue
- **Secure Authentication**: Bcrypt password hashing, session management
- **Clean Architecture**: Blueprints, utilities, and organized structure

## Project Structure

```
ROHIDAS_FOOTWEAR/
│
├── app.py                      # Main Flask application
├── config.py                   # Database configuration
├── requirements.txt            # Python dependencies
│
├── instance/
│   └── rohidas_footwear.sql   # Complete database schema
│
├── routes/
│   ├── admin_routes.py        # Admin shop management
│   ├── auth_routes.py         # Authentication (login/logout)
│   ├── main_routes.py         # Home and common routes
│   ├── marketing_routes.py    # QR generator & customer leads
│   └── shop_routes.py         # Shop dashboard & products
│
├── utils/
│   ├── __init__.py
│   ├── slug_generator.py      # URL slug generation
│   └── helpers.py             # Common utilities
│
├── static/
│   ├── css/                   # Stylesheets
│   ├── js/                    # JavaScript files
│   └── uploads/               # Product images & uploads
│
└── templates/
    ├── base.html              # Base template
    ├── home.html              # Landing page
    ├── admin/                 # Admin templates
    ├── auth/                  # Login templates
    ├── dashboard/             # Dashboard templates
    ├── marketing/             # Marketing templates
    └── public/                # Public-facing templates
```

## Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd rohidas_footwear
```

### 2. Create Virtual Environment
```bash
python -m venv venv
```

### 3. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Database

Edit `config.py` with your MySQL credentials:
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',
    'database': 'rohidas_footwear'
}
```

### 6. Setup Database

**Windows PowerShell:**
```powershell
Get-Content instance/rohidas_footwear.sql | mysql -u root -p
```

**Linux/Mac:**
```bash
mysql -u root -p < instance/rohidas_footwear.sql
```

### 7. Run Application
```bash
python app.py
```

Visit: `http://127.0.0.1:5000`

## Default Login Credentials

### Admin
- **Email**: admin@rohidas.com
- **Password**: admin123
- **Access**: `/admin/login`

### Shop Manager
- **Email**: shop@rohidas.com
- **Password**: admin123
- **Access**: `/shop/login`

### Marketing Manager
- **Email**: marketing@rohidas.com
- **Password**: marketing123
- **Access**: `/marketing/login`

## Key Features

### Admin Panel
- Create and manage multiple shops
- Auto-generate shop credentials
- View shop statistics
- Activate/deactivate shops
- Delete shops with cascade cleanup

### Shop Dashboard
- Manage products and categories
- Upload product images
- Create offers and discounts
- Customize website settings
- View shop statistics

### Marketing Dashboard
- Generate QR codes for shops
- View customer leads
- Export leads to CSV
- Track lead sources
- Campaign overview

### QR Lead Capture
- Public registration form: `/shop/<shop-slug>/join`
- Customer data collection (name, phone)
- Duplicate prevention
- WhatsApp integration
- Source tracking

## Database Schema

### Core Tables
- `admins` - Admin users
- `shops` - Shop information with slugs
- `shop_stats` - Shop statistics
- `marketing_users` - Marketing team users

### Product Tables
- `categories` - Product categories per shop
- `products` - Products with images and pricing
- `offers` - Discount offers

### Marketing Tables
- `customers` - QR lead captures
- `website_settings` - Per-shop customization

## Utilities

### Slug Generator (`utils/slug_generator.py`)
```python
from utils import generate_slug

slug = generate_slug("Main Store")  # Returns: "main-store"
```

### Password Hashing (`utils/helpers.py`)
```python
from utils import hash_password, verify_password

hashed = hash_password("password123")
is_valid = verify_password("password123", hashed)
```

### Email/Phone Validation
```python
from utils import validate_email, validate_phone

is_valid_email = validate_email("user@example.com")
is_valid_phone = validate_phone("+91 1234567890")
```

## API Routes

### Admin Routes (`/admin`)
- `GET /admin/shops` - List all shops
- `GET /admin/shops/add` - Add shop form
- `POST /admin/shops/add` - Create shop
- `GET /admin/shops/edit/<id>` - Edit shop form
- `POST /admin/shops/edit/<id>` - Update shop
- `GET /admin/shops/view/<id>` - View shop details
- `POST /admin/shops/delete/<id>` - Delete shop
- `POST /admin/shops/toggle-status/<id>` - Toggle active status

### Marketing Routes (`/marketing`)
- `GET /marketing/qr-generator` - QR code generator
- `GET /marketing/generate-qr/<shop_id>` - Download QR code
- `GET /marketing/customer-leads` - View all leads
- `GET /marketing/export-customers` - Export CSV

### Public Routes
- `GET /shop/<shop_slug>/join` - Registration form
- `POST /shop/<shop_slug>/join` - Submit registration

## Security Features

- ✅ Bcrypt password hashing
- ✅ Session-based authentication
- ✅ Role-based access control
- ✅ CSRF protection
- ✅ SQL injection prevention (parameterized queries)
- ✅ Input validation and sanitization
- ✅ Unique constraints on emails and slugs

## Production Deployment

### Environment Variables
Create `.env` file:
```
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
DB_HOST=localhost
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=rohidas_footwear
```

### WSGI Server (Gunicorn)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /path/to/rohidas_footwear/static;
    }
}
```

## Troubleshooting

### Database Connection Error
- Check MySQL is running
- Verify credentials in `config.py`
- Ensure database exists: `CREATE DATABASE rohidas_footwear;`

### Import Errors
- Activate virtual environment
- Install dependencies: `pip install -r requirements.txt`

### Upload Errors
- Check `static/uploads/` folder permissions
- Ensure folder exists and is writable

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## License

This project is proprietary software for Rohidas Footwear.

## Support

For issues and questions:
- Email: support@rohidas.com
- Documentation: See `/docs` folder

## Version History

- **v1.0.0** - Initial release with multi-tenant architecture
- **v1.1.0** - Added QR lead capture system
- **v1.2.0** - Restructured for production deployment

---

**Built with ❤️ using Flask, MySQL, and Bootstrap 5**
