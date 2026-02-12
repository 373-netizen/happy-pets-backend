"""
Updated Django import script for granular pet product suggestions
Handles hierarchical categories and specific product types
WITH ENHANCED IMAGE DETECTION AND AUTO-FIX FOR DOUBLE EXTENSIONS
"""

import os
import django
import json
import shutil
from pathlib import Path

# ==================== CONFIGURATION ====================
SOURCE_IMAGE_FOLDER = r"C:\P_images"  # Using raw string for Windows paths
JSON_FILE_PATH = "products_1.json"
# ======================================================

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.conf import settings
from products.models import Product, ProductCategory, Brand

def setup_media_directory():
    """Create media/products directory"""
    media_root = settings.MEDIA_ROOT
    products_dir = os.path.join(media_root, 'products')
    
    if not os.path.exists(products_dir):
        os.makedirs(products_dir)
        print(f"✅ Created directory: {products_dir}")
    
    return products_dir

def fix_double_extensions(source_folder):
    """Fix double extensions like 1.jpg.jpeg -> 1.jpeg"""
    print("\n" + "="*70)
    print("🔧 FIXING DOUBLE EXTENSIONS")
    print("="*70)
    
    if not os.path.exists(source_folder):
        print(f"❌ Folder not found: {source_folder}")
        return 0
    
    fixed = 0
    errors = 0
    
    for filename in os.listdir(source_folder):
        # Check for various double extension patterns
        needs_fix = False
        new_filename = filename
        
        if '.jpg.jpeg' in filename.lower():
            new_filename = filename.replace('.jpg.jpeg', '.jpeg').replace('.jpg.JPEG', '.jpeg').replace('.JPG.jpeg', '.jpeg')
            needs_fix = True
        elif '.jpeg.jpeg' in filename.lower():
            new_filename = filename.replace('.jpeg.jpeg', '.jpeg').replace('.JPEG.jpeg', '.jpeg')
            needs_fix = True
        elif '.png.png' in filename.lower():
            new_filename = filename.replace('.png.png', '.png').replace('.PNG.png', '.png')
            needs_fix = True
        elif '.jpg.jpg' in filename.lower():
            new_filename = filename.replace('.jpg.jpg', '.jpg').replace('.JPG.jpg', '.jpg')
            needs_fix = True
        
        if needs_fix:
            old_path = os.path.join(source_folder, filename)
            new_path = os.path.join(source_folder, new_filename)
            
            try:
                os.rename(old_path, new_path)
                fixed += 1
                if fixed <= 10:  # Show first 10
                    print(f"  ✓ {filename} → {new_filename}")
                elif fixed == 11:
                    print(f"  ... (showing first 10, continuing ...)")
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"  ❌ Error renaming {filename}: {e}")
    
    print(f"\n✅ Fixed {fixed} files")
    if errors > 0:
        print(f"⚠️  {errors} errors occurred")
    print("="*70)
    return fixed

def find_and_copy_image(product_id, source_folder, dest_folder):
    """Find and copy product image - tries multiple naming patterns"""
    # Try different file patterns
    patterns = [
        f"{product_id}.jpg",
        f"{product_id}.jpeg",
        f"{product_id}.png",
        f"{product_id}.webp",
        f"{product_id}.JPG",
        f"{product_id}.JPEG",
        f"{product_id}.PNG",
        f"{product_id}.WEBP",
    ]
    
    for pattern in patterns:
        source_path = os.path.join(source_folder, pattern)
        
        if os.path.exists(source_path):
            # Use lowercase extension for destination
            ext = os.path.splitext(pattern)[1].lower()
            dest_filename = f"{product_id}{ext}"
            dest_path = os.path.join(dest_folder, dest_filename)
            
            try:
                shutil.copy2(source_path, dest_path)
                if product_id <= 5:  # Only show for first 5
                    print(f"  ✓ Copied: {pattern}")
                return f"products/{dest_filename}"
            except Exception as e:
                print(f"  ❌ Copy error: {e}")
                return None
    
    return None

def copy_image_from_json_path(image_path_from_json, product_id, dest_folder):
    """Copy image using path from JSON"""
    if not image_path_from_json:
        return None
    
    # Handle both absolute and relative paths
    if os.path.exists(image_path_from_json):
        try:
            # Extract just the filename
            filename = os.path.basename(image_path_from_json)
            # Ensure it has product_id in the name
            file_ext = os.path.splitext(filename)[1].lower()
            dest_filename = f"{product_id}{file_ext}"
            dest_path = os.path.join(dest_folder, dest_filename)
            
            shutil.copy2(image_path_from_json, dest_path)
            print(f"  ✓ Copied from JSON: {filename}")
            return f"products/{dest_filename}"
        except Exception as e:
            print(f"  ❌ JSON copy error: {e}")
            return None
    
    return None

def get_or_create_category(category_data):
    """
    Get or create category from category data
    
    category_data can be:
    - String: "food" → get/create category with name "food"
    - Dict: {"name": "Dry Food", "parent": "Food", "category_type": "food", ...}
    """
    if isinstance(category_data, str):
        # Simple string category
        category, created = ProductCategory.objects.get_or_create(
            name__iexact=category_data,
            defaults={
                'name': category_data.lower(),
                'slug': category_data.lower().replace(' ', '-')
            }
        )
        return category
    
    elif isinstance(category_data, dict):
        # Detailed category data
        name = category_data.get('name')
        parent_name = category_data.get('parent')
        
        # Get or create parent if specified
        parent = None
        if parent_name:
            parent, _ = ProductCategory.objects.get_or_create(
                name__iexact=parent_name,
                defaults={
                    'name': parent_name.title(),
                    'slug': parent_name.lower().replace(' ', '-')
                }
            )
        
        # Get or create category
        category, created = ProductCategory.objects.get_or_create(
            name__iexact=name,
            defaults={
                'name': name.title(),
                'slug': name.lower().replace(' ', '-'),
                'parent': parent,
                'category_type': category_data.get('category_type', ''),
                'sub_type': category_data.get('sub_type', ''),
                'species': category_data.get('species', 'all'),
                'icon': category_data.get('icon', ''),
                'description': category_data.get('description', ''),
            }
        )
        
        return category
    
    return None

def get_or_create_brand(brand_data):
    """Get or create brand"""
    if isinstance(brand_data, str):
        brand, created = Brand.objects.get_or_create(
            name__iexact=brand_data,
            defaults={
                'name': brand_data,
                'slug': brand_data.lower().replace(' ', '-')
            }
        )
        return brand
    
    elif isinstance(brand_data, dict):
        brand, created = Brand.objects.get_or_create(
            name__iexact=brand_data.get('name'),
            defaults={
                'name': brand_data.get('name'),
                'slug': brand_data.get('slug', brand_data.get('name').lower().replace(' ', '-')),
                'description': brand_data.get('description', ''),
                'website': brand_data.get('website', ''),
            }
        )
        return brand
    
    return None

def diagnose_image_folder(source_folder):
    """Diagnose image folder contents"""
    print("\n" + "="*70)
    print("🔍 IMAGE FOLDER DIAGNOSTICS")
    print("="*70)
    
    if not os.path.exists(source_folder):
        print(f"❌ Folder does NOT exist: {source_folder}")
        print("\nTry these paths:")
        print(f"   1. C:\\P_images")
        print(f"   2. C:\\Users\\{os.getenv('USERNAME')}\\P_images")
        print(f"   3. {os.getcwd()}\\P_images")
        return False
    
    print(f"✅ Folder exists: {source_folder}")
    
    try:
        all_files = os.listdir(source_folder)
        image_exts = ('.jpg', '.jpeg', '.png', '.webp')
        images = [f for f in all_files if f.lower().endswith(image_exts)]
        
        print(f"\n📊 Stats:")
        print(f"   Total files: {len(all_files)}")
        print(f"   Image files: {len(images)}")
        
        if images:
            print(f"\n📋 First 10 images:")
            for img in images[:10]:
                print(f"   - {img}")
        else:
            print(f"\n⚠️  No images found!")
            print(f"   Files in folder:")
            for f in all_files[:10]:
                print(f"   - {f}")
        
        # Check for numbered images
        print(f"\n🔢 Checking for numbered images (1-10):")
        found_count = 0
        for i in range(1, 11):
            found = False
            for ext in image_exts:
                if f"{i}{ext}" in all_files or f"{i}{ext.upper()}" in all_files:
                    print(f"   ✅ {i}{ext}")
                    found = True
                    found_count += 1
                    break
            if not found:
                print(f"   ❌ {i}.jpg not found")
        
        print(f"\n✅ Found {found_count}/10 numbered images")
        return len(images) > 0
        
    except Exception as e:
        print(f"❌ Error reading folder: {e}")
        return False

def import_products():
    print("="*70)
    print("🔧 PRODUCT IMPORT SCRIPT - ENHANCED")
    print("="*70)
    
    # FIX DOUBLE EXTENSIONS FIRST
    fixed_count = fix_double_extensions(SOURCE_IMAGE_FOLDER)
    
    if fixed_count > 0:
        print(f"\n✅ Auto-fixed {fixed_count} image filenames")
    
    # Diagnose image folder
    has_images = diagnose_image_folder(SOURCE_IMAGE_FOLDER)
    
    if not has_images:
        print("\n⚠️  WARNING: No images detected!")
        response = input("\nContinue anyway? (yes/no): ").lower().strip()
        if response not in ['yes', 'y']:
            print("❌ Import cancelled")
            return
    
    # Validate JSON
    if not os.path.exists(JSON_FILE_PATH):
        print(f"\n❌ ERROR: JSON file not found!")
        print(f"   Looking for: {JSON_FILE_PATH}")
        return
    
    print(f"\n✅ JSON file: {JSON_FILE_PATH}")
    
    # Setup media directory
    dest_folder = setup_media_directory()
    
    # Load JSON
    print(f"\n📥 Loading products from JSON...")
    try:
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            products_data = json.load(f)
    except Exception as e:
        print(f"❌ ERROR loading JSON: {str(e)}")
        return
    
    print(f"✅ Loaded {len(products_data)} products")
    
    # Process products
    print(f"\n🔄 Processing products...")
    print("="*70)
    
    stats = {
        'created': 0,
        'updated': 0,
        'images_copied': 0,
        'images_missing': 0,
        'categories_created': set(),
        'brands_created': set(),
        'errors': []
    }
    
    for item in products_data:
        try:
            product_id = item.get('id')
            
            # Show progress every 50 items (less verbose)
            if product_id % 50 == 1 or product_id <= 5:
                print(f"\n📦 Product {product_id}: {item.get('name', 'Unknown')[:40]}")
            
            # Try to copy image
            image_path = None
            
            # Method 1: Try JSON path first
            json_image_path = item.get('image', '')
            if json_image_path:
                image_path = copy_image_from_json_path(json_image_path, product_id, dest_folder)
            
            # Method 2: Search by ID
            if not image_path:
                image_path = find_and_copy_image(product_id, SOURCE_IMAGE_FOLDER, dest_folder)
            
            # Track statistics
            if image_path:
                stats['images_copied'] += 1
            else:
                stats['images_missing'] += 1
                if product_id <= 5:  # Only show warnings for first 5
                    print(f"  ⚠️  No image found")
                image_path = ""
            
            # Get or create category
            category_data = item.get('category', '')
            category_obj = get_or_create_category(category_data) if category_data else None
            
            if category_obj:
                stats['categories_created'].add(str(category_obj))
            
            # Get or create brand
            brand_data = item.get('brand', '')
            brand_obj = get_or_create_brand(brand_data) if brand_data else None
            
            if brand_obj:
                stats['brands_created'].add(brand_obj.name)
            
            # Prepare defaults
            defaults = {
                'name': item.get('name'),
                'description': item.get('description', ''),
                'species': item.get('species', 'dog'),
                'price': item.get('price', 0),
                'original_price': item.get('original_price'),
                'image_url': image_path,
                'rating': item.get('rating', 0.0),
                'review_count': item.get('review_count', 0),
                'stock': item.get('stock', 0),
                'is_trending': item.get('is_trending', False),
                'is_featured': item.get('is_featured', False),
                'is_recommended': item.get('is_recommended', False),
                'platform_links': item.get('available_on', {}),
                'tags': item.get('tags', []),
                
                # Product type fields
                'food_type': item.get('food_type', ''),
                'toy_type': item.get('toy_type', ''),
                'grooming_type': item.get('grooming_type', ''),
                'health_type': item.get('health_type', ''),
                
                # Additional attributes
                'age_group': item.get('age_group', 'all'),
                'size_suitability': item.get('size_suitability', 'all'),
                'suitable_breeds': item.get('suitable_breeds', []),
                'material': item.get('material', ''),
                'color': item.get('color', ''),
                'weight': item.get('weight', ''),
                'dimensions': item.get('dimensions', ''),
            }
            
            # Add category and brand if available
            if category_obj:
                defaults['category'] = category_obj
            if brand_obj:
                defaults['brand'] = brand_obj
            
            # Create or update product
            product, created = Product.objects.update_or_create(
                id=product_id,
                defaults=defaults
            )
            
            if created:
                stats['created'] += 1
            else:
                stats['updated'] += 1
            
            # Progress indicator
            total = stats['created'] + stats['updated']
            if total % 50 == 0:
                print(f"\n{'─'*70}")
                print(f"✓ Progress: {total}/{len(products_data)} products")
                print(f"  Images: {stats['images_copied']} copied, {stats['images_missing']} missing")
                print(f"{'─'*70}")
                
        except Exception as e:
            error = f"Product {product_id}: {str(e)}"
            stats['errors'].append(error)
            if len(stats['errors']) <= 5:  # Show first 5 errors
                print(f"  ❌ ERROR: {e}")
    
    # Final report
    print("\n" + "="*70)
    print("✅ IMPORT COMPLETE!")
    print("="*70)
    print(f"\n📊 FINAL RESULTS:")
    print(f"   🆕 Created:         {stats['created']} products")
    print(f"   🔄 Updated:         {stats['updated']} products")
    print(f"   📷 Images copied:   {stats['images_copied']}")
    print(f"   ⚠️  Images missing:  {stats['images_missing']}")
    print(f"   📁 Categories:      {len(stats['categories_created'])}")
    print(f"   🏷️  Brands:          {len(stats['brands_created'])}")
    print(f"   ❌ Errors:          {len(stats['errors'])}")
    
    if stats['errors']:
        print(f"\n❌ ERRORS (showing first 10):")
        for error in stats['errors'][:10]:
            print(f"   • {error}")
    
    if stats['images_missing'] > 0:
        print(f"\n⚠️  IMAGE TROUBLESHOOTING:")
        print(f"   • {stats['images_missing']} products missing images")
        print(f"   • Check that files are named: 1.jpg, 2.jpg, etc.")
        print(f"   • Verify folder: {SOURCE_IMAGE_FOLDER}")
    
    print("\n" + "="*70)

if __name__ == '__main__':
    print("\n📋 CONFIGURATION:")
    print(f"   Images: {SOURCE_IMAGE_FOLDER}")
    print(f"   JSON:   {JSON_FILE_PATH}")
    
    print("\n" + "="*70)
    response = input("Start import? (yes/no): ").lower().strip()
    
    if response in ['yes', 'y']:
        import_products()
    else:
        print("\n❌ Import cancelled")