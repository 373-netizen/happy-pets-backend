"""
Views for Breed Information API - OPTIMIZED FOR SPEED
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.utils.text import slugify
from django.core.paginator import Paginator

from .serializers import BreedListSerializer, BreedDetailSerializer
from info.services.breed_aggregator import BreedAggregator


PEXELS_API_KEY = 'oAyeJhiZ3JRkW3kX6DlLuRRuaIaP0q4f4tIyW1kBxEtQFbwz57EKwUjd'
# Initialize the aggregator
aggregator = BreedAggregator()

"""
OPTIMIZED Views - Fast AND Accurate Breed Images
Strategy: Pre-warm cache + async image loading + smart fallbacks
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.utils.text import slugify
from django.core.paginator import Paginator
from django.core.cache import cache
from django.conf import settings
import requests
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# API Keys
YOUTUBE_API_KEY = getattr(settings, 'YOUTUBE_API_KEY', '')

# Thread pool for async requests
executor = ThreadPoolExecutor(max_workers=10)

# ============== BREED LISTS ==============
ALL_DOG_BREEDS = [
    # POPULAR BREEDS (35 existing)
    'Golden Retriever', 'Labrador Retriever', 'German Shepherd',
    'French Bulldog', 'Bulldog', 'Poodle', 'Beagle', 
    'Rottweiler', 'Yorkshire Terrier', 'Boxer',
    'Dachshund', 'Siberian Husky', 'Great Dane', 'Doberman Pinscher',
    'Australian Shepherd', 'Shih Tzu', 'Boston Terrier', 'Pomeranian',
    'Border Collie', 'Chihuahua', 'Pembroke Welsh Corgi', 'Basset Hound',
    'Newfoundland', 'Shiba Inu', 'Bernese Mountain Dog', 'Akita',
    'Pug', 'Dalmatian', 'Samoyed', 'Weimaraner', 'Vizsla',
    'Cocker Spaniel', 'Miniature Schnauzer', 'Maltese', 'Havanese',
    
    # ADDITIONAL 105+ BREEDS
    'Afghan Hound', 'Airedale Terrier', 'Alaskan Malamute', 'American Eskimo Dog',
    'American Staffordshire Terrier', 'Anatolian Shepherd', 'Australian Cattle Dog',
    'Basenji', 'Bearded Collie', 'Belgian Malinois', 'Belgian Sheepdog',
    'Belgian Tervuren', 'Bichon Frise', 'Bloodhound', 'Border Terrier',
    'Bouvier des Flandres', 'Boykin Spaniel', 'Briard', 'Brittany',
    'Brussels Griffon', 'Bull Terrier', 'Bullmastiff', 'Cairn Terrier',
    'Cane Corso', 'Cardigan Welsh Corgi', 'Cavalier King Charles Spaniel',
    'Chesapeake Bay Retriever', 'Chinese Crested', 'Chinese Shar-Pei', 'Chow Chow',
    'Clumber Spaniel', 'Collie', 'Curly-Coated Retriever', 'English Setter',
    'English Springer Spaniel', 'English Toy Spaniel', 'Field Spaniel',
    'Finnish Spitz', 'Flat-Coated Retriever', 'Fox Terrier', 'German Shorthaired Pointer',
    'German Wirehaired Pointer', 'Giant Schnauzer', 'Glen of Imaal Terrier',
    'Gordon Setter', 'Great Pyrenees', 'Greater Swiss Mountain Dog', 'Greyhound',
    'Harrier', 'Ibizan Hound', 'Icelandic Sheepdog', 'Irish Setter',
    'Irish Terrier', 'Irish Water Spaniel', 'Irish Wolfhound', 'Italian Greyhound',
    'Jack Russell Terrier', 'Japanese Chin', 'Keeshond', 'Kerry Blue Terrier',
    'Komondor', 'Kuvasz', 'Labradoodle', 'Lagotto Romagnolo', 'Lakeland Terrier',
    'Leonberger', 'Lhasa Apso', 'Lowchen', 'Manchester Terrier',
    'Mastiff', 'Miniature Bull Terrier', 'Miniature Pinscher', 'Neapolitan Mastiff',
    'Norfolk Terrier', 'Norwegian Buhund', 'Norwegian Elkhound', 'Norwich Terrier',
    'Nova Scotia Duck Tolling Retriever', 'Old English Sheepdog', 'Otterhound',
    'Papillon', 'Parson Russell Terrier', 'Pekingese', 'Pharaoh Hound',
    'Plott Hound', 'Pointer', 'Polish Lowland Sheepdog', 'Portuguese Water Dog',
    'Puli', 'Pumi', 'Pyrenean Shepherd', 'Rat Terrier', 'Redbone Coonhound',
    'Rhodesian Ridgeback', 'Saint Bernard', 'Saluki', 'Schipperke',
    'Scottish Deerhound', 'Scottish Terrier', 'Sealyham Terrier', 'Shetland Sheepdog',
    'Shikoku', 'Silky Terrier', 'Skye Terrier', 'Sloughi', 'Smooth Fox Terrier',
    'Soft Coated Wheaten Terrier', 'Spanish Water Dog', 'Spinone Italiano',
    'Staffordshire Bull Terrier', 'Standard Schnauzer', 'Sussex Spaniel',
    'Swedish Vallhund', 'Tibetan Mastiff', 'Tibetan Spaniel', 'Tibetan Terrier',
    'Toy Fox Terrier', 'Treeing Walker Coonhound', 'Welsh Springer Spaniel',
    'Welsh Terrier', 'West Highland White Terrier', 'Whippet', 'Wire Fox Terrier',
    'Wirehaired Pointing Griffon', 'Xoloitzcuintli', 'English Cocker Spaniel',
    'American Foxhound', 'Black and Tan Coonhound', 'Bluetick Coonhound',
]

BREED_SLUG_TO_DOGCEO = {
    'golden-retriever': 'retriever/golden',
    'labrador-retriever': 'retriever/labrador',
    'chesapeake-bay-retriever': 'retriever/chesapeake',
    'curly-coated-retriever': 'retriever/curly',
    'flat-coated-retriever': 'retriever/flatcoated',
    'german-shepherd': 'germanshepherd',
    'australian-shepherd': 'australian/shepherd',
    'french-bulldog': 'bulldog/french',
    'bulldog': 'bulldog/english',
    'bullmastiff': 'bullmastiff',
    'poodle': 'poodle/standard',
    'yorkshire-terrier': 'terrier/yorkshire',
    'boston-terrier': 'terrier/boston',
    'airedale-terrier': 'airedale',
    'border-terrier': 'terrier/border',
    'bull-terrier': 'bullterrier/staffordshire',
    'cairn-terrier': 'terrier/cairn',
    'fox-terrier': 'terrier/fox',
    'irish-terrier': 'terrier/irish',
    'jack-russell-terrier': 'terrier/russell',
    'kerry-blue-terrier': 'terrier/kerryblue',
    'norfolk-terrier': 'terrier/norfolk',
    'norwich-terrier': 'terrier/norwich',
    'scottish-terrier': 'terrier/scottish',
    'soft-coated-wheaten-terrier': 'terrier/wheaten',
    'staffordshire-bull-terrier': 'staffordshire/american',
    'welsh-terrier': 'terrier/welsh',
    'west-highland-white-terrier': 'terrier/westhighland',
    'wire-fox-terrier': 'terrier/fox',
    'toy-fox-terrier': 'terrier/toy',
    'american-staffordshire-terrier': 'staffordshire/american',
    'miniature-bull-terrier': 'bullterrier/staffordshire',
    'parson-russell-terrier': 'terrier/russell',
    'sealyham-terrier': 'terrier/sealyham',
    'silky-terrier': 'terrier/silky',
    'tibetan-terrier': 'terrier/tibetan',
    'border-collie': 'collie/border',
    'collie': 'collie/border',
    'belgian-malinois': 'malinois',
    'old-english-sheepdog': 'sheepdog/english',
    'shetland-sheepdog': 'sheepdog/shetland',
    'basset-hound': 'hound/basset',
    'afghan-hound': 'hound/afghan',
    'bloodhound': 'hound/blood',
    'ibizan-hound': 'hound/ibizan',
    'american-foxhound': 'hound/english',
    'black-and-tan-coonhound': 'hound/walker',
    'bluetick-coonhound': 'hound/walker',
    'treeing-walker-coonhound': 'hound/walker',
    'cocker-spaniel': 'spaniel/cocker',
    'english-cocker-spaniel': 'spaniel/cocker',
    'cavalier-king-charles-spaniel': 'spaniel/blenheim',
    'english-springer-spaniel': 'spaniel/springer',
    'english-toy-spaniel': 'spaniel/japanese',
    'irish-water-spaniel': 'spaniel/irish',
    'welsh-springer-spaniel': 'spaniel/welsh',
    'miniature-schnauzer': 'schnauzer/miniature',
    'giant-schnauzer': 'schnauzer/giant',
    'standard-schnauzer': 'schnauzer/giant',
    'english-setter': 'setter/english',
    'gordon-setter': 'setter/gordon',
    'irish-setter': 'setter/irish',
    'german-shorthaired-pointer': 'pointer/german',
    'german-wirehaired-pointer': 'pointer/germanlonghair',
    'pointer': 'pointer/german',
    'pembroke-welsh-corgi': 'corgi/cardigan',
    'cardigan-welsh-corgi': 'corgi/cardigan',
    'beagle': 'beagle',
    'rottweiler': 'rottweiler',
    'boxer': 'boxer',
    'dachshund': 'dachshund',
    'siberian-husky': 'husky',
    'great-dane': 'dane/great',
    'doberman-pinscher': 'doberman',
    'shih-tzu': 'shihtzu',
    'pomeranian': 'pomeranian',
    'chihuahua': 'chihuahua',
    'newfoundland': 'newfoundland',
    'shiba-inu': 'shiba',
    'bernese-mountain-dog': 'mountain/bernese',
    'akita': 'akita',
    'pug': 'pug',
    'dalmatian': 'dalmatian',
    'samoyed': 'samoyed',
    'weimaraner': 'weimaraner',
    'vizsla': 'vizsla',
    'havanese': 'havanese',
    'maltese': 'maltese',
    'alaskan-malamute': 'malamute',
    'saint-bernard': 'stbernard',
    'great-pyrenees': 'pyrenees',
    'mastiff': 'mastiff/english',
    'neapolitan-mastiff': 'mastiff/bull',
    'tibetan-mastiff': 'mastiff/tibetan',
    'greater-swiss-mountain-dog': 'mountain/swiss',
    'keeshond': 'keeshond',
    'komondor': 'komondor',
    'kuvasz': 'kuvasz',
    'bouvier-des-flandres': 'bouvier',
    'briard': 'briard',
    'basenji': 'basenji',
    'chow-chow': 'chow',
    'lhasa-apso': 'lhasa',
    'pekingese': 'pekinese',
    'miniature-pinscher': 'pinscher',
    'papillon': 'papillon',
    'japanese-chin': 'spaniel/japanese',
    'italian-greyhound': 'greyhound/italian',
    'greyhound': 'greyhound/italian',
    'whippet': 'whippet',
    'saluki': 'saluki',
    'irish-wolfhound': 'wolfhound/irish',
    'american-eskimo-dog': 'eskimo',
    'norwegian-elkhound': 'elkhound/norwegian',
    'schipperke': 'schipperke',
    'bichon-frise': 'bichon/frise',
    'brittany': 'brittany',
    'puli': 'puli',
    'rhodesian-ridgeback': 'ridgeback/rhodesian',
}

BREED_INFO_DATABASE = {
    'Golden Retriever': {
        'origin': 'Scotland', 'life_span': '10-12 years', 'weight': '55-75 lbs', 'height': '20-24 inches',
        'temperament': 'Friendly, Intelligent, Devoted, Trustworthy, Reliable, Gentle',
        'bred_for': 'Retrieving waterfowl for hunters, Companionship',
        'description': 'The Golden Retriever is a large, friendly gun dog that excels as a family companion, therapy dog, and service animal.',
        'intelligence': 4, 'energy_level': 4, 'trainability': 5, 'good_with_children': 5, 'shedding_level': 4,
        'grooming_needs': 'High - daily brushing required',
        'exercise_needs': 'High - 1-2 hours daily',
        'health_concerns': 'Hip dysplasia, cancer, heart disease',
        'history': 'Developed in Scotland during the Victorian era.',
        'fun_facts': ['Can hold eggs in their mouths without breaking them', 'Originally bred in Scotland in the 1800s'],
        'ideal_owner': 'Active families, first-time owners',
        'barking_level': 3, 'adaptability': 4, 'apartment_friendly': 2,
    },
    'Labrador Retriever': {
        'origin': 'Newfoundland, Canada', 'life_span': '10-14 years', 'weight': '55-80 lbs', 'height': '21-24 inches',
        'temperament': 'Outgoing, Even-tempered, Gentle, Intelligent',
        'bred_for': 'Retrieving fishing nets and game',
        'description': 'Most popular dog breed in America. Friendly, outgoing, and active.',
        'intelligence': 5, 'energy_level': 5, 'trainability': 5, 'good_with_children': 5, 'shedding_level': 4,
        'grooming_needs': 'Moderate - weekly brushing',
        'exercise_needs': 'Very High - 2+ hours daily',
        'health_concerns': 'Hip dysplasia, obesity, eye problems',
        'barking_level': 3, 'adaptability': 4, 'apartment_friendly': 2,
    },
    'German Shepherd': {
        'origin': 'Germany', 'life_span': '9-13 years', 'weight': '50-90 lbs', 'height': '22-26 inches',
        'temperament': 'Confident, Courageous, Intelligent, Loyal',
        'bred_for': 'Herding, Guarding, Police work',
        'description': 'Large, athletic dogs with noble character.',
        'intelligence': 5, 'energy_level': 4, 'trainability': 5, 'good_with_children': 4, 'shedding_level': 5,
        'grooming_needs': 'High - daily brushing during shedding',
        'exercise_needs': 'High - 1-2 hours daily',
        'health_concerns': 'Hip dysplasia, degenerative myelopathy',
        'barking_level': 4, 'adaptability': 3, 'apartment_friendly': 1,
    },
}

DEFAULT_BREED_INFO = {
    'origin': 'Various', 'life_span': '10-14 years', 'weight': '30-60 lbs', 'height': '18-24 inches',
    'temperament': 'Friendly, Loyal, Intelligent', 'bred_for': 'Companionship',
    'description': 'A wonderful breed known for loyalty.', 'intelligence': 4, 'energy_level': 3,
    'trainability': 4, 'good_with_children': 4, 'shedding_level': 3, 'grooming_needs': 'Moderate',
    'exercise_needs': 'Moderate', 'health_concerns': 'Regular vet checkups',
    'barking_level': 3, 'adaptability': 4, 'apartment_friendly': 3,
}

def fetch_single_dogceo_image(dogceo_breed):
    """Fetch a random image from Dog CEO API"""
    try:
        url = f'https://dog.ceo/api/breed/{dogceo_breed}/images/random'
        response = requests.get(url, timeout=2.0)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return data.get('message')
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Dog CEO API error for {dogceo_breed}: {e}")
    
    return None

def get_breed_image_smart(breed_slug, breed_name):
    """Smart image fetching with cache"""
    cache_key = f'img_v3_{breed_slug}'
    cached = cache.get(cache_key)
    
    if cached:
        return cached
    
    dogceo_breed = BREED_SLUG_TO_DOGCEO.get(breed_slug)
    
    if dogceo_breed:
        try:
            image_url = fetch_single_dogceo_image(dogceo_breed)
            if image_url:
                cache.set(cache_key, image_url, 60 * 60 * 24 * 7)
                return image_url
        except:
            pass
    
    fallback = f'https://source.unsplash.com/400x300/?{breed_name.replace(" ", "+")}+dog'
    cache.set(cache_key, fallback, 60 * 60 * 24)
    return fallback

def prewarm_image_cache(breed_slugs):
    """Background task to pre-fetch images for popular breeds"""
    def fetch_and_cache(slug, breed_name):
        cache_key = f'img_v3_{slug}'
        if cache.get(cache_key):
            return
        
        dogceo_breed = BREED_SLUG_TO_DOGCEO.get(slug)
        if dogceo_breed:
            image_url = fetch_single_dogceo_image(dogceo_breed)
            if image_url:
                cache.set(cache_key, image_url, 60 * 60 * 24 * 7)
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for slug in breed_slugs[:30]:
            breed_name = slug.replace('-', ' ').title()
            future = executor.submit(fetch_and_cache, slug, breed_name)
            futures.append(future)

def get_gallery_images_fast(breed_slug, count=15):
    """Fetch multiple images for detail view"""
    cache_key = f'gallery_v3_{breed_slug}_{count}'
    cached = cache.get(cache_key)
    
    if cached:
        return cached
    
    dogceo_breed = BREED_SLUG_TO_DOGCEO.get(breed_slug)
    
    if not dogceo_breed:
        breed_name = breed_slug.replace('-', ' ')
        fallback = [f'https://source.unsplash.com/800x600/?{breed_name.replace(" ", "+")}+dog+{i}' for i in range(count)]
        cache.set(cache_key, fallback, 60 * 60 * 24)
        return fallback
    
    try:
        url = f'https://dog.ceo/api/breed/{dogceo_breed}/images'
        response = requests.get(url, timeout=1.5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                all_images = data.get('message', [])
                if all_images:
                    images = random.sample(all_images, min(count, len(all_images)))
                    cache.set(cache_key, images, 60 * 60 * 24 * 7)
                    return images
    except:
        pass
    
    breed_name = breed_slug.replace('-', ' ')
    fallback = [f'https://source.unsplash.com/800x600/?{breed_name.replace(" ", "+")}+dog+{i}' for i in range(count)]
    cache.set(cache_key, fallback, 60 * 60 * 24)
    return fallback

def fetch_single_catapi_image(catapi_breed):
    """Fetch a random image from The Cat API"""
    try:
        url = f'https://api.thecatapi.com/v1/images/search?breed_ids={catapi_breed}&limit=1'
        response = requests.get(url, timeout=2.0)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return data[0].get('url')
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Cat API error for {catapi_breed}: {e}")
    
    return None

def get_cat_breed_image_smart(breed_slug, breed_name):
    """Smart cat image fetching with v4 cache"""
    cache_key = f'cat_img_v4_{breed_slug}'
    cached = cache.get(cache_key)
    
    if cached:
        return cached
    
    catapi_breed = BREED_SLUG_TO_CATAPI.get(breed_slug)
    
    if catapi_breed:
        try:
            image_url = fetch_single_catapi_image(catapi_breed)
            if image_url:
                cache.set(cache_key, image_url, 60 * 60 * 24 * 7)
                return image_url
        except:
            pass
    
    clean_name = breed_name.replace(' Cat', '')
    fallback = f'https://source.unsplash.com/400x300/?{clean_name.replace(" ", "+")}+cat'
    cache.set(cache_key, fallback, 60 * 60 * 24)
    return fallback

def get_cat_gallery_images_fast(breed_slug, count=15):
    """Fetch multiple cat images for detail view"""
    cache_key = f'cat_gallery_v4_{breed_slug}_{count}'
    cached = cache.get(cache_key)
    
    if cached:
        return cached
    
    catapi_breed = BREED_SLUG_TO_CATAPI.get(breed_slug)
    
    if not catapi_breed:
        breed_name = breed_slug.replace('-', ' ').replace(' cat', '')
        fallback = [
            f'https://source.unsplash.com/800x600/?{breed_name.replace(" ", "+")}+cat+{i}' 
            for i in range(count)
        ]
        cache.set(cache_key, fallback, 60 * 60 * 24)
        return fallback
    
    try:
        url = f'https://api.thecatapi.com/v1/images/search?breed_ids={catapi_breed}&limit={count}'
        response = requests.get(url, timeout=2.0)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                images = [item.get('url') for item in data if item.get('url')]
                if images:
                    cache.set(cache_key, images, 60 * 60 * 24 * 7)
                    return images
    except:
        pass
    
    breed_name = breed_slug.replace('-', ' ').replace(' cat', '')
    fallback = [
        f'https://source.unsplash.com/800x600/?{breed_name.replace(" ", "+")}+cat+{i}' 
        for i in range(count)
    ]
    cache.set(cache_key, fallback, 60 * 60 * 24)
    return fallback

def prewarm_cat_image_cache(breed_slugs):
    """Background task to pre-fetch cat images"""
    def fetch_and_cache(slug, breed_name):
        cache_key = f'cat_img_v4_{slug}'
        if cache.get(cache_key):
            return
        
        catapi_breed = BREED_SLUG_TO_CATAPI.get(slug)
        if catapi_breed:
            image_url = fetch_single_catapi_image(catapi_breed)
            if image_url:
                cache.set(cache_key, image_url, 60 * 60 * 24 * 7)
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for slug in breed_slugs[:20]:
            breed_name = slug.replace('-', ' ').title()
            future = executor.submit(fetch_and_cache, slug, breed_name)
            futures.append(future)

def get_cat_breed_info_with_fallback(breed_name):
    """Get breed info with intelligent defaults"""
    if breed_name in CAT_BREED_INFO:
        return CAT_BREED_INFO[breed_name]
    
    breed_name_alt = f"{breed_name} Cat" if not breed_name.endswith(' Cat') else breed_name.replace(' Cat', '')
    if breed_name_alt in CAT_BREED_INFO:
        return CAT_BREED_INFO[breed_name_alt]
    
    return {
        'origin': 'Various',
        'life_span': '12-18 years',
        'weight': '8-15 lbs',
        'coat_length': 'medium',
        'temperament': 'Friendly, Affectionate, Playful, Intelligent',
        'description': f'The {breed_name} is a unique and wonderful cat breed known for its distinctive characteristics, loving personality, and companionship.',
        'affection_level': 4,
        'intelligence': 4,
        'energy_level': 3,
        'playfulness': 4,
        'grooming_needs': 'Weekly brushing recommended',
    }

# ============== BIRD IMAGE FUNCTIONS (FIXED - NO DECORATORS!) ==============

def fetch_pexels_bird_image(bird_name, cache_key):
    """Fetch high-quality bird image from Pexels API"""
    try:
        clean_name = bird_name.replace(' Parrot', '').replace(' Parakeet', '').replace(' Finch', '').replace(' Conure', '').strip()
        search_term = f'{clean_name} bird'
        
        url = f'https://api.pexels.com/v1/search?query={search_term}&per_page=15'
        headers = {'Authorization': PEXELS_API_KEY}
        
        response = requests.get(url, headers=headers, timeout=3.0)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('photos') and len(data['photos']) > 0:
                photo = random.choice(data['photos'][:10])
                image_url = photo['src']['medium']
                
                if image_url:
                    cache.set(cache_key, image_url, 60 * 60 * 24 * 7)
                    return image_url
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Pexels API error for {bird_name}: {e}")
    
    return None

def get_bird_image_smart(breed_slug, breed_name):
    """Smart bird image fetching with multi-layer fallback"""
    cache_key = f'bird_img_v7_{breed_slug}'
    cached = cache.get(cache_key)
    
    if cached:
        return cached
    
    pexels_url = fetch_pexels_bird_image(breed_name, cache_key)
    if pexels_url:
        return pexels_url
    
    clean_name = breed_name.replace(' Parrot', '').replace(' Parakeet', '').strip().lower()
    
    PEXELS_BIRD_PHOTOS = {
        'budgerigar': '1661179',
        'cockatiel': '2317904',
        'african grey': '5857408',
        'canary': '1661179',
        'macaw': '1661179',
        'cockatoo': '5857408',
        'parrot': '1661179',
        'parakeet': '1661179',
        'lovebird': '1661179',
        'conure': '2317904',
        'finch': '1661179',
    }
    
    photo_id = '1661179'
    for key, pid in PEXELS_BIRD_PHOTOS.items():
        if key in clean_name:
            photo_id = pid
            break
    
    pexels_static = f'https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.jpeg?auto=compress&cs=tinysrgb&w=400'
    cache.set(cache_key, pexels_static, 60 * 60 * 24)
    return pexels_static

def get_bird_gallery_images_fast(breed_slug, count=15):
    """Fetch multiple bird images for gallery"""
    cache_key = f'bird_gallery_v7_{breed_slug}_{count}'
    cached = cache.get(cache_key)
    
    if cached:
        return cached
    
    breed_name = breed_slug.replace('-', ' ').title()
    clean_name = breed_name.replace(' Parrot', '').replace(' Parakeet', '').replace(' Finch', '').strip()
    
    try:
        url = f'https://api.pexels.com/v1/search?query={clean_name}+bird&per_page={count}'
        headers = {'Authorization': PEXELS_API_KEY}
        
        response = requests.get(url, headers=headers, timeout=3.0)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('photos'):
                images = [photo['src']['large'] for photo in data['photos'][:count]]
                cache.set(cache_key, images, 60 * 60 * 24 * 7)
                return images
    except:
        pass
    
    images = []
    pexels_ids = ['1661179', '2317904', '5857408', '1020315', '1661544', '349758', '1463295', '326012', '1178991', '2098427']
    
    for i in range(count):
        if i < len(pexels_ids):
            pid = pexels_ids[i]
            images.append(f'https://images.pexels.com/photos/{pid}/pexels-photo-{pid}.jpeg?auto=compress&cs=tinysrgb&w=800')
        else:
            images.append(f'https://source.unsplash.com/800x600/?{clean_name.replace(" ", "+")}+bird&sig={i}')
    
    cache.set(cache_key, images, 60 * 60 * 24)
    return images

def get_bird_breed_info_with_fallback(breed_name):
    """Get bird breed info with intelligent defaults"""
    if breed_name in BIRD_BREED_INFO:
        return BIRD_BREED_INFO[breed_name]
    
    return {
        'origin': 'Various',
        'life_span': '10-20 years',
        'size': 'medium',
        'temperament': 'Friendly, Social, Intelligent, Playful',
        'description': f'The {breed_name} is a beautiful and intelligent bird species known for its unique characteristics and engaging personality.',
        'intelligence': 4,
        'vocalization': 3,
        'social_needs': 4,
        'care_level': 'intermediate',
        'diet': 'Species-appropriate pellets, seeds, fresh fruits, and vegetables',
    }

@api_view(['GET'])
@permission_classes([AllowAny])
def dog_breeds_list(request):
    """Fast list with breed-specific images"""
    page_number = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 30))
    search_query = request.GET.get('search', '').lower()
    
    if search_query:
        breeds_list = [b for b in ALL_DOG_BREEDS if search_query in b.lower()]
    else:
        breeds_list = ALL_DOG_BREEDS
    
    breeds_data = []
    for idx, breed_name in enumerate(breeds_list):
        slug = slugify(breed_name)
        info = BREED_INFO_DATABASE.get(breed_name, DEFAULT_BREED_INFO)
        
        cache_key = f'img_v3_{slug}'
        image = cache.get(cache_key)

        if not image:
            image = get_breed_image_smart(slug, breed_name)
        
        breeds_data.append({
            'id': idx + 1,
            'name': breed_name,
            'slug': slug,
            'image': image,
            'origin': info.get('origin', 'Various'),
            'life_span': info.get('life_span', '10-14 years'),
            'size': _get_size_fast(breed_name, info.get('weight', '')),
            'breed_group': _get_group_fast(breed_name),
            'is_popular': idx < 35
        })
    
    paginator = Paginator(breeds_data, page_size)
    page_obj = paginator.get_page(page_number)
    
    return Response({
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': page_number,
        'page_size': page_size,
        'results': page_obj.object_list
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def dog_breed_detail(request, slug):
    """Detail view with full gallery"""
    breed_name = slug.replace('-', ' ').title()
    breed_info = BREED_INFO_DATABASE.get(breed_name, DEFAULT_BREED_INFO.copy())
    
    gallery_images = get_gallery_images_fast(slug, 15)
    main_image = gallery_images[0]
    
    youtube_videos = get_youtube_videos_cached(breed_name, 6)
    
    detail = {
        'id': 1,
        'name': breed_name,
        'slug': slug,
        'species': 'dog',
        'main_image': main_image,
        'gallery_images': gallery_images,
        'origin': breed_info.get('origin', 'Various'),
        'life_span': breed_info.get('life_span', '10-14 years'),
        'weight': breed_info.get('weight', '30-60 lbs'),
        'height': breed_info.get('height', '18-24 inches'),
        'temperament': breed_info.get('temperament', 'Friendly, Loyal'),
        'bred_for': breed_info.get('bred_for', 'Companionship'),
        'description': breed_info.get('description', 'A wonderful breed.'),
        'breed_group': _get_group_fast(breed_name),
        'intelligence': breed_info.get('intelligence', 4),
        'energy_level': breed_info.get('energy_level', 3),
        'trainability': breed_info.get('trainability', 4),
        'good_with_children': breed_info.get('good_with_children', 4),
        'shedding_level': breed_info.get('shedding_level', 3),
        'barking_level': breed_info.get('barking_level', 3),
        'grooming_needs': breed_info.get('grooming_needs', 'Moderate'),
        'exercise_needs': breed_info.get('exercise_needs', 'Moderate'),
        'health_concerns': breed_info.get('health_concerns', 'Regular checkups'),
        'youtube_videos': youtube_videos,
        'wikipedia_url': f'https://en.wikipedia.org/wiki/{breed_name.replace(" ", "_")}',
    }
    
    return Response(detail)

@api_view(['GET'])
@permission_classes([AllowAny])
def cat_breeds_list(request):
    """Fast cat breed list with breed-specific images"""
    page_number = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 30))
    search_query = request.GET.get('search', '').lower()
    
    if search_query:
        breeds_list = [b for b in ALL_CAT_BREEDS if search_query in b.lower()]
    else:
        breeds_list = ALL_CAT_BREEDS
    
    breeds_data = []
    for idx, breed_name in enumerate(breeds_list):
        slug = slugify(breed_name)
        info = get_cat_breed_info_with_fallback(breed_name)
        
        image = get_cat_breed_image_smart(slug, breed_name)
        
        breeds_data.append({
            'id': idx + 1,
            'name': breed_name,
            'slug': slug,
            'image': image,
            'origin': info.get('origin', 'Various'),
            'life_span': info.get('life_span', '12-18 years'),
            'coat_length': info.get('coat_length', 'medium'),
            'temperament': info.get('temperament', 'Friendly, Affectionate'),
            'is_popular': idx < 32
        })
    
    paginator = Paginator(breeds_data, page_size)
    page_obj = paginator.get_page(page_number)
    
    return Response({
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': page_number,
        'page_size': page_size,
        'results': page_obj.object_list
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def cat_breed_detail(request, slug):
    """Cat breed detail view with full gallery"""
    breed_name = slug.replace('-', ' ').title()
    
    if not breed_name.endswith(' Cat'):
        breed_name_with_cat = f"{breed_name} Cat"
        breed_info = CAT_BREED_INFO.get(breed_name_with_cat, CAT_BREED_INFO.get(breed_name, DEFAULT_CAT_INFO.copy()))
    else:
        breed_info = CAT_BREED_INFO.get(breed_name, DEFAULT_CAT_INFO.copy())
    
    gallery_images = get_cat_gallery_images_fast(slug, 15)
    main_image = gallery_images[0] if gallery_images else get_cat_breed_image_smart(slug, breed_name)
    
    youtube_videos = get_youtube_videos_cached(breed_name, 6)
    
    detail = {
        'id': 1,
        'name': breed_name,
        'slug': slug,
        'species': 'cat',
        'main_image': main_image,
        'gallery_images': gallery_images,
        'origin': breed_info.get('origin', 'Various'),
        'life_span': breed_info.get('life_span', '12-18 years'),
        'weight': breed_info.get('weight', '8-15 lbs'),
        'coat_length': breed_info.get('coat_length', 'medium'),
        'temperament': breed_info.get('temperament', 'Friendly, Affectionate'),
        'description': breed_info.get('description', 'A wonderful cat breed.'),
        'affection_level': breed_info.get('affection_level', 4),
        'intelligence': breed_info.get('intelligence', 4),
        'energy_level': breed_info.get('energy_level', 3),
        'playfulness': breed_info.get('playfulness', 4),
        'grooming_needs': breed_info.get('grooming_needs', 'Weekly brushing'),
        'health_concerns': breed_info.get('health_concerns', 'Regular vet checkups'),
        'youtube_videos': youtube_videos,
        'wikipedia_url': f'https://en.wikipedia.org/wiki/{breed_name.replace(" ", "_")}',
    }
    
    return Response(detail)

# ============== BIRD VIEWS (FIXED!) ==============

@api_view(['GET'])
@permission_classes([AllowAny])
def bird_breeds_list(request):
    """Paginated bird species list with REAL images from Pexels"""
    page_number = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 30))
    search_query = request.GET.get('search', '').lower()
    
    if search_query:
        breeds_list = [b for b in ALL_BIRD_BREEDS if search_query in b.lower()]
    else:
        breeds_list = ALL_BIRD_BREEDS
    
    breeds_data = []
    for idx, bird_name in enumerate(breeds_list):
        slug = slugify(bird_name)
        info = get_bird_breed_info_with_fallback(bird_name)
        
        image = get_bird_image_smart(slug, bird_name)
        
        breed_info = {
            'id': idx + 1,
            'name': bird_name,
            'slug': slug,
            'image': image,
            'origin': info.get('origin', 'Various'),
            'life_span': info.get('life_span', '10-20 years'),
            'size': info.get('size', 'medium'),
            'temperament': info.get('temperament', 'Friendly, Social'),
            'bird_type': _get_bird_type(bird_name),
            'is_popular': idx < 20
        }
        breeds_data.append(breed_info)
    
    paginator = Paginator(breeds_data, page_size)
    page_obj = paginator.get_page(page_number)
    
    return Response({
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': page_number,
        'page_size': page_size,
        'results': page_obj.object_list
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def bird_breed_detail(request, slug):
    """Bird breed detail with real image gallery from Pexels"""
    bird_name = slug.replace('-', ' ').title()
    
    breed_info = get_bird_breed_info_with_fallback(bird_name)
    
    gallery_images = get_bird_gallery_images_fast(slug, 15)
    
    main_image = gallery_images[0] if gallery_images else get_bird_image_smart(slug, bird_name)
    
    youtube_videos = get_youtube_videos_cached(bird_name, 6)
    
    detail = {
        'id': 1,
        'name': bird_name,
        'slug': slug,
        'species': 'bird',
        'main_image': main_image,
        'image': main_image,
        'gallery_images': gallery_images,
        'description': breed_info.get('description', f'The {bird_name} is a beautiful and intelligent bird species.'),
        'origin': breed_info.get('origin', 'Various'),
        'life_span': breed_info.get('life_span', '10-20 years'),
        'size': breed_info.get('size', 'medium'),
        'temperament': breed_info.get('temperament', 'Friendly, Social, Intelligent'),
        'bird_type': _get_bird_type(bird_name),
        'intelligence': breed_info.get('intelligence', 4),
        'vocalization': breed_info.get('vocalization', 3),
        'social_needs': breed_info.get('social_needs', 4),
        'care_level': breed_info.get('care_level', 'intermediate'),
        'diet': breed_info.get('diet', 'Pellets, seeds, fruits, vegetables'),
        'housing_requirements': 'Spacious cage with perches, toys, and enrichment',
        'health_concerns': 'Regular vet checkups, species-specific care',
        'youtube_videos': youtube_videos,
        'wikipedia_url': f'https://en.wikipedia.org/wiki/{bird_name.replace(" ", "_")}',
    }
    
    return Response(detail)

def get_youtube_videos_cached(breed_name, max_results=6):
    """YouTube with caching"""
    cache_key = f'youtube_v3_{breed_name.lower().replace(" ", "_")}'
    cached = cache.get(cache_key)
    
    if cached:
        return cached
    
    videos = get_youtube_fallback(breed_name, max_results)
    cache.set(cache_key, videos, 60 * 60 * 24 * 30)
    return videos

def get_youtube_fallback(breed_name, max_results=6):
    """YouTube search links"""
    search_base = breed_name.replace(' ', '+')
    return [
        {
            'title': f'{breed_name} - Complete Guide',
            'url': f'https://www.youtube.com/results?search_query={search_base}+breed+guide',
            'thumbnail': 'https://via.placeholder.com/480x360/FF6B35/FFFFFF?text=Guide',
        },
        {
            'title': f'{breed_name} - Training',
            'url': f'https://www.youtube.com/results?search_query={search_base}+training',
            'thumbnail': 'https://via.placeholder.com/480x360/F7931E/FFFFFF?text=Training',
        },
    ][:max_results]

def _get_size_fast(breed_name, weight_str):
    """Fast size calculation"""
    try:
        weight = int(weight_str.split('-')[0].replace('lbs', '').strip())
        if weight > 70:
            return 'large'
        elif weight < 25:
            return 'small'
    except:
        pass
    return 'medium'

def _get_group_fast(breed_name):
    """Fast breed group"""
    name_lower = breed_name.lower()
    
    if any(w in name_lower for w in ['retriever', 'spaniel', 'pointer', 'setter']):
        return 'Sporting'
    elif 'hound' in name_lower:
        return 'Hound'
    elif 'terrier' in name_lower:
        return 'Terrier'
    elif any(w in name_lower for w in ['shepherd', 'collie', 'corgi']):
        return 'Herding'
    
    return 'Companion'

def _get_bird_type(bird_name):
    """Determine bird type from name"""
    name_lower = bird_name.lower()
    
    if 'parrot' in name_lower or 'macaw' in name_lower or 'amazon' in name_lower:
        return 'parrot'
    elif 'conure' in name_lower:
        return 'conure'
    elif 'cockatoo' in name_lower:
        return 'cockatoo'
    elif 'canary' in name_lower:
        return 'canary'
    elif 'finch' in name_lower:
        return 'finch'
    elif 'lovebird' in name_lower:
        return 'lovebird'
    elif 'parakeet' in name_lower or 'budgerigar' in name_lower:
        return 'parakeet'
    elif 'cockatiel' in name_lower:
        return 'cockatiel'
    
    return 'other'

@api_view(['GET'])
@permission_classes([AllowAny])
def test_endpoint(request):
    return Response({
        'status': 'OPTIMIZED',
        'message': f'{len(ALL_DOG_BREEDS)} breeds with smart image caching',
        'mapped_breeds': len(BREED_SLUG_TO_DOGCEO)
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def prewarm_cache_endpoint(request):
    """Call this endpoint to pre-warm the image cache"""
    breed_slugs = [slugify(b) for b in ALL_DOG_BREEDS[:30]]
    
    threading.Thread(target=prewarm_image_cache, args=(breed_slugs,)).start()
    
    return Response({
        'status': 'started',
        'message': 'Pre-warming cache for 30 breeds in background'
    })

# ============== CAT & BIRD BREED DATA ==============

ALL_CAT_BREEDS = [
    'Persian Cat', 'Maine Coon', 'Siamese Cat', 'Ragdoll',
    'British Shorthair', 'Scottish Fold', 'Sphynx Cat',
    'Bengal Cat', 'Russian Blue', 'Abyssinian', 'American Shorthair',
    'Birman', 'Oriental', 'Devon Rex', 'Himalayan', 'Burmese',
    'Exotic Shorthair', 'Siberian Cat', 'Manx', 'Cornish Rex',
    'Norwegian Forest Cat', 'Tonkinese', 'Turkish Angora', 'Somali',
    'Chartreux', 'Balinese', 'Egyptian Mau', 'Japanese Bobtail',
    'Ragamuffin', 'Selkirk Rex', 'Singapura', 'Bombay',
    'Turkish Van', 'American Curl', 'LaPerm', 'Ocicat',
    'Snowshoe', 'Korat', 'Havana Brown', 'American Bobtail',
    'Peterbald', 'Munchkin', 'Savannah', 'Toyger',
    'Pixie-Bob', 'Nebelung', 'Chausie', 'Khao Manee',
    'Burmilla', 'York Chocolate', 'Sokoke', 'Lykoi',
    'Asian Cat', 'Australian Mist', 'Cymric', 'Dragon Li',
    'Donskoy', 'European Shorthair', 'German Rex', 'Highlander',
    'Kurilian Bobtail', 'Minskin', 'Napoleon', 'Ojos Azules',
    'Oregon Rex', 'Raas', 'Sam Sawet', 'Serengeti',
    'Seychellois', 'Tiffanie', 'Ukrainian Levkoy', 'Ussuri',
    'California Spangled', 'Chantilly-Tiffany', 'Colorpoint Shorthair',
    'Foldex', 'Javanese', 'Kinkalow', 'Lambkin', 'Mandalay',
    'Minuet', 'Mojave Spotted', 'Oriental Longhair', 'Oriental Shorthair',
    'Owyhee Bob', 'Pantherette', 'Safari', 'Siberian Forest Cat',
    'Thai Cat', 'Traditional Persian', 'Ural Rex', 'Vienna Woods',
    'American Wirehair', 'Aphrodite Giant', 'Bambino', 'Bristol',
    'Colorpoint Persian', 'Dwelf', 'Genetta', 'Khmer',
    'Korn Ja', 'Kurilian', 'Lynx Point Siamese', 'Malayan',
    'Mekong Bobtail', 'Neva Masquerade', 'Poodle Cat', 'Skookum',
    'Suphalak', 'Tennessee Rex', 'Templecat', 'Wichien Maat'
]

BREED_SLUG_TO_CATAPI = {
    'persian-cat': 'pers', 'maine-coon': 'mcoo', 'siamese-cat': 'siam',
    'ragdoll': 'raga', 'british-shorthair': 'bsho', 'scottish-fold': 'sfol',
    'sphynx-cat': 'sphy', 'bengal-cat': 'beng', 'russian-blue': 'ruba',
    'abyssinian': 'abys', 'american-shorthair': 'asho', 'birman': 'birm',
    'oriental': 'orie', 'devon-rex': 'drex', 'himalayan': 'hima',
    'burmese': 'burm', 'exotic-shorthair': 'esho', 'siberian-cat': 'sibe',
    'manx': 'manx', 'cornish-rex': 'crex', 'norwegian-forest-cat': 'norw',
    'tonkinese': 'tonk', 'turkish-angora': 'tang', 'somali': 'soma',
    'chartreux': 'char', 'balinese': 'bali', 'egyptian-mau': 'emau',
    'japanese-bobtail': 'jbob', 'ragamuffin': 'raga', 'selkirk-rex': 'srex',
    'singapura': 'sing', 'bombay': 'bomb', 'turkish-van': 'tvan',
    'american-curl': 'acur', 'laperm': 'lape', 'ocicat': 'ocic',
    'snowshoe': 'snow', 'korat': 'kora', 'havana-brown': 'hava',
    'american-bobtail': 'abob', 'peterbald': 'pete', 'munchkin': 'munc',
    'savannah': 'sava', 'toyger': 'toyg', 'pixie-bob': 'pixi',
    'nebelung': 'nebe', 'chausie': 'chau', 'khao-manee': 'khao',
    'burmilla': 'bure', 'york-chocolate': 'ycho', 'sokoke': 'soko',
    'lykoi': 'lyko', 'asian-cat': 'asho', 'australian-mist': 'amis',
    'cymric': 'cymr', 'dragon-li': 'lihu', 'donskoy': 'dons',
    'european-shorthair': 'esho', 'german-rex': 'grex', 'highlander': 'high',
    'kurilian-bobtail': 'kuri', 'minskin': 'mins', 'napoleon': 'minu',
    'american-wirehair': 'awir', 'bambino': 'bamb', 'javanese': 'java',
    'oriental-shorthair': 'orie', 'oriental-longhair': 'orie',
    'colorpoint-shorthair': 'siam', 'traditional-persian': 'pers',
    'siberian-forest-cat': 'sibe', 'thai-cat': 'siam',
    'lynx-point-siamese': 'siam', 'colorpoint-persian': 'hima',
    'neva-masquerade': 'sibe', 'mekong-bobtail': 'jbob',
}

CAT_BREED_INFO = {
    'Persian Cat': {
        'origin': 'Iran (Persia)', 'life_span': '12-17 years', 'weight': '7-12 lbs',
        'coat_length': 'long', 'temperament': 'Quiet, Sweet, Gentle, Affectionate',
        'description': 'Known for their long, luxurious coat and sweet personality.',
        'affection_level': 5, 'intelligence': 3, 'energy_level': 2, 'playfulness': 3,
        'grooming_needs': 'Daily brushing required',
    },
    'Maine Coon': {
        'origin': 'United States', 'life_span': '12-15 years', 'weight': '10-25 lbs',
        'coat_length': 'long', 'temperament': 'Friendly, Intelligent, Playful, Gentle',
        'description': 'One of the largest domesticated cat breeds, known as "gentle giants".',
        'affection_level': 5, 'intelligence': 5, 'energy_level': 4, 'playfulness': 5,
        'grooming_needs': 'Weekly brushing',
    },
    'Siamese Cat': {
        'origin': 'Thailand', 'life_span': '12-20 years', 'weight': '8-12 lbs',
        'coat_length': 'short', 'temperament': 'Vocal, Social, Intelligent, Affectionate',
        'description': 'Highly vocal and social cats with distinctive color points.',
        'affection_level': 5, 'intelligence': 5, 'energy_level': 5, 'playfulness': 5,
        'grooming_needs': 'Low - weekly brushing',
    },
    'Ragdoll': {
        'origin': 'United States', 'life_span': '12-17 years', 'weight': '10-20 lbs',
        'coat_length': 'long', 'temperament': 'Docile, Gentle, Calm, Affectionate',
        'description': 'Large, gentle cats that go limp when picked up, hence the name.',
        'affection_level': 5, 'intelligence': 4, 'energy_level': 2, 'playfulness': 3,
        'grooming_needs': 'Regular brushing',
    },
    'Bengal Cat': {
        'origin': 'United States', 'life_span': '12-16 years', 'weight': '8-15 lbs',
        'coat_length': 'short', 'temperament': 'Active, Intelligent, Curious, Playful',
        'description': 'Wild-looking cats with leopard-like spots and high energy.',
        'affection_level': 4, 'intelligence': 5, 'energy_level': 5, 'playfulness': 5,
        'grooming_needs': 'Low - weekly brushing',
    },
}

DEFAULT_CAT_INFO = {
    'origin': 'Various', 'life_span': '12-18 years', 'weight': '8-15 lbs',
    'coat_length': 'medium', 'temperament': 'Friendly, Affectionate, Playful',
    'description': 'A wonderful cat breed known for companionship.',
    'affection_level': 4, 'intelligence': 4, 'energy_level': 3, 'playfulness': 4,
    'grooming_needs': 'Weekly brushing',
}

ALL_BIRD_BREEDS = [
    'Budgerigar', 'Cockatiel', 'African Grey Parrot', 'Canary',
    'Lovebird', 'Parakeet', 'Sun Conure', 'Finch', 'Green Cheek Conure', 
    'Cockatoo', 'Amazon Parrot', 'Eclectus Parrot', 'Quaker Parrot',
    'Pionus Parrot', 'Senegal Parrot', 'Caique', 'Lorikeet', 
    'Jenday Conure', 'Blue and Gold Macaw', 'Scarlet Macaw',
    'Military Macaw', 'Greenwing Macaw', 'Hyacinth Macaw', 
    'Yellow Naped Amazon', 'Blue Fronted Amazon', 'Double Yellow Head Amazon',
    'Indian Ringneck', 'Alexandrine Parakeet', 'Moustached Parakeet',
    'Congo African Grey', 'Timneh African Grey', 'Meyer\'s Parrot',
    'Red Bellied Parrot', 'Jardine\'s Parrot', 'Cape Parrot',
    'Umbrella Cockatoo', 'Moluccan Cockatoo', 'Sulphur Crested Cockatoo',
    'Goffin\'s Cockatoo', 'Bare Eyed Cockatoo', 'Rose Breasted Cockatoo',
    'Major Mitchell Cockatoo', 'Palm Cockatoo',
    'Nanday Conure', 'Cherry Head Conure', 'Mitred Conure', 
    'Blue Crown Conure', 'Dusky Conure', 'Maroon Bellied Conure',
    'Peach Fronted Conure', 'Golden Conure', 'Patagonian Conure',
    'White Eyed Conure',
]

BIRD_BREED_INFO = {
    'Budgerigar': {
        'origin': 'Australia', 'life_span': '5-10 years', 'size': 'small',
        'temperament': 'Playful, Social, Intelligent, Friendly',
        'description': 'Also known as budgies or parakeets, these small parrots are one of the most popular pet birds worldwide.',
        'intelligence': 4, 'vocalization': 4, 'social_needs': 4,
        'care_level': 'beginner', 'diet': 'Seeds, pellets, vegetables, fruits',
    },
    'Cockatiel': {
        'origin': 'Australia', 'life_span': '15-25 years', 'size': 'small',
        'temperament': 'Gentle, Affectionate, Whistler, Social',
        'description': 'Friendly crested parrots known for their whistling ability and charming personalities.',
        'intelligence': 4, 'vocalization': 3, 'social_needs': 5,
        'care_level': 'beginner', 'diet': 'Pellets, seeds, vegetables, fruits',
    },
    'African Grey Parrot': {
        'origin': 'Central Africa', 'life_span': '40-60 years', 'size': 'large',
        'temperament': 'Highly Intelligent, Sensitive, Talkative, Loyal',
        'description': 'Renowned for exceptional intelligence and talking ability. Considered one of the smartest bird species.',
        'intelligence': 5, 'vocalization': 5, 'social_needs': 5,
        'care_level': 'advanced', 'diet': 'Pellets, nuts, vegetables, fruits',
    },
    'Canary': {
        'origin': 'Canary Islands', 'life_span': '10-15 years', 'size': 'small',
        'temperament': 'Melodious, Independent, Calm, Cheerful',
        'description': 'Small songbirds prized for their beautiful singing. Males are especially vocal.',
        'intelligence': 3, 'vocalization': 5, 'social_needs': 2,
        'care_level': 'beginner', 'diet': 'Seeds, greens, fruits',
    },
}

# ============== EXOTIC PETS IMAGE FUNCTIONS ==============

def fetch_pexels_exotic_image(pet_name, category, cache_key):
    """Fetch high-quality exotic pet image from Pexels API"""
    try:
        # Clean the search term based on category
        if category == 'reptile':
            search_term = pet_name.replace('Bearded Dragon', 'bearded dragon lizard')
            search_term = search_term.replace('Ball Python', 'ball python snake')
            search_term = search_term.replace('Leopard Gecko', 'leopard gecko')
            search_term = search_term.replace('Corn Snake', 'corn snake')
            search_term = search_term.replace('Blue-Tongued Skink', 'blue tongue skink')
            search_term = search_term.replace('Red-Eared Slider', 'red eared slider turtle')
        elif category == 'fish':
            search_term = pet_name.replace('Betta Fish', 'betta fish')
            search_term = search_term.replace('Goldfish', 'goldfish')
            search_term = search_term.replace('Guppy', 'guppy fish')
        elif category == 'rabbit':
            search_term = pet_name + ' rabbit'
        elif category == 'rodent':
            search_term = pet_name
        elif category == 'amphibian':
            search_term = pet_name.replace('Fire-Bellied Toad', 'fire bellied toad')
            search_term = search_term.replace('Axolotl', 'axolotl')
        else:
            search_term = pet_name
        
        url = f'https://api.pexels.com/v1/search?query={search_term}&per_page=15'
        headers = {'Authorization': PEXELS_API_KEY}
        
        response = requests.get(url, headers=headers, timeout=3.0)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('photos') and len(data['photos']) > 0:
                photo = random.choice(data['photos'][:10])
                image_url = photo['src']['medium']
                
                if image_url:
                    cache.set(cache_key, image_url, 60 * 60 * 24 * 7)
                    return image_url
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Pexels API error for {pet_name}: {e}")
    
    return None

def get_exotic_image_smart(pet_slug, pet_name, category):
    """Smart exotic pet image fetching with multi-layer fallback"""
    cache_key = f'exotic_img_v1_{pet_slug}'
    cached = cache.get(cache_key)
    
    if cached:
        return cached
    
    # Try Pexels first
    pexels_url = fetch_pexels_exotic_image(pet_name, category, cache_key)
    if pexels_url:
        return pexels_url
    
    # Fallback to Unsplash
    search_term = pet_name.replace(' ', '+')
    fallback = f'https://source.unsplash.com/400x300/?{search_term}'
    cache.set(cache_key, fallback, 60 * 60 * 24)
    return fallback

def get_exotic_gallery_images_fast(pet_slug, pet_name, category, count=15):
    """Fetch multiple exotic pet images for gallery"""
    cache_key = f'exotic_gallery_v1_{pet_slug}_{count}'
    cached = cache.get(cache_key)
    
    if cached:
        return cached
    
    # Prepare search term
    if category == 'reptile':
        search_term = pet_name.replace('Bearded Dragon', 'bearded dragon lizard')
        search_term = search_term.replace('Ball Python', 'ball python snake')
        search_term = search_term.replace('Leopard Gecko', 'leopard gecko')
        search_term = search_term.replace('Corn Snake', 'corn snake')
        search_term = search_term.replace('Blue-Tongued Skink', 'blue tongue skink')
        search_term = search_term.replace('Red-Eared Slider', 'red eared slider turtle')
    elif category == 'fish':
        search_term = pet_name
    elif category == 'rabbit':
        search_term = pet_name + ' rabbit'
    elif category == 'rodent':
        search_term = pet_name
    elif category == 'amphibian':
        search_term = pet_name
    else:
        search_term = pet_name
    
    try:
        url = f'https://api.pexels.com/v1/search?query={search_term}&per_page={count}'
        headers = {'Authorization': PEXELS_API_KEY}
        
        response = requests.get(url, headers=headers, timeout=3.0)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('photos') and len(data['photos']) > 0:
                images = [photo['src']['large'] for photo in data['photos'][:count]]
                cache.set(cache_key, images, 60 * 60 * 24 * 7)
                return images
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Pexels gallery error for {pet_name}: {e}")
    
    # Fallback to Unsplash with variations
    images = []
    search_base = pet_name.replace(' ', '+')
    for i in range(count):
        images.append(f'https://source.unsplash.com/800x600/?{search_base}&sig={i}')
    
    cache.set(cache_key, images, 60 * 60 * 24)
    return images

def get_exotic_breed_info_with_fallback(pet_name, category):
    """Get exotic pet info with intelligent defaults"""
    if pet_name in EXOTIC_BREED_INFO:
        return EXOTIC_BREED_INFO[pet_name]
    
    # Return category-based defaults
    return {
        'origin': 'Various',
        'life_span': _get_exotic_lifespan(pet_name, category),
        'size': _get_exotic_size(pet_name),
        'temperament': 'Varies by species',
        'description': f'The {pet_name} is a fascinating exotic pet with unique care requirements.',
        'care_level': _get_care_level(pet_name),
        'diet': _get_exotic_diet(category),
        'housing_requirements': _get_exotic_housing(category),
        'temperature_range': _get_temperature(category),
        'humidity_level': _get_humidity(category),
    }

# Exotic pet breed information database
EXOTIC_BREED_INFO = {
    'Bearded Dragon': {
        'origin': 'Australia',
        'life_span': '10-15 years',
        'size': 'medium',
        'temperament': 'Docile, Curious, Friendly',
        'description': 'Bearded Dragons are popular pet lizards known for their calm demeanor and distinctive spiny throat pouch that expands like a beard when threatened.',
        'care_level': 'beginner',
        'diet': 'Insects, vegetables, occasional fruits',
        'housing_requirements': '40+ gallon terrarium with UVB lighting and heating',
        'temperature_range': '75-85°F (24-29°C)',
        'humidity_level': '30-40%',
    },
    'Ball Python': {
        'origin': 'West and Central Africa',
        'life_span': '20-30 years',
        'size': 'medium',
        'temperament': 'Calm, Docile, Shy',
        'description': 'Ball Pythons are gentle constrictors that curl into a ball when stressed, making them excellent pet snakes for beginners.',
        'care_level': 'beginner',
        'diet': 'Rodents (mice and rats)',
        'housing_requirements': '40+ gallon terrarium with heating and hiding spots',
        'temperature_range': '78-82°F (26-28°C)',
        'humidity_level': '50-60%',
    },
    'Leopard Gecko': {
        'origin': 'Afghanistan, Pakistan, India',
        'life_span': '15-20 years',
        'size': 'small',
        'temperament': 'Gentle, Curious, Easy-going',
        'description': 'Leopard Geckos are hardy, nocturnal lizards with beautiful spotted patterns and easy care requirements, perfect for first-time reptile owners.',
        'care_level': 'beginner',
        'diet': 'Insects (crickets, mealworms, dubia roaches)',
        'housing_requirements': '20+ gallon terrarium with heating pad and hides',
        'temperature_range': '75-85°F (24-29°C)',
        'humidity_level': '30-40%',
    },
    'Guinea Pig': {
        'origin': 'South America (Andes)',
        'life_span': '5-7 years',
        'size': 'small',
        'temperament': 'Social, Gentle, Vocal, Friendly',
        'description': 'Guinea Pigs are sociable rodents that thrive in pairs and communicate through various vocalizations including wheeks, purrs, and chirps.',
        'care_level': 'beginner',
        'diet': 'Hay, pellets, fresh vegetables, vitamin C supplement',
        'housing_requirements': 'Large cage (7.5+ sq ft) with solid flooring',
        'temperature_range': '65-75°F (18-24°C)',
        'humidity_level': '40-60%',
    },
    'Axolotl': {
        'origin': 'Mexico (Lake Xochimilco)',
        'life_span': '10-15 years',
        'size': 'medium',
        'temperament': 'Calm, Curious, Passive',
        'description': 'Axolotls are unique aquatic salamanders that retain their larval features throughout life and possess remarkable regenerative abilities.',
        'care_level': 'intermediate',
        'diet': 'Bloodworms, brine shrimp, earthworms, pellets',
        'housing_requirements': '20+ gallon aquarium with filtration and cool water',
        'temperature_range': '60-64°F (16-18°C)',
        'humidity_level': 'N/A - Fully aquatic',
    },
    'Hamster': {
        'origin': 'Syria, Middle East',
        'life_span': '2-3 years',
        'size': 'small',
        'temperament': 'Curious, Active, Solitary',
        'description': 'Hamsters are popular small rodents with cheek pouches for storing food and a nocturnal lifestyle.',
        'care_level': 'beginner',
        'diet': 'Commercial hamster mix, vegetables, occasional treats',
        'housing_requirements': 'Large cage with deep bedding for burrowing',
        'temperature_range': '65-75°F (18-24°C)',
        'humidity_level': '40-60%',
    },
}

# ============== EXOTIC PETS ==============

# COMPLETE EXOTIC PETS CODE - Replace your existing exotic pets section
# This includes ALL helper functions and utilities

# ============== EXOTIC PETS DATA ==============

ALL_EXOTIC_PETS = [
    {'name': 'Bearded Dragon', 'category': 'reptile'},
    {'name': 'Ball Python', 'category': 'reptile'},
    {'name': 'Leopard Gecko', 'category': 'reptile'},
    {'name': 'Red-Eared Slider', 'category': 'reptile'},
    {'name': 'Corn Snake', 'category': 'reptile'},
    {'name': 'Blue-Tongued Skink', 'category': 'reptile'},
    {'name': 'Crested Gecko', 'category': 'reptile'},
    {'name': 'Green Iguana', 'category': 'reptile'},
    {'name': 'Russian Tortoise', 'category': 'reptile'},
    {'name': 'Betta Fish', 'category': 'fish'},
    {'name': 'Goldfish', 'category': 'fish'},
    {'name': 'Guppy', 'category': 'fish'},
    {'name': 'Neon Tetra', 'category': 'fish'},
    {'name': 'Angelfish', 'category': 'fish'},
    {'name': 'Dwarf Rabbit', 'category': 'rabbit'},
    {'name': 'Holland Lop', 'category': 'rabbit'},
    {'name': 'Lionhead Rabbit', 'category': 'rabbit'},
    {'name': 'Netherland Dwarf', 'category': 'rabbit'},
    {'name': 'Hamster', 'category': 'rodent'},
    {'name': 'Guinea Pig', 'category': 'rodent'},
    {'name': 'Gerbil', 'category': 'rodent'},
    {'name': 'Chinchilla', 'category': 'rodent'},
    {'name': 'Rat', 'category': 'rodent'},
    {'name': 'Mouse', 'category': 'rodent'},
    {'name': 'Axolotl', 'category': 'amphibian'},
    {'name': 'Fire-Bellied Toad', 'category': 'amphibian'},
    {'name': 'African Dwarf Frog', 'category': 'amphibian'},
    {'name': 'Hedgehog', 'category': 'mammal'},
    {'name': 'Sugar Glider', 'category': 'mammal'},
    {'name': 'Ferret', 'category': 'mammal'},
]

# Create a lookup dictionary for quick category access
EXOTIC_PET_CATEGORIES = {pet['name']: pet['category'] for pet in ALL_EXOTIC_PETS}

EXOTIC_BREED_INFO = {
    'Bearded Dragon': {
        'origin': 'Australia',
        'life_span': '10-15 years',
        'size': 'medium',
        'temperament': 'Docile, Curious, Friendly',
        'description': 'Bearded Dragons are popular pet lizards known for their calm demeanor and distinctive spiny throat pouch that expands like a beard when threatened. They make excellent pets for beginners due to their hardy nature and interactive personalities.',
        'care_level': 'beginner',
        'diet': 'Insects (crickets, dubia roaches), vegetables (collard greens, squash), occasional fruits',
        'housing_requirements': '40+ gallon terrarium with UVB lighting, basking spot, and temperature gradient',
        'temperature_range': '75-85°F (24-29°C) with basking spot at 95-105°F',
        'humidity_level': '30-40%',
    },
    'Ball Python': {
        'origin': 'West and Central Africa',
        'life_span': '20-30 years',
        'size': 'medium',
        'temperament': 'Calm, Docile, Shy',
        'description': 'Ball Pythons are gentle constrictors that curl into a ball when stressed, making them excellent pet snakes for beginners. They come in hundreds of beautiful color morphs and are known for their manageable size.',
        'care_level': 'beginner',
        'diet': 'Frozen-thawed rodents (mice and rats) appropriate to snake size',
        'housing_requirements': '40+ gallon terrarium with secure lid, hiding spots on both warm and cool sides',
        'temperature_range': '78-82°F (26-28°C) with basking spot at 88-92°F',
        'humidity_level': '50-60%',
    },
    'Leopard Gecko': {
        'origin': 'Afghanistan, Pakistan, India',
        'life_span': '15-20 years',
        'size': 'small',
        'temperament': 'Gentle, Curious, Easy-going',
        'description': 'Leopard Geckos are hardy, nocturnal lizards with beautiful spotted patterns and easy care requirements, perfect for first-time reptile owners. They don\'t require UVB lighting like many other lizards.',
        'care_level': 'beginner',
        'diet': 'Insects (crickets, mealworms, dubia roaches) dusted with calcium and vitamins',
        'housing_requirements': '20+ gallon terrarium with heating pad, multiple hides, and shallow water dish',
        'temperature_range': '75-85°F (24-29°C) with warm spot at 88-92°F',
        'humidity_level': '30-40%',
    },
    'Guinea Pig': {
        'origin': 'South America (Andes)',
        'life_span': '5-7 years',
        'size': 'small',
        'temperament': 'Social, Gentle, Vocal, Friendly',
        'description': 'Guinea Pigs are sociable rodents that thrive in pairs and communicate through various vocalizations including wheeks, purrs, and chirps. They require vitamin C supplementation and make wonderful family pets.',
        'care_level': 'beginner',
        'diet': 'Unlimited timothy hay, pellets, fresh vegetables daily, vitamin C supplement',
        'housing_requirements': 'Large cage (7.5+ sq ft minimum) with solid flooring and hideaways',
        'temperature_range': '65-75°F (18-24°C)',
        'humidity_level': '40-60%',
    },
    'Axolotl': {
        'origin': 'Mexico (Lake Xochimilco)',
        'life_span': '10-15 years',
        'size': 'medium',
        'temperament': 'Calm, Curious, Passive',
        'description': 'Axolotls are unique aquatic salamanders that retain their larval features throughout life and possess remarkable regenerative abilities. They come in various colors including wild type, leucistic, and golden albino.',
        'care_level': 'intermediate',
        'diet': 'Bloodworms, brine shrimp, earthworms, axolotl pellets',
        'housing_requirements': '20+ gallon aquarium with filtration, cool water (60-64°F), and gentle flow',
        'temperature_range': '60-64°F (16-18°C) - Must stay cool!',
        'humidity_level': 'N/A - Fully aquatic',
    },
    'Hamster': {
        'origin': 'Syria, Middle East',
        'life_span': '2-3 years',
        'size': 'small',
        'temperament': 'Curious, Active, Solitary',
        'description': 'Hamsters are popular small rodents with cheek pouches for storing food and a nocturnal lifestyle. Syrian hamsters are solitary while dwarf varieties can sometimes live in same-sex pairs.',
        'care_level': 'beginner',
        'diet': 'Commercial hamster mix, vegetables, occasional treats (no citrus)',
        'housing_requirements': 'Large cage (450+ sq inches) with deep bedding for burrowing, wheel, and hideaways',
        'temperature_range': '65-75°F (18-24°C)',
        'humidity_level': '40-60%',
    },
    'Betta Fish': {
        'origin': 'Thailand, Southeast Asia',
        'life_span': '3-5 years',
        'size': 'small',
        'temperament': 'Territorial, Curious, Interactive',
        'description': 'Betta fish, also known as Siamese fighting fish, are stunning freshwater fish known for their flowing fins and vibrant colors. Males are territorial and must be housed alone.',
        'care_level': 'beginner',
        'diet': 'Betta pellets, frozen or live bloodworms, brine shrimp',
        'housing_requirements': '5+ gallon filtered and heated aquarium with plants and hiding spots',
        'temperature_range': '76-82°F (24-28°C)',
        'humidity_level': 'N/A - Aquatic',
    },
    'Corn Snake': {
        'origin': 'United States (Southeastern)',
        'life_span': '15-20 years',
        'size': 'medium',
        'temperament': 'Docile, Calm, Easy to Handle',
        'description': 'Corn Snakes are one of the best pet snakes for beginners. They are non-venomous, come in beautiful color morphs, and have gentle temperaments.',
        'care_level': 'beginner',
        'diet': 'Frozen-thawed mice appropriate to snake size',
        'housing_requirements': '20+ gallon terrarium with secure lid, hiding spots, and climbing branches',
        'temperature_range': '75-85°F (24-29°C) with basking spot at 85-88°F',
        'humidity_level': '40-50%',
    },
    'Chinchilla': {
        'origin': 'Andes Mountains, South America',
        'life_span': '15-20 years',
        'size': 'medium',
        'temperament': 'Energetic, Playful, Social',
        'description': 'Chinchillas are soft-furred rodents known for having the densest fur of any land mammal. They require dust baths for grooming and are active during dawn and dusk.',
        'care_level': 'intermediate',
        'diet': 'Timothy hay, chinchilla pellets, limited treats',
        'housing_requirements': 'Large multi-level cage with platforms and dust bath area',
        'temperature_range': '60-70°F (16-21°C) - Must stay cool!',
        'humidity_level': '30-50%',
    },
    'Goldfish': {
        'origin': 'China',
        'life_span': '10-20 years',
        'size': 'small to medium',
        'temperament': 'Peaceful, Social, Active',
        'description': 'Goldfish are classic aquarium fish that can live for decades with proper care. Contrary to popular belief, they need much more space than a small bowl.',
        'care_level': 'beginner',
        'diet': 'Goldfish pellets, vegetables, occasional live or frozen food',
        'housing_requirements': '20+ gallons per fish with filtration (much more for fancy varieties)',
        'temperature_range': '65-75°F (18-24°C)',
        'humidity_level': 'N/A - Aquatic',
    },
    'Ferret': {
        'origin': 'Europe',
        'life_span': '6-10 years',
        'size': 'small',
        'temperament': 'Playful, Curious, Mischievous, Energetic',
        'description': 'Ferrets are highly social, energetic carnivores that require significant interaction and playtime. They are intelligent and can be litter trained.',
        'care_level': 'intermediate',
        'diet': 'High-protein ferret food or quality cat food, occasional raw meat',
        'housing_requirements': 'Multi-level cage with hammocks, plus 4+ hours daily free-roam time',
        'temperature_range': '60-75°F (16-24°C)',
        'humidity_level': '40-60%',
    },
    'Hedgehog': {
        'origin': 'Africa, Europe',
        'life_span': '4-7 years',
        'size': 'small',
        'temperament': 'Shy, Nocturnal, Solitary, Curious once comfortable',
        'description': 'African Pygmy Hedgehogs are popular exotic pets covered in soft spines. They are nocturnal and require patient handling to become socialized.',
        'care_level': 'intermediate',
        'diet': 'High-quality cat food, insects (mealworms, crickets), occasional fruits/vegetables',
        'housing_requirements': 'Large cage (4+ sq ft) with solid flooring, exercise wheel, hiding spots',
        'temperature_range': '72-80°F (22-27°C) - Cannot tolerate cold!',
        'humidity_level': '40-60%',
    },
}

# ============== HELPER FUNCTIONS ==============

def _get_care_level(pet_name):
    """Determine care level based on pet name"""
    pet_lower = pet_name.lower()
    
    beginner = ['hamster', 'guinea pig', 'goldfish', 'betta', 'gerbil', 
                'dwarf rabbit', 'holland lop', 'bearded dragon', 'leopard gecko',
                'corn snake', 'ball python']
    
    advanced = ['iguana', 'chameleon', 'sugar glider', 'monitor', 'boa']
    
    if any(pet in pet_lower for pet in beginner):
        return 'beginner'
    elif any(pet in pet_lower for pet in advanced):
        return 'advanced'
    
    return 'intermediate'

def _get_exotic_lifespan(pet_name, category):
    """Get lifespan based on pet name or category"""
    pet_lower = pet_name.lower()
    
    # Specific lifespans
    lifespans = {
        'bearded dragon': '10-15 years', 
        'ball python': '20-30 years',
        'leopard gecko': '15-20 years', 
        'corn snake': '15-20 years',
        'red-eared slider': '20-40 years',
        'blue-tongued skink': '15-20 years',
        'crested gecko': '15-20 years',
        'green iguana': '15-20 years',
        'russian tortoise': '40-50 years',
        'betta fish': '3-5 years',
        'goldfish': '10-20 years',
        'guppy': '2-3 years',
        'neon tetra': '5-10 years',
        'angelfish': '10-12 years',
        'hamster': '2-3 years',
        'guinea pig': '5-7 years', 
        'rabbit': '8-12 years',
        'dwarf rabbit': '8-12 years',
        'holland lop': '7-10 years',
        'lionhead rabbit': '7-10 years',
        'netherland dwarf': '10-12 years',
        'gerbil': '3-5 years',
        'chinchilla': '15-20 years',
        'rat': '2-3 years',
        'mouse': '1-3 years',
        'axolotl': '10-15 years',
        'fire-bellied toad': '10-15 years',
        'african dwarf frog': '5-10 years',
        'hedgehog': '4-7 years',
        'sugar glider': '12-15 years',
        'ferret': '6-10 years',
    }
    
    # Check for specific pet name matches
    for key, value in lifespans.items():
        if key in pet_lower:
            return value
    
    # Category-based defaults
    defaults = {
        'reptile': '10-20 years', 
        'fish': '5-10 years',
        'rodent': '3-6 years', 
        'rabbit': '8-12 years',
        'amphibian': '10-15 years',
        'mammal': '6-12 years',
    }
    
    return defaults.get(category, '5-10 years')

def _get_exotic_size(pet_name):
    """Determine size based on pet name"""
    pet_lower = pet_name.lower()
    
    small_pets = ['hamster', 'gerbil', 'mouse', 'betta', 'guppy', 'neon tetra',
                  'leopard gecko', 'fire-bellied toad', 'african dwarf frog',
                  'dwarf rabbit', 'netherland dwarf']
    
    large_pets = ['ball python', 'red-eared slider', 'chinchilla', 'green iguana',
                  'ferret', 'russian tortoise', 'corn snake']
    
    if any(pet in pet_lower for pet in small_pets):
        return 'small'
    elif any(pet in pet_lower for pet in large_pets):
        return 'large'
    
    return 'medium'

def _get_exotic_category_improved(pet_name):
    """Improved category detection for exotic pets"""
    pet_lower = pet_name.lower()
    
    # Reptile keywords
    if any(word in pet_lower for word in ['dragon', 'gecko', 'python', 'snake', 'turtle', 
                                            'slider', 'lizard', 'skink', 'corn', 'iguana', 
                                            'tortoise', 'chameleon', 'boa', 'monitor']):
        return 'reptile'
    
    # Fish keywords
    if any(word in pet_lower for word in ['fish', 'goldfish', 'betta', 'guppy', 'tetra', 
                                            'angelfish', 'molly', 'platy', 'gourami']):
        return 'fish'
    
    # Rabbit keywords
    if any(word in pet_lower for word in ['rabbit', 'bunny', 'lop', 'dwarf rabbit', 
                                            'lionhead', 'netherland']):
        return 'rabbit'
    
    # Rodent keywords
    if any(word in pet_lower for word in ['hamster', 'guinea pig', 'gerbil', 'chinchilla', 
                                            'rat', 'mouse', 'degu']):
        return 'rodent'
    
    # Amphibian keywords
    if any(word in pet_lower for word in ['frog', 'axolotl', 'toad', 'salamander', 'newt']):
        return 'amphibian'
    
    # Mammal keywords (exotic mammals)
    if any(word in pet_lower for word in ['hedgehog', 'sugar glider', 'ferret', 'skunk']):
        return 'mammal'
    
    # Default to reptile if unknown
    return 'reptile'

def _get_temperature(category):
    """Get temperature range by category"""
    temps = {
        'reptile': '75-85°F (24-29°C)',
        'fish': '72-78°F (22-26°C)',
        'amphibian': '65-75°F (18-24°C)',
        'rodent': '65-75°F (18-24°C)',
        'rabbit': '60-70°F (16-21°C)',
        'mammal': '68-75°F (20-24°C)',
    }
    return temps.get(category, '70-80°F (21-27°C)')

def _get_humidity(category):
    """Get humidity level by category"""
    humidity = {
        'reptile': '30-50%',
        'amphibian': '60-80%',
        'fish': 'N/A - Aquatic',
        'rodent': '40-60%',
        'rabbit': '40-60%',
        'mammal': '40-60%',
    }
    return humidity.get(category, '40-60%')

def _get_exotic_diet(category):
    """Get typical diet by category"""
    diets = {
        'reptile': 'Insects, vegetables, commercial reptile food',
        'fish': 'Flakes, pellets, live/frozen food',
        'rabbit': 'Hay, vegetables, pellets',
        'rodent': 'Pellets, vegetables, fruits, hay',
        'amphibian': 'Live insects, worms, pellets',
        'mammal': 'Species-specific diet with appropriate protein',
    }
    return diets.get(category, 'Species-specific diet')

def _get_exotic_housing(category):
    """Get typical housing requirements by category"""
    housing = {
        'reptile': 'Terrarium with appropriate heating and lighting',
        'fish': 'Aquarium with filtration and heating',
        'rabbit': 'Large hutch or free-roaming space with litter area',
        'rodent': 'Cage with bedding, toys, and enrichment',
        'amphibian': 'Aquatic or semi-aquatic setup with filtration',
        'mammal': 'Large enclosure with enrichment and exercise space',
    }
    return housing.get(category, 'Species-appropriate enclosure')

# ============== IMAGE FUNCTIONS ==============

def fetch_pexels_exotic_image(pet_name, category, cache_key):
    """Fetch high-quality exotic pet image from Pexels API with better error handling"""
    try:
        # Prepare optimized search terms
        search_mapping = {
            'Bearded Dragon': 'bearded dragon lizard',
            'Ball Python': 'ball python snake',
            'Leopard Gecko': 'leopard gecko lizard',
            'Corn Snake': 'corn snake',
            'Blue-Tongued Skink': 'blue tongue skink lizard',
            'Red-Eared Slider': 'red eared slider turtle',
            'Crested Gecko': 'crested gecko',
            'Green Iguana': 'green iguana',
            'Russian Tortoise': 'russian tortoise',
            'Betta Fish': 'betta fish siamese fighting',
            'Goldfish': 'goldfish aquarium',
            'Guppy': 'guppy fish',
            'Neon Tetra': 'neon tetra fish',
            'Angelfish': 'angelfish aquarium',
            'Fire-Bellied Toad': 'fire bellied toad',
            'Axolotl': 'axolotl salamander',
            'African Dwarf Frog': 'african dwarf frog',
            'Guinea Pig': 'guinea pig pet',
            'Hamster': 'hamster pet',
            'Chinchilla': 'chinchilla pet',
            'Gerbil': 'gerbil pet',
            'Rat': 'pet rat',
            'Mouse': 'pet mouse',
            'Dwarf Rabbit': 'dwarf rabbit',
            'Holland Lop': 'holland lop rabbit',
            'Lionhead Rabbit': 'lionhead rabbit',
            'Netherland Dwarf': 'netherland dwarf rabbit',
            'Hedgehog': 'hedgehog pet',
            'Sugar Glider': 'sugar glider',
            'Ferret': 'ferret pet',
        }
        
        search_term = search_mapping.get(pet_name, pet_name)
        
        url = f'https://api.pexels.com/v1/search?query={search_term}&per_page=15'
        headers = {'Authorization': PEXELS_API_KEY}
        
        response = requests.get(url, headers=headers, timeout=3.0)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('photos') and len(data['photos']) > 0:
                # Pick a random photo from top 10 results
                photo = random.choice(data['photos'][:10])
                image_url = photo['src']['medium']
                
                if image_url:
                    cache.set(cache_key, image_url, 60 * 60 * 24 * 7)  # Cache for 7 days
                    return image_url
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Pexels API error for {pet_name}: {e}")
    
    return None

def get_exotic_image_smart(pet_slug, pet_name, category):
    """Smart exotic pet image fetching with multi-layer fallback"""
    cache_key = f'exotic_img_v2_{pet_slug}'
    cached = cache.get(cache_key)
    
    if cached:
        return cached
    
    # Try Pexels first
    pexels_url = fetch_pexels_exotic_image(pet_name, category, cache_key)
    if pexels_url:
        return pexels_url
    
    # Fallback: Use curated Pexels photo IDs for common pets
    PEXELS_FALLBACK_IDS = {
        'bearded-dragon': '4791276',
        'ball-python': '7862389',
        'leopard-gecko': '4791276',
        'corn-snake': '7862389',
        'blue-tongued-skink': '4791276',
        'red-eared-slider': '5277788',
        'crested-gecko': '4791276',
        'green-iguana': '4791276',
        'russian-tortoise': '5277788',
        'guinea-pig': '4588065',
        'hamster': '4588440',
        'gerbil': '4588440',
        'chinchilla': '4588440',
        'rat': '4588440',
        'mouse': '4588440',
        'betta-fish': '1168756',
        'goldfish': '3299901',
        'guppy': '1168756',
        'neon-tetra': '1168756',
        'angelfish': '1168756',
        'axolotl': '8100784',
        'fire-bellied-toad': '8100784',
        'african-dwarf-frog': '8100784',
        'dwarf-rabbit': '7788009',
        'holland-lop': '7788009',
        'lionhead-rabbit': '7788009',
        'netherland-dwarf': '7788009',
        'ferret': '5967917',
        'hedgehog': '5967917',
        'sugar-glider': '5967917',
    }
    
    # Check for fallback photo ID
    for key, photo_id in PEXELS_FALLBACK_IDS.items():
        if key in pet_slug:
            fallback = f'https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.jpeg?auto=compress&cs=tinysrgb&w=400'
            cache.set(cache_key, fallback, 60 * 60 * 24)
            return fallback
    
    # Last resort: Unsplash
    search_term = pet_name.replace(' ', '+')
    fallback = f'https://source.unsplash.com/400x300/?{search_term}'
    cache.set(cache_key, fallback, 60 * 60 * 24)
    return fallback

def get_exotic_gallery_images_fast(pet_slug, pet_name, category, count=15):
    """Fetch multiple exotic pet images for gallery with better fallbacks"""
    cache_key = f'exotic_gallery_v2_{pet_slug}_{count}'
    cached = cache.get(cache_key)
    
    if cached:
        return cached
    
    # Prepare search terms
    search_mapping = {
        'Bearded Dragon': 'bearded dragon',
        'Ball Python': 'ball python',
        'Leopard Gecko': 'leopard gecko',
        'Corn Snake': 'corn snake',
        'Guinea Pig': 'guinea pig',
        'Hamster': 'hamster',
        'Betta Fish': 'betta fish',
        'Axolotl': 'axolotl',
        'Chinchilla': 'chinchilla',
        'Goldfish': 'goldfish',
        'Ferret': 'ferret',
        'Hedgehog': 'hedgehog',
    }
    
    search_term = search_mapping.get(pet_name, pet_name)
    
    try:
        url = f'https://api.pexels.com/v1/search?query={search_term}&per_page={count}'
        headers = {'Authorization': PEXELS_API_KEY}
        
        response = requests.get(url, headers=headers, timeout=3.0)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('photos') and len(data['photos']) > 0:
                images = [photo['src']['large'] for photo in data['photos'][:count]]
                if len(images) >= 5:  # Only cache if we got decent results
                    cache.set(cache_key, images, 60 * 60 * 24 * 7)
                    return images
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Pexels gallery error for {pet_name}: {e}")
    
    # Fallback: Generate Unsplash URLs with variations
    images = []
    search_base = pet_name.replace(' ', '+')
    for i in range(count):
        images.append(f'https://source.unsplash.com/800x600/?{search_base}&sig={i}')
    
    cache.set(cache_key, images, 60 * 60 * 24)
    return images

def get_exotic_breed_info_with_fallback(pet_name, category):
    """Get exotic pet info with intelligent defaults"""
    if pet_name in EXOTIC_BREED_INFO:
        return EXOTIC_BREED_INFO[pet_name]
    
    # Return category-based defaults
    defaults_by_category = {
        'reptile': {
            'origin': 'Various',
            'life_span': _get_exotic_lifespan(pet_name, 'reptile'),
            'size': _get_exotic_size(pet_name),
            'temperament': 'Calm, Curious',
            'description': f'The {pet_name} is a fascinating reptile with unique care requirements. Like many reptiles, it requires proper heating, lighting, and a species-appropriate diet.',
            'care_level': _get_care_level(pet_name),
            'diet': 'Insects, vegetables, commercial reptile food',
            'housing_requirements': 'Terrarium with proper heating and UVB lighting',
            'temperature_range': _get_temperature('reptile'),
            'humidity_level': _get_humidity('reptile'),
        },
        'fish': {
            'origin': 'Various',
            'life_span': _get_exotic_lifespan(pet_name, 'fish'),
            'size': _get_exotic_size(pet_name),
            'temperament': 'Peaceful, Active',
            'description': f'The {pet_name} is a beautiful aquarium fish that requires proper water parameters and tank maintenance.',
            'care_level': _get_care_level(pet_name),
            'diet': 'Fish flakes, pellets, frozen or live food',
            'housing_requirements': 'Aquarium with filtration and heating',
            'temperature_range': _get_temperature('fish'),
            'humidity_level': _get_humidity('fish'),
        },
        'rabbit': {
            'origin': 'Various',
            'life_span': _get_exotic_lifespan(pet_name, 'rabbit'),
            'size': _get_exotic_size(pet_name),
            'temperament': 'Gentle, Social, Playful',
            'description': f'The {pet_name} is a wonderful rabbit breed that makes an excellent companion pet with proper care and socialization.',
            'care_level': _get_care_level(pet_name),
            'diet': 'Unlimited hay, vegetables, limited pellets',
            'housing_requirements': 'Large hutch or free-roaming space with litter box',
            'temperature_range': _get_temperature('rabbit'),
            'humidity_level': _get_humidity('rabbit'),
        },
        'rodent': {
            'origin': 'Various',
            'life_span': _get_exotic_lifespan(pet_name, 'rodent'),
            'size': _get_exotic_size(pet_name),
            'temperament': 'Curious, Active, Social',
            'description': f'The {pet_name} is a delightful small pet that brings joy to many households with its playful personality.',
            'care_level': _get_care_level(pet_name),
            'diet': 'Commercial pellets, vegetables, limited fruits and treats',
            'housing_requirements': 'Spacious cage with bedding, toys, and enrichment',
            'temperature_range': _get_temperature('rodent'),
            'humidity_level': _get_humidity('rodent'),
        },
        'amphibian': {
            'origin': 'Various',
            'life_span': _get_exotic_lifespan(pet_name, 'amphibian'),
            'size': _get_exotic_size(pet_name),
            'temperament': 'Calm, Passive, Aquatic',
            'description': f'The {pet_name} is a unique amphibian that requires specialized aquatic or semi-aquatic care.',
            'care_level': _get_care_level(pet_name),
            'diet': 'Live insects, worms, amphibian pellets',
            'housing_requirements': 'Aquatic setup with filtration and appropriate water depth',
            'temperature_range': _get_temperature('amphibian'),
            'humidity_level': _get_humidity('amphibian'),
        },
        'mammal': {
            'origin': 'Various',
            'life_span': _get_exotic_lifespan(pet_name, 'mammal'),
            'size': _get_exotic_size(pet_name),
            'temperament': 'Playful, Curious, Social',
            'description': f'The {pet_name} is an interesting exotic mammal that requires specialized care and commitment.',
            'care_level': _get_care_level(pet_name),
            'diet': 'Species-specific diet with appropriate protein and nutrients',
            'housing_requirements': 'Large enclosure with enrichment and exercise opportunities',
            'temperature_range': _get_temperature('mammal'),
            'humidity_level': _get_humidity('mammal'),
        },
    }
    
    return defaults_by_category.get(category, defaults_by_category['reptile'])

# ============== VIEWS ==============

@api_view(['GET'])
@permission_classes([AllowAny])
def exotic_pets_list(request):
    """Paginated exotic pets list with REAL images from Pexels"""
    page_number = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 30))
    search_query = request.GET.get('search', '').lower()
    category_filter = request.GET.get('category', '').lower()
    
    # Filter by search query
    if search_query:
        pets_list = [p for p in ALL_EXOTIC_PETS if search_query in p['name'].lower()]
    else:
        pets_list = ALL_EXOTIC_PETS
    
    # Filter by category
    if category_filter:
        pets_list = [p for p in pets_list if p['category'] == category_filter]
    
    breeds_data = []
    for idx, pet in enumerate(pets_list):
        slug = slugify(pet['name'])
        category = pet['category']
        
        # Get breed info for additional fields
        info = get_exotic_breed_info_with_fallback(pet['name'], category)
        
        # Get real image using Pexels/Unsplash
        image = get_exotic_image_smart(slug, pet['name'], category)
        
        breed_info = {
            'id': idx + 1,
            'name': pet['name'],
            'slug': slug,
            'image': image,
            'category': category,
            'care_level': info.get('care_level', 'intermediate'),
            'life_span': info.get('life_span', '5-10 years'),
            'temperament': info.get('temperament', 'Varies'),
            'size': info.get('size', 'medium'),
            'is_popular': idx < 10
        }
        breeds_data.append(breed_info)
    
    paginator = Paginator(breeds_data, page_size)
    page_obj = paginator.get_page(page_number)
    
    return Response({
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': page_number,
        'page_size': page_size,
        'results': page_obj.object_list
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def exotic_pet_detail(request, slug):
    """Detailed exotic pet info with real image gallery"""
    # Convert slug back to name
    pet_name = slug.replace('-', ' ').title()
    
    # Get category from lookup dict
    category = EXOTIC_PET_CATEGORIES.get(pet_name)
    
    # If not found in lookup, try to determine category
    if not category:
        category = _get_exotic_category_improved(pet_name)
    
    # Get breed info
    breed_info = get_exotic_breed_info_with_fallback(pet_name, category)
    
    # Get gallery images from Pexels
    gallery_images = get_exotic_gallery_images_fast(slug, pet_name, category, 15)
    main_image = gallery_images[0] if gallery_images else get_exotic_image_smart(slug, pet_name, category)
    
    # Get YouTube videos
    youtube_videos = get_youtube_videos_cached(pet_name, 6)
    
    breed_detail = {
        'id': 1,
        'name': pet_name,
        'slug': slug,
        'species': 'exotic',
        'category': category,
        'main_image': main_image,
        'image': main_image,  # Some frontends might expect 'image' instead of 'main_image'
        'gallery_images': gallery_images,
        'description': breed_info.get('description', f'The {pet_name} is a fascinating exotic pet.'),
        'origin': breed_info.get('origin', 'Various'),
        'life_span': breed_info.get('life_span', '5-10 years'),
        'size': breed_info.get('size', 'medium'),
        'temperament': breed_info.get('temperament', 'Varies by species'),
        'care_level': breed_info.get('care_level', 'intermediate'),
        'diet': breed_info.get('diet', 'Species-specific diet'),
        'housing_requirements': breed_info.get('housing_requirements', 'Species-appropriate enclosure'),
        'temperature_range': breed_info.get('temperature_range', '70-80°F (21-27°C)'),
        'humidity_level': breed_info.get('humidity_level', '40-60%'),
        'health_concerns': 'Species-specific care required. Consult with exotic animal veterinarian regularly.',
        'youtube_videos': youtube_videos,
        'wikipedia_url': f'https://en.wikipedia.org/wiki/{pet_name.replace(" ", "_")}',
    }
    
    return Response(breed_detail)