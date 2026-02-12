"""
Check API configuration and test API calls
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.conf import settings

print("\n" + "="*70)
print("API CONFIGURATION CHECK")
print("="*70)

print("\n📋 Settings Configuration:")
print(f"   DOG_API_KEY: {getattr(settings, 'DOG_API_KEY', 'NOT FOUND')[:20]}...")
print(f"   CAT_API_KEY: {getattr(settings, 'CAT_API_KEY', 'NOT FOUND')[:20]}...")
print(f"   YOUTUBE_API_KEY: {getattr(settings, 'YOUTUBE_API_KEY', 'NOT FOUND')[:20]}...")
print(f"   NEWS_API_KEY: {getattr(settings, 'NEWS_API_KEY', 'NOT FOUND')[:20]}...")

print("\n🔍 Checking DogAPIService...")
try:
    from info.services.dog_api_service import DogAPIService
    
    # Check if service is using the API key
    service = DogAPIService()
    
    # Print the headers it's using
    print(f"   Service initialized: ✓")
    
    # Try to access the headers attribute
    if hasattr(service, 'headers'):
        print(f"   Headers configured: {service.headers}")
    else:
        print(f"   ⚠️  No headers attribute found")
    
    if hasattr(service, 'api_key'):
        print(f"   API Key set: {service.api_key[:20]}...")
    else:
        print(f"   ⚠️  No api_key attribute found")
        
except ImportError as e:
    print(f"   ❌ Import error: {e}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n🔍 Checking file location...")
import pathlib
base_dir = pathlib.Path(__file__).parent
info_dir = base_dir / 'info' / 'services'
print(f"   Looking for: {info_dir}")
print(f"   Exists: {info_dir.exists()}")

if info_dir.exists():
    print(f"\n   Files in info/services/:")
    for file in info_dir.glob('*.py'):
        print(f"      - {file.name}")

print("\n" + "="*70)