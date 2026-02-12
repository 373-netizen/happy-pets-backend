# products/management/commands/import_real_products.py
from django.core.management.base import BaseCommand
from products.scrapers.product_scraper import import_products_to_database # type: ignore

class Command(BaseCommand):
    help = 'Import real pet products from curated dataset'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting import of real pet products...'))
        
        count = import_products_to_database()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully imported {count} products!')
        )