"""
Enhanced Pre-warming Command for ALL 100+ Breeds
Place this at: info/management/commands/prewarm_breeds.py
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.core.cache import cache
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


class Command(BaseCommand):
    help = 'Pre-warm breed image cache with smart batching for 100+ breeds'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=110,
            help='Number of breeds to pre-warm (default: 110)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force refresh even if already cached',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of breeds per batch (default: 10)',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.5,
            help='Delay between batches in seconds (default: 0.5)',
        )
        parser.add_argument(
            '--workers',
            type=int,
            default=5,
            help='Number of concurrent workers (default: 5)',
        )

    def handle(self, *args, **options):
        from info.views import ALL_DOG_BREEDS, BREED_SLUG_TO_DOGCEO
        
        count = min(options['count'], len(ALL_DOG_BREEDS))
        batch_size = options['batch_size']
        delay = options['delay']
        force = options['force']
        workers = options['workers']
        
        breeds_to_warm = ALL_DOG_BREEDS[:count]
        
        # Header
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('🚀 BREED IMAGE CACHE PRE-WARMING'))
        self.stdout.write('='*70)
        self.stdout.write(f'Total breeds: {count}')
        self.stdout.write(f'Batch size: {batch_size} breeds')
        self.stdout.write(f'Delay between batches: {delay}s')
        self.stdout.write(f'Concurrent workers: {workers}')
        self.stdout.write(f'Force refresh: {"Yes" if force else "No"}')
        self.stdout.write('='*70 + '\n')
        
        total_success = 0
        total_skip = 0
        total_fail = 0
        total_fallback = 0
        
        start_time = time.time()
        
        def fetch_and_cache(breed_name):
            """Fetch and cache a single breed image"""
            slug = slugify(breed_name)
            cache_key = f'img_v3_{slug}'
            
            # Skip if cached (unless force)
            if not force and cache.get(cache_key):
                return 'skip', breed_name, None
            
            dogceo_breed = BREED_SLUG_TO_DOGCEO.get(slug)
            
            if not dogceo_breed:
                # No Dog CEO mapping - use fallback
                fallback_url = f'https://source.unsplash.com/400x300/?{breed_name.replace(" ", "+")}+dog'
                cache.set(cache_key, fallback_url, 60 * 60 * 24 * 7)
                return 'fallback', breed_name, None
            
            try:
                url = f'https://dog.ceo/api/breed/{dogceo_breed}/images/random'
                response = requests.get(url, timeout=2)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'success':
                        image_url = data.get('message')
                        cache.set(cache_key, image_url, 60 * 60 * 24 * 7)  # 7 days
                        return 'success', breed_name, image_url
                
                # API failed - use fallback
                fallback_url = f'https://source.unsplash.com/400x300/?{breed_name.replace(" ", "+")}+dog'
                cache.set(cache_key, fallback_url, 60 * 60 * 24)
                return 'fail', breed_name, None
                
            except Exception as e:
                # Exception - use fallback
                fallback_url = f'https://source.unsplash.com/400x300/?{breed_name.replace(" ", "+")}+dog'
                cache.set(cache_key, fallback_url, 60 * 60 * 24)
                return 'fail', breed_name, str(e)
        
        # Process in batches
        total_batches = (len(breeds_to_warm) + batch_size - 1) // batch_size
        
        for batch_num in range(0, len(breeds_to_warm), batch_size):
            batch = breeds_to_warm[batch_num:batch_num + batch_size]
            batch_number = (batch_num // batch_size) + 1
            
            self.stdout.write(
                self.style.WARNING(f'\n📦 Batch {batch_number}/{total_batches}') + 
                f' ({len(batch)} breeds)'
            )
            
            batch_start = time.time()
            batch_success = 0
            batch_skip = 0
            batch_fail = 0
            batch_fallback = 0
            
            # Process batch concurrently
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {executor.submit(fetch_and_cache, breed): breed for breed in batch}
                
                for future in as_completed(futures):
                    status, breed, extra = future.result()
                    
                    if status == 'success':
                        batch_success += 1
                        total_success += 1
                        self.stdout.write(self.style.SUCCESS(f'  ✓ {breed}'))
                    elif status == 'skip':
                        batch_skip += 1
                        total_skip += 1
                        self.stdout.write(f'  ○ {breed} (already cached)')
                    elif status == 'fallback':
                        batch_fallback += 1
                        total_fallback += 1
                        self.stdout.write(f'  ◆ {breed} (using fallback)')
                    else:  # fail
                        batch_fail += 1
                        total_fail += 1
                        self.stdout.write(self.style.WARNING(f'  ✗ {breed} (failed)'))
            
            batch_duration = time.time() - batch_start
            
            self.stdout.write(
                f'  📊 Batch stats: ' +
                self.style.SUCCESS(f'{batch_success} success') + ', ' +
                f'{batch_fallback} fallback, ' +
                f'{batch_skip} skipped, ' +
                self.style.WARNING(f'{batch_fail} failed') +
                f' ({batch_duration:.1f}s)'
            )
            
            # Delay between batches (except last one)
            if batch_num + batch_size < len(breeds_to_warm):
                self.stdout.write(f'  ⏳ Waiting {delay}s before next batch...')
                time.sleep(delay)
        
        # Final summary
        total_duration = time.time() - start_time
        total_cached = total_success + total_fallback
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('✨ PRE-WARMING COMPLETE!'))
        self.stdout.write('='*70)
        
        # Stats table
        self.stdout.write(f'{"Metric":<25} {"Count":<10} {"Percentage":<15}')
        self.stdout.write('-'*70)
        
        def print_stat(label, value, total, style_func=None):
            percentage = (value / total * 100) if total > 0 else 0
            text = f'{label:<25} {value:<10} {percentage:>6.1f}%'
            if style_func:
                self.stdout.write(style_func(text))
            else:
                self.stdout.write(text)
        
        print_stat('✓ Cached (Dog CEO)', total_success, count, self.style.SUCCESS)
        print_stat('◆ Cached (Fallback)', total_fallback, count)
        print_stat('○ Already Cached', total_skip, count)
        print_stat('✗ Failed', total_fail, count, self.style.WARNING if total_fail > 0 else None)
        self.stdout.write('-'*70)
        print_stat('TOTAL CACHED', total_cached, count, self.style.SUCCESS)
        
        self.stdout.write('='*70)
        self.stdout.write(f'⏱️  Total time: {total_duration:.1f}s ({total_duration/60:.1f} minutes)')
        self.stdout.write(f'⚡ Average: {total_duration/count:.2f}s per breed')
        self.stdout.write('='*70)
        
        if total_cached >= count * 0.9:  # 90%+ success
            self.stdout.write(self.style.SUCCESS('\n🎉 Excellent! Your API is now supercharged!'))
            self.stdout.write(self.style.SUCCESS(f'   {total_cached}/{count} breeds cached and ready!'))
        elif total_cached >= count * 0.75:  # 75%+ success
            self.stdout.write(self.style.WARNING('\n⚠️  Good! Most breeds cached.'))
            self.stdout.write(f'   {total_cached}/{count} breeds ready.')
        else:
            self.stdout.write(self.style.WARNING('\n⚠️  Warning: Low cache rate.'))
            self.stdout.write('   Check your internet connection or Dog CEO API status.')
        
        self.stdout.write('\n💡 Tip: Run with --force to refresh already cached breeds')
        self.stdout.write('   Example: python manage.py prewarm_breeds --force\n')