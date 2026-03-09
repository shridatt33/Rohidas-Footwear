"""
Slug Generator Utility
Generates URL-friendly slugs from shop names
"""
import re

def generate_slug(text):
    """
    Generate URL-friendly slug from text
    
    Args:
        text (str): Input text (e.g., shop name)
    
    Returns:
        str: URL-friendly slug
    
    Examples:
        >>> generate_slug("Main Store")
        'main-store'
        >>> generate_slug("Rohidas & Sons Footwear")
        'rohidas-and-sons-footwear'
    """
    if not text:
        return 'shop'
    
    # Convert to lowercase
    slug = text.lower()
    
    # Replace & with 'and'
    slug = re.sub(r'[&]', 'and', slug)
    
    # Replace spaces and underscores with hyphens
    slug = re.sub(r'[\s_]+', '-', slug)
    
    # Remove all special characters except hyphens
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    
    # Collapse multiple hyphens
    slug = re.sub(r'-+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Return slug or default
    return slug if slug else 'shop'

def ensure_unique_slug(slug, existing_slugs):
    """
    Ensure slug is unique by appending number if needed
    
    Args:
        slug (str): Base slug
        existing_slugs (list): List of existing slugs
    
    Returns:
        str: Unique slug
    
    Examples:
        >>> ensure_unique_slug("main-store", ["main-store"])
        'main-store-1'
    """
    if slug not in existing_slugs:
        return slug
    
    counter = 1
    while f"{slug}-{counter}" in existing_slugs:
        counter += 1
    
    return f"{slug}-{counter}"
