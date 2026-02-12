"""
Constants for the Info app - API endpoints, choices, cache settings
"""

# Species Choices
SPECIES_CHOICES = [
    ('dog', 'Dog'),
    ('cat', 'Cat'),
    ('bird', 'Bird'),
    ('fish', 'Fish'),
    ('rabbit', 'Rabbit'),
    ('other', 'Other'),
]

# API Endpoints
WIKIPEDIA_BASE_URL = 'https://en.wikipedia.org/api/rest_v1'
DOG_API_BASE_URL = 'https://api.thedogapi.com/v1'
CAT_API_BASE_URL = 'https://api.thecatapi.com/v1'

# API Configuration
API_TIMEOUT = 10  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

# Media Configuration
GALLERY_IMAGE_LIMIT = 8
YOUTUBE_VIDEO_LIMIT = 4

# Cache Configuration
BREED_CACHE_TTL = 60 * 60 * 24 * 7  # 7 days in seconds
BREED_CACHE_KEY_PREFIX = 'breed_info'

# Rate Limiting
API_CALL_COOLDOWN = 2  # seconds between calls to same breed

# Image Quality Filters
MIN_IMAGE_WIDTH = 400
MIN_IMAGE_HEIGHT = 400