# products/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()
class ProductCategory(models.Model):
    """
    Hierarchical category system for granular filtering
    Examples:
    - Food > Dry Food > Cat Dry Food
    - Toys > Interactive Toys > Cat Interactive Toys
    - Grooming > Brushes > Long Hair Brushes
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    
    # Category metadata
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class name")
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    
    # For filtering
    species = models.CharField(
        max_length=20,
        choices=[
            ('all', 'All Pets'),
            ('dog', 'Dog'),
            ('cat', 'Cat'),
            ('bird', 'Bird'),
            ('fish', 'Fish'),
            ('small_pet', 'Small Pet'),
        ],
        default='all'
    )
    
    # Category type for specific filtering
    category_type = models.CharField(
        max_length=50,
        choices=[
            ('food', 'Food'),
            ('treats', 'Treats'),
            ('toys', 'Toys'),
            ('grooming', 'Grooming'),
            ('health', 'Health & Medicine'),
            ('accessories', 'Accessories'),
            ('housing', 'Housing & Bedding'),
            ('training', 'Training'),
            ('other', 'Other'),
        ],
        blank=True
    )
    
    # Sub-type for even more specific filtering
    sub_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g., 'dry', 'wet', 'interactive', 'plush'"
    )
    
    # Display order
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = 'Product Categories'
        ordering = ['order', 'name']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    def get_full_path(self):
        """Get full category path like 'Food > Cat Food > Dry Food'"""
        path = [self.name]
        parent = self.parent
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent
        return ' > '.join(path)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Brand(models.Model):
    """Product brands"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True) 
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """
    Main Product model for pet product suggestions
    Not for e-commerce - focuses on recommendations and information
    """
    
    # Basic Info
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()
    
    # Categorization
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products'
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    
    # Pet Information
    species = models.CharField(
        max_length=20,
        choices=[
            ('dog', 'Dog'),
            ('cat', 'Cat'),
            ('bird', 'Bird'),
            ('fish', 'Fish'),
            ('rabbit', 'Rabbit'),
            ('hamster', 'Hamster'),
            ('guinea_pig', 'Guinea Pig'),
            ('reptile', 'Reptile'),
            ('other', 'Other'),
        ]
    )
    
    # Specific breed suitability (optional)
    suitable_breeds = models.JSONField(
        default=list,
        blank=True,
        help_text="List of breed names this product is suitable for"
    )
    
    # Age group suitability
    age_group = models.CharField(
        max_length=50,
        choices=[
            ('all', 'All Ages'),
            ('puppy_kitten', 'Puppy/Kitten'),
            ('adult', 'Adult'),
            ('senior', 'Senior'),
        ],
        default='all'
    )
    
    # Size suitability (for dogs mainly)
    size_suitability = models.CharField(
        max_length=50,
        choices=[
            ('all', 'All Sizes'),
            ('small', 'Small (< 25 lbs)'),
            ('medium', 'Medium (25-50 lbs)'),
            ('large', 'Large (50-100 lbs)'),
            ('xlarge', 'Extra Large (> 100 lbs)'),
        ],
        default='all'
    )
    
    # Product Specifics (for filtering)
    food_type = models.CharField(
        max_length=20,
        choices=[
            ('', 'Not Food'),
            ('dry', 'Dry Food'),
            ('wet', 'Wet Food'),
            ('raw', 'Raw Food'),
            ('freeze_dried', 'Freeze Dried'),
            ('dehydrated', 'Dehydrated'),
        ],
        blank=True
    )
    
    toy_type = models.CharField(
        max_length=30,
        choices=[
            ('', 'Not Toy'),
            ('interactive', 'Interactive'),
            ('plush', 'Plush/Soft'),
            ('chew', 'Chew Toy'),
            ('puzzle', 'Puzzle'),
            ('fetch', 'Fetch/Throw'),
            ('teaser', 'Teaser/Wand'),
            ('ball', 'Ball'),
        ],
        blank=True
    )
    
    grooming_type = models.CharField(
        max_length=30,
        choices=[
            ('', 'Not Grooming'),
            ('brush', 'Brush/Comb'),
            ('shampoo', 'Shampoo/Conditioner'),
            ('nail_care', 'Nail Care'),
            ('dental', 'Dental Care'),
            ('ear_care', 'Ear Care'),
            ('cologne', 'Cologne/Deodorizer'),
        ],
        blank=True
    )
    
    health_type = models.CharField(
        max_length=30,
        choices=[
            ('', 'Not Health Product'),
            ('supplement', 'Supplement'),
            ('medication', 'Medication'),
            ('flea_tick', 'Flea & Tick'),
            ('vitamins', 'Vitamins'),
            ('first_aid', 'First Aid'),
        ],
        blank=True
    )
    
    # Additional attributes for filtering
    material = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=50, blank=True)
    weight = models.CharField(max_length=50, blank=True, help_text="Product weight or pet weight range")
    dimensions = models.CharField(max_length=100, blank=True)
    
    # Pricing (for reference, not selling)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Approximate price for reference"
    )
    original_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    
    # Media
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    image_url = models.URLField(blank=True, help_text="External image URL")
    
    # Where to buy links
    platform_links = models.JSONField(
        default=dict,
        blank=True,
        help_text="Links to purchase platforms: {'amazon': 'url', 'chewy': 'url', ...}"
    )
    
    # Availability
    stock = models.IntegerField(default=0, help_text="General availability indicator")
    is_available = models.BooleanField(default=True)
    
    # Tags for flexible filtering
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Additional tags: ['grain-free', 'organic', 'usa-made', ...]"
    )
    
    # Ratings and Stats
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    review_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)
    save_count = models.IntegerField(default=0)
    
    # Flags
    is_trending = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_recommended = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_products'
    )
    
    class Meta:
        ordering = ['-is_featured', '-is_trending', '-rating']
        indexes = [
            models.Index(fields=['species', 'category']),
            models.Index(fields=['food_type']),
            models.Index(fields=['toy_type']),
            models.Index(fields=['-rating', '-review_count']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def increment_views(self):
        """Increment view count"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def get_discount_percentage(self):
        """Calculate discount percentage"""
        if self.original_price and self.original_price > self.price:
            return round(((self.original_price - self.price) / self.original_price) * 100)
        return 0


class ProductImage(models.Model):
    """Additional product images"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.product.name} - Image {self.order}"


class SavedProduct(models.Model):
    """User's saved/bookmarked products"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='saved_by')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'product']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class ProductView(models.Model):
    """Track product views for recommendations"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_views')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['product', '-created_at']),
        ]
    
    def __str__(self):
        user_str = self.user.username if self.user else f"Session: {self.session_id}"
        return f"{user_str} viewed {self.product.name}"