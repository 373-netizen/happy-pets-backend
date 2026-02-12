# products/real_products_data.py
"""
Curated real pet products with actual purchase links
No API or scraping needed - all data is manually curated
"""

REAL_PET_PRODUCTS = {
    'dog_food': [
        {
            'name': 'Blue Buffalo Life Protection Formula Adult Chicken & Brown Rice Recipe',
            'description': 'Real chicken is the first ingredient. Natural ingredients enhanced with vitamins and minerals. No chicken by-product meals.',
            'price': 54.98,
            'original_price': 64.99,
            'category': 'food',
            'species': 'dog',
            'suitable_breeds': ['all'],
            'brand': 'Blue Buffalo',
            'weight': '30 lbs',
            'rating': 4.7,
            'review_count': 68543,
            'image_url': 'https://images.unsplash.com/photo-1589924691995-400dc9ecc119?w=800',
            'purchase_url': 'https://www.chewy.com/blue-buffalo-life-protection-formula/dp/34406',
            'tags': ['natural', 'chicken', 'brown-rice', 'no-by-products'],
            'is_trending': True,
            'stock': 150,
            'features': [
                'Real chicken first ingredient',
                'Natural ingredients',
                'Life source bits',
                'No poultry by-products'
            ]
        },
        {
            'name': "Hill's Science Diet Adult Large Breed Dry Dog Food",
            'description': 'Clinically proven antioxidants for immune system support. High-quality protein for lean muscle. Glucosamine and chondroitin for joint health.',
            'price': 59.99,
            'original_price': 69.99,
            'category': 'food',
            'species': 'dog',
            'suitable_breeds': ['Golden Retriever', 'Labrador', 'German Shepherd', 'Husky', 'Rottweiler'],
            'brand': "Hill's Science Diet",
            'weight': '35 lbs',
            'rating': 4.8,
            'review_count': 45231,
            'image_url': 'https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?w=800',
            'purchase_url': 'https://www.chewy.com/hills-science-diet-adult-large-breed/dp/51435',
            'tags': ['large-breed', 'veterinarian-recommended', 'joint-support'],
            'is_trending': True,
            'stock': 125,
            'features': [
                'Clinically proven antioxidants',
                'Joint support',
                'Vet recommended',
                'Balanced nutrition'
            ]
        },
        {
            'name': 'Purina Pro Plan High Protein Dog Food With Probiotics',
            'description': 'Real chicken is #1 ingredient. Fortified with guaranteed live probiotics for digestive and immune health.',
            'price': 67.48,
            'original_price': 79.99,
            'category': 'food',
            'species': 'dog',
            'suitable_breeds': ['all'],
            'brand': 'Purina Pro Plan',
            'weight': '47 lbs',
            'rating': 4.8,
            'review_count': 52847,
            'image_url': 'https://images.unsplash.com/photo-1628009368231-7bb7cfcb0def?w=800',
            'purchase_url': 'https://www.chewy.com/purina-pro-plan-adult-shredded-blend/dp/52456',
            'tags': ['high-protein', 'probiotics', 'chicken', 'immune-support'],
            'is_trending': False,
            'stock': 200,
            'features': [
                '30% protein',
                'Live probiotics',
                'Real chicken #1',
                'Immune health'
            ]
        },
        {
            'name': 'Royal Canin Medium Breed Adult Dry Dog Food',
            'description': 'Balanced nutrition for medium breed dogs aged 1-7 years. Optimal protein content helps maintain muscle mass.',
            'price': 54.99,
            'original_price': 64.99,
            'category': 'food',
            'species': 'dog',
            'suitable_breeds': ['Beagle', 'Cocker Spaniel', 'Bulldog', 'Border Collie'],
            'brand': 'Royal Canin',
            'weight': '30 lbs',
            'rating': 4.7,
            'review_count': 31254,
            'image_url': 'https://images.unsplash.com/photo-1615751072497-5f5169febe17?w=800',
            'purchase_url': 'https://www.chewy.com/royal-canin-medium-adult-dry-dog/dp/48325',
            'tags': ['medium-breed', 'balanced-nutrition', 'muscle-support'],
            'is_trending': False,
            'stock': 180,
            'features': [
                'Medium breed formula',
                'Optimal protein',
                'Healthy digestion',
                'Skin & coat support'
            ]
        },
        {
            'name': 'Taste of the Wild High Prairie Grain-Free Dog Food',
            'description': 'Real buffalo and venison. Grain-free recipe with sweet potatoes and peas. High protein diet inspired by nature.',
            'price': 52.99,
            'original_price': 62.99,
            'category': 'food',
            'species': 'dog',
            'suitable_breeds': ['Husky', 'Malamute', 'German Shepherd', 'Australian Shepherd'],
            'brand': 'Taste of the Wild',
            'weight': '28 lbs',
            'rating': 4.6,
            'review_count': 41236,
            'image_url': 'https://images.unsplash.com/photo-1534361960057-19889db9621e?w=800',
            'purchase_url': 'https://www.chewy.com/taste-wild-high-prairie-grain-free/dp/49278',
            'tags': ['grain-free', 'buffalo', 'venison', 'high-protein'],
            'is_trending': True,
            'stock': 160,
            'features': [
                'Real buffalo & venison',
                'Grain-free',
                'Probiotics',
                'Antioxidants'
            ]
        }
    ],
    
    'dog_toys': [
        {
            'name': 'KONG Classic Dog Toy - Red',
            'description': 'The KONG Classic is the gold standard of dog toys. Durable rubber formula is designed for determined chewers.',
            'price': 13.49,
            'original_price': 16.99,
            'category': 'toys',
            'species': 'dog',
            'suitable_breeds': ['all'],
            'brand': 'KONG',
            'size': 'Large',
            'rating': 4.7,
            'review_count': 87324,
            'image_url': 'https://images.unsplash.com/photo-1591769225440-811ad7d6eab3?w=800',
            'purchase_url': 'https://www.chewy.com/kong-classic-dog-toy-red/dp/38482',
            'tags': ['durable', 'treat-dispenser', 'chew-toy', 'vet-recommended'],
            'is_trending': True,
            'stock': 300,
            'features': [
                'Unpredictable bounce',
                'Dishwasher safe',
                'Made in USA',
                'Fill with treats'
            ]
        },
        {
            'name': 'Chuckit! Ultra Ball 2-Pack',
            'description': 'High bounce, durable rubber ball designed for the game of fetch. Bright colors for easy visibility.',
            'price': 9.95,
            'original_price': 12.99,
            'category': 'toys',
            'species': 'dog',
            'suitable_breeds': ['Golden Retriever', 'Labrador', 'Border Collie', 'all'],
            'brand': 'Chuckit!',
            'size': 'Medium',
            'rating': 4.6,
            'review_count': 42567,
            'image_url': 'https://images.unsplash.com/photo-1535400587924-3934f1167e2e?w=800',
            'purchase_url': 'https://www.chewy.com/chuckit-ultra-ball-medium/dp/45231',
            'tags': ['fetch', 'durable', 'high-bounce', 'water-float'],
            'is_trending': True,
            'stock': 250,
            'features': [
                'High bounce',
                'Bright colors',
                'Compatible with launcher',
                'Floats in water'
            ]
        },
        {
            'name': 'Nylabone Dura Chew Power Chew Textured Ring',
            'description': 'Long-lasting chew toy made of tough, durable nylon. Massages gums and cleans teeth as dogs chew.',
            'price': 8.99,
            'original_price': 11.99,
            'category': 'toys',
            'species': 'dog',
            'suitable_breeds': ['German Shepherd', 'Rottweiler', 'Husky', 'Pit Bull'],
            'brand': 'Nylabone',
            'size': 'Large',
            'rating': 4.5,
            'review_count': 35421,
            'image_url': 'https://images.unsplash.com/photo-1623387641168-d9803ddd3f35?w=800',
            'purchase_url': 'https://www.chewy.com/nylabone-dura-chew-textured-ring/dp/38901',
            'tags': ['power-chewer', 'dental', 'long-lasting', 'made-in-usa'],
            'is_trending': False,
            'stock': 275,
            'features': [
                'Aggressive chewer approved',
                'Dental benefits',
                'Long lasting',
                'Bacon flavored'
            ]
        },
        {
            'name': 'ZippyPaws Skinny Peltz No Stuffing Squeaky Plush Dog Toys, 3 Pack',
            'description': 'No stuffing means less mess! Each toy has 1 round squeaker. Perfect for dogs who love to fetch and squeak.',
            'price': 12.99,
            'original_price': 15.99,
            'category': 'toys',
            'species': 'dog',
            'suitable_breeds': ['all'],
            'brand': 'ZippyPaws',
            'size': 'Small',
            'rating': 4.6,
            'review_count': 28934,
            'image_url': 'https://images.unsplash.com/photo-1601758228041-f3b2795255f1?w=800',
            'purchase_url': 'https://www.chewy.com/zippypaws-skinny-peltz-no-stuffing/dp/52318',
            'tags': ['no-stuffing', 'squeaky', 'set-of-3', 'plush'],
            'is_trending': False,
            'stock': 200,
            'features': [
                'No stuffing mess',
                'Squeakers inside',
                'Cute characters',
                '3-pack value'
            ]
        }
    ],
    
    'grooming': [
        {
            'name': 'FURminator deShedding Tool for Large Dogs - Long Hair',
            'description': 'Reduces shedding up to 90%. Stainless steel edge reaches through topcoat to remove loose undercoat hair.',
            'price': 39.99,
            'original_price': 49.99,
            'category': 'grooming',
            'species': 'dog',
            'suitable_breeds': ['Golden Retriever', 'Husky', 'German Shepherd', 'Collie', 'Bernese Mountain Dog'],
            'brand': 'FURminator',
            'size': 'Large',
            'rating': 4.6,
            'review_count': 67821,
            'image_url': 'https://images.unsplash.com/photo-1616398643070-045f06e8d0d7?w=800',
            'purchase_url': 'https://www.chewy.com/furminator-long-hair-deshedding-edge/dp/38714',
            'tags': ['deshedding', 'large-breed', 'stainless-steel', 'long-hair'],
            'is_trending': True,
            'stock': 150,
            'features': [
                'Reduces shedding 90%',
                'Stainless steel edge',
                'Ergonomic handle',
                'FURejector button'
            ]
        },
        {
            'name': "Burt's Bees for Dogs Natural Shampoo 2-in-1",
            'description': 'Tearless formula made with honey. Gentle, pH balanced for dogs. Made in the USA.',
            'price': 14.99,
            'original_price': 18.99,
            'category': 'grooming',
            'species': 'dog',
            'suitable_breeds': ['all'],
            'brand': "Burt's Bees",
            'size': '16 oz',
            'rating': 4.7,
            'review_count': 41256,
            'image_url': 'https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?w=800',
            'purchase_url': 'https://www.chewy.com/burts-bees-dogs-natural-shampoo/dp/54234',
            'tags': ['natural', 'tearless', 'honey', '2-in-1', 'made-in-usa'],
            'is_trending': False,
            'stock': 300,
            'features': [
                'Tearless formula',
                'Natural ingredients',
                'Shampoo & conditioner',
                'No sulfates or parabens'
            ]
        },
        {
            'name': 'Safari Professional Large Nail Trimmer for Dogs',
            'description': 'Professional quality nail clippers with safety stop to prevent over-cutting. Sharp stainless steel blades.',
            'price': 10.99,
            'original_price': 14.99,
            'category': 'grooming',
            'species': 'dog',
            'suitable_breeds': ['all'],
            'brand': 'Safari',
            'size': 'Large',
            'rating': 4.5,
            'review_count': 23456,
            'image_url': 'https://images.unsplash.com/photo-1612536621073-8e0d4e3e3b16?w=800',
            'purchase_url': 'https://www.chewy.com/safari-professional-large-nail/dp/39124',
            'tags': ['nail-trimmer', 'safety-stop', 'professional', 'stainless-steel'],
            'is_trending': False,
            'stock': 225,
            'features': [
                'Safety stop blade',
                'Sharp stainless steel',
                'Non-slip handles',
                'Professional quality'
            ]
        }
    ],
    
    'accessories': [
        {
            'name': 'Blueberry Pet Classic Solid Color Dog Collar',
            'description': 'Durable nylon collar with quick-release buckle. Color-matched plastic hardware.',
            'price': 13.99,
            'original_price': 17.99,
            'category': 'accessories',
            'species': 'dog',
            'suitable_breeds': ['all'],
            'brand': 'Blueberry Pet',
            'size': 'Medium (15-20 inches)',
            'rating': 4.6,
            'review_count': 18234,
            'image_url': 'https://images.unsplash.com/photo-1601758228041-f3b2795255f1?w=800',
            'purchase_url': 'https://www.chewy.com/blueberry-pet-classic-solid-color/dp/45892',
            'tags': ['collar', 'durable', 'adjustable', 'quick-release'],
            'is_trending': False,
            'stock': 400,
            'features': [
                'Durable nylon',
                'Quick-release buckle',
                'Adjustable fit',
                'Machine washable'
            ]
        },
        {
            'name': 'Flexi Classic Retractable Dog Leash - 16 ft',
            'description': 'Retractable tape leash for dogs up to 110 lbs. One-button braking system. Ergonomic handle.',
            'price': 24.99,
            'original_price': 32.99,
            'category': 'accessories',
            'species': 'dog',
            'suitable_breeds': ['all'],
            'brand': 'Flexi',
            'size': 'Large - 16 ft',
            'rating': 4.5,
            'review_count': 34567,
            'image_url': 'https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=800',
            'purchase_url': 'https://www.chewy.com/flexi-classic-retractable-tape-dog/dp/48751',
            'tags': ['retractable', '16-feet', 'one-hand-brake', 'ergonomic'],
            'is_trending': True,
            'stock': 275,
            'features': [
                '16 ft freedom',
                'One-hand brake',
                'Up to 110 lbs',
                'Comfortable grip'
            ]
        },
        {
            'name': 'Rabbitgoo No-Pull Dog Harness with Handle',
            'description': 'Reflective adjustable harness with easy control handle. 2 leash attachment rings.',
            'price': 21.99,
            'original_price': 29.99,
            'category': 'accessories',
            'species': 'dog',
            'suitable_breeds': ['Husky', 'German Shepherd', 'Golden Retriever', 'Labrador', 'Pit Bull'],
            'brand': 'Rabbitgoo',
            'size': 'Large',
            'rating': 4.6,
            'review_count': 52341,
            'image_url': 'https://images.unsplash.com/photo-1548199973-03cce0bbc87b?w=800',
            'purchase_url': 'https://www.chewy.com/rabbitgoo-no-pull-dog-harness/dp/51234',
            'tags': ['no-pull', 'reflective', 'adjustable', 'handle'],
            'is_trending': True,
            'stock': 350,
            'features': [
                'No-pull design',
                'Reflective stitching',
                'Easy control handle',
                '2 leash rings'
            ]
        }
    ],
    
    'health': [
        {
            'name': 'Zesty Paws Glucosamine for Dogs - Hip & Joint Support',
            'description': 'Hip & joint supplement with glucosamine, chondroitin, and MSM. Chicken flavored soft chews.',
            'price': 29.97,
            'original_price': 39.99,
            'category': 'health',
            'species': 'dog',
            'suitable_breeds': ['Golden Retriever', 'Labrador', 'German Shepherd', 'Rottweiler', 'all'],
            'brand': 'Zesty Paws',
            'count': '90 chews',
            'rating': 4.5,
            'review_count': 45678,
            'image_url': 'https://images.unsplash.com/photo-1628009368231-7bb7cfcb0def?w=800',
            'purchase_url': 'https://www.chewy.com/zesty-paws-mobility-bites-hip-joint/dp/54892',
            'tags': ['joint-support', 'glucosamine', 'chondroitin', 'senior-dogs'],
            'is_trending': False,
            'stock': 275,
            'features': [
                'Glucosamine 300mg',
                'Chondroitin',
                'MSM for inflammation',
                'Chicken flavor'
            ]
        },
        {
            'name': 'Purina FortiFlora Dog Probiotic Powder Supplement',
            'description': 'Probiotic supplement for digestive health. Helps reduce gas and diarrhea. Veterinary recommended.',
            'price': 32.99,
            'original_price': 42.99,
            'category': 'health',
            'species': 'dog',
            'suitable_breeds': ['all'],
            'brand': 'Purina Pro Plan',
            'count': '30 sachets',
            'rating': 4.7,
            'review_count': 38945,
            'image_url': 'https://images.unsplash.com/photo-1615751072497-5f5169febe17?w=800',
            'purchase_url': 'https://www.chewy.com/purina-pro-plan-veterinary-diets/dp/49238',
            'tags': ['probiotic', 'digestive-health', 'vet-recommended', 'diarrhea'],
            'is_trending': True,
            'stock': 200,
            'features': [
                'Live probiotics',
                'Vet recommended',
                'Immune support',
                'Easy to use'
            ]
        },
        {
            'name': 'Nutri-Vet Multi-Vite Chewables for Dogs',
            'description': 'Complete multivitamin with essential vitamins and minerals. Liver flavor dogs love.',
            'price': 11.99,
            'original_price': 16.99,
            'category': 'health',
            'species': 'dog',
            'suitable_breeds': ['all'],
            'brand': 'Nutri-Vet',
            'count': '120 chewables',
            'rating': 4.6,
            'review_count': 12456,
            'image_url': 'https://images.unsplash.com/photo-1534361960057-19889db9621e?w=800',
            'purchase_url': 'https://www.chewy.com/nutri-vet-multi-vite-chewables-dogs/dp/38451',
            'tags': ['multivitamin', 'essential-vitamins', 'liver-flavor', 'daily-supplement'],
            'is_trending': False,
            'stock': 325,
            'features': [
                'Complete multivitamin',
                'Essential minerals',
                'Liver flavor',
                '120-day supply'
            ]
        }
    ],
    
    'beds': [
        {
            'name': 'Furhaven Orthopedic Dog Bed with Removable Cover',
            'description': 'Memory foam dog bed with removable, machine-washable cover. Perfect for senior dogs and large breeds.',
            'price': 42.99,
            'original_price': 59.99,
            'category': 'beds',
            'species': 'dog',
            'suitable_breeds': ['Golden Retriever', 'Labrador', 'German Shepherd', 'Rottweiler', 'all'],
            'brand': 'Furhaven',
            'size': 'Large - 36" x 27"',
            'rating': 4.5,
            'review_count': 56234,
            'image_url': 'https://images.unsplash.com/photo-1601758123927-64b5384f4588?w=800',
            'purchase_url': 'https://www.chewy.com/furhaven-ultra-plush-luxe-lounger/dp/51892',
            'tags': ['orthopedic', 'memory-foam', 'washable', 'senior-dogs'],
            'is_trending': False,
            'stock': 175,
            'features': [
                'Orthopedic memory foam',
                'Removable cover',
                'Machine washable',
                'Non-slip bottom'
            ]
        },
        {
            'name': 'Best Pet Supplies Cozy Cave Hooded Dog Bed',
            'description': 'Hooded cave bed for dogs who love to burrow. Soft sherpa interior. Perfect for anxious dogs.',
            'price': 39.95,
            'original_price': 52.99,
            'category': 'beds',
            'species': 'dog',
            'suitable_breeds': ['all'],
            'brand': 'Best Pet Supplies',
            'size': 'Medium - 25"',
            'rating': 4.6,
            'review_count': 28934,
            'image_url': 'https://images.unsplash.com/photo-1591769225440-811ad7d6eab3?w=800',
            'purchase_url': 'https://www.chewy.com/best-pet-supplies-tent-cave-pet-bed/dp/48923',
            'tags': ['cave-bed', 'cozy', 'hooded', 'anxiety-relief'],
            'is_trending': True,
            'stock': 150,
            'features': [
                'Hooded design',
                'Sherpa interior',
                'Anxiety relief',
                'Machine washable'
            ]
        },
        {
            'name': 'K&H Pet Products Elevated Dog Bed',
            'description': 'Elevated mesh bed keeps dogs cool and comfortable. Perfect for outdoor use. Easy to clean.',
            'price': 34.99,
            'original_price': 44.99,
            'category': 'beds',
            'species': 'dog',
            'suitable_breeds': ['all'],
            'brand': 'K&H Pet Products',
            'size': 'Large - 30" x 42"',
            'rating': 4.7,
            'review_count': 19234,
            'image_url': 'https://images.unsplash.com/photo-1535400587924-3934f1167e2e?w=800',
            'purchase_url': 'https://www.chewy.com/kh-pet-products-original-elevated/dp/39851',
            'tags': ['elevated', 'outdoor', 'breathable', 'easy-clean'],
            'is_trending': False,
            'stock': 200,
            'features': [
                'Elevated design',
                'Breathable mesh',
                'Outdoor safe',
                'Easy assembly'
            ]
        }
    ]
}


def get_all_products():
    """Get all products as a flat list"""
    all_products = []
    for category, products in REAL_PET_PRODUCTS.items():
        all_products.extend(products)
    return all_products


def get_products_by_category(category):
    """Get products by category"""
    return REAL_PET_PRODUCTS.get(category, [])


def get_products_by_breed(breed):
    """Get products suitable for a specific breed"""
    all_products = get_all_products()
    return [
        p for p in all_products 
        if breed in p['suitable_breeds'] or 'all' in p['suitable_breeds']
    ]