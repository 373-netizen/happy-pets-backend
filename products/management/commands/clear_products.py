# products/management/commands/clear_products.py
from django.core.management.base import BaseCommand
from products.models import Product, ProductCategory, Brand, ProductImage, SavedProduct, ProductView


class Command(BaseCommand):
    help = 'Clear all products data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Deleting all products data...')
        
        ProductView.objects.all().delete()
        self.stdout.write('✓ Deleted ProductViews')
        
        SavedProduct.objects.all().delete()
        self.stdout.write('✓ Deleted SavedProducts')
        
        ProductImage.objects.all().delete()
        self.stdout.write('✓ Deleted ProductImages')
        
        Product.objects.all().delete()
        self.stdout.write('✓ Deleted Products')
        
        ProductCategory.objects.all().delete()
        self.stdout.write('✓ Deleted Categories')
        
        Brand.objects.all().delete()
        self.stdout.write('✓ Deleted Brands')
        
        self.stdout.write(self.style.SUCCESS('All products data deleted!'))