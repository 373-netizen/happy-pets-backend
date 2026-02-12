from django.core.management.base import BaseCommand
from py_vapid import Vapid01


class Command(BaseCommand):
    help = 'Generate VAPID keys for Web Push notifications'

    def handle(self, *args, **options):
        """Generate and display VAPID key pair"""
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('  Generating VAPID Keys for Web Push Notifications'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        
        try:
            # Generate VAPID key pair
            vapid = Vapid01()
            vapid.generate_keys()
            
            public_key = vapid.public_key.decode('utf-8')
            private_key = vapid.private_key.decode('utf-8')
            
            # Display the keys
            self.stdout.write(self.style.WARNING('\n📋 Add these to your settings.py file:\n'))
            
            self.stdout.write(self.style.SUCCESS('# Web Push (VAPID) Settings'))
            self.stdout.write(f'VAPID_PUBLIC_KEY = "{public_key}"')
            self.stdout.write(f'VAPID_PRIVATE_KEY = "{private_key}"')
            self.stdout.write('VAPID_ADMIN_EMAIL = "admin@yourapp.com"  # Change this to your email')
            
            self.stdout.write(self.style.WARNING('\n\n📱 Add the PUBLIC KEY to your React .env file:\n'))
            self.stdout.write(f'REACT_APP_VAPID_PUBLIC_KEY={public_key}')
            
            self.stdout.write(self.style.SUCCESS('\n\n✅ VAPID keys generated successfully!'))
            self.stdout.write(self.style.WARNING('\n⚠️  IMPORTANT:'))
            self.stdout.write('   - Keep your PRIVATE KEY secret!')
            self.stdout.write('   - Only share the PUBLIC KEY with your frontend')
            self.stdout.write('   - Store keys in environment variables for production')
            self.stdout.write(self.style.SUCCESS('\n' + '='*70 + '\n'))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Error generating VAPID keys: {str(e)}\n')
            )
            self.stdout.write(
                self.style.WARNING('Make sure py-vapid is installed: pip install py-vapid\n')
            )