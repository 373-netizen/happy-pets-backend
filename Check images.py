"""
Diagnostic script to check image paths and database records
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.conf import settings
from products.models import Product

print("\n" + "="*70)
print("🔍 IMAGE DIAGNOSTIC CHECK")
print("="*70)

# Check Django settings
print(f"\n📁 Django Media Configuration:")
print(f"   MEDIA_ROOT: {settings.MEDIA_ROOT}")
print(f"   MEDIA_URL: {settings.MEDIA_URL}")

# Check if media/products directory exists
products_dir = os.path.join(settings.MEDIA_ROOT, 'products')
print(f"\n📂 Products Directory: {products_dir}")
print(f"   Exists: {os.path.exists(products_dir)}")

if os.path.exists(products_dir):
    files = os.listdir(products_dir)
    print(f"   Files in directory: {len(files)}")
    if files:
        print(f"   First 10 files:")
        for f in files[:10]:
            print(f"      - {f}")
else:
    print("   ❌ Directory does not exist!")

# Check database records
print(f"\n💾 Database Check:")
products = Product.objects.all()[:10]
print(f"   Total products: {Product.objects.count()}")
print(f"\n   First 10 products image_url:")

for p in products:
    has_image = "✅" if p.image_url else "❌"
    print(f"   {has_image} ID {p.id}: {p.name[:40]}")
    print(f"      image_url: '{p.image_url}'")
    
    if p.image_url:
        # Check if file actually exists
        full_path = os.path.join(settings.MEDIA_ROOT, p.image_url)
        exists = os.path.exists(full_path)
        print(f"      File exists: {exists} ({full_path})")

print("\n" + "="*70)

# Count products with/without images
with_images = Product.objects.exclude(image_url='').count()
without_images = Product.objects.filter(image_url='').count()

print(f"\n📊 Summary:")
print(f"   Products WITH images: {with_images}")
print(f"   Products WITHOUT images: {without_images}")
print("\n" + "="*70)