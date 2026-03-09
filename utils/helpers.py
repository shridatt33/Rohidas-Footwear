"""
Helper Utilities
Common helper functions used across the application
"""
import bcrypt
import secrets
import string
import re

def hash_password(password):
    """
    Hash password using bcrypt
    
    Args:
        password (str): Plain text password
    
    Returns:
        str: Hashed password
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password, password_hash):
    """
    Verify password against hash
    
    Args:
        password (str): Plain text password
        password_hash (str): Hashed password
    
    Returns:
        bool: True if password matches, False otherwise
    """
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def generate_password(length=12):
    """
    Generate a secure random password
    
    Args:
        length (int): Password length (default: 12)
    
    Returns:
        str: Random password
    """
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password

def validate_email(email):
    """
    Validate email format
    
    Args:
        email (str): Email address
    
    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """
    Validate phone number format
    
    Args:
        phone (str): Phone number
    
    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r'^\+?[\d\s\-\(\)]{10,15}$'
    return re.match(pattern, phone) is not None

def format_currency(amount):
    """
    Format amount as currency
    
    Args:
        amount (float): Amount
    
    Returns:
        str: Formatted currency string
    """
    return f"₹{amount:,.2f}"

def sanitize_filename(filename):
    """
    Sanitize filename for safe storage
    
    Args:
        filename (str): Original filename
    
    Returns:
        str: Sanitized filename
    """
    # Remove path components
    filename = filename.split('/')[-1].split('\\')[-1]
    
    # Remove special characters
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    
    # Replace spaces with underscores
    filename = re.sub(r'\s+', '_', filename)
    
    return filename
