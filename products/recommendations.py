# products/recommendations.py
from django.db.models import Q, Count, Avg, F
from django.contrib.auth.models import User
from .models import Product, ProductView, SavedProduct, ProductCategory
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class SmartRecommendationEngine:
    """
    Intelligent recommendation engine for pet products
    
    Recommendation strategies:
    1. Based on viewing history
    2. Based on saved products
    3. Complementary products
    4. Similar products
    5. Popular in category
    6. Trending products
    """
    
    def __init__(self, user: Optional[User] = None, session_id: Optional[str] = None):
        self.user = user
        self.session_id = session_id
    
    def get_recommendations(
        self,
        species: Optional[str] = None,
        limit: int = 12,
        context_product: Optional[Product] = None
    ) -> List[Product]:
        """
        Get personalized recommendations
        
        Args:
            species: Filter by pet species
            limit: Number of recommendations
            context_product: Product user is currently viewing
            
        Returns:
            List of recommended Product objects
        """
        if context_product:
            # Context-aware recommendations based on current product
            return self._get_context_recommendations(context_product, limit)
        
        if self.user and self.user.is_authenticated:
            return self._get_user_recommendations(species, limit)
        
        return self._get_general_recommendations(species, limit)
    
    def _get_user_recommendations(self, species: Optional[str], limit: int) -> List[Product]:
        """
        Get personalized recommendations for authenticated users
        """
        recommendations = []
        
        # Strategy 1: Based on recently viewed products
        recent_recs = self._recommendations_from_views(species, limit // 3)
        recommendations.extend(recent_recs)
        
        # Strategy 2: Based on saved products
        saved_recs = self._recommendations_from_saved(species, limit // 3)
        recommendations.extend(saved_recs)
        
        # Strategy 3: Fill remaining with trending/popular
        remaining = limit - len(recommendations)
        if remaining > 0:
            trending_recs = self._get_trending(species, remaining)
            recommendations.extend(trending_recs)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recs = []
        for product in recommendations:
            if product.id not in seen:
                seen.add(product.id)
                unique_recs.append(product)
        
        return unique_recs[:limit]
    
    def _recommendations_from_views(self, species: Optional[str], limit: int) -> List[Product]:
        """
        Get recommendations based on user's viewing history
        """
        # Get recently viewed products
        recent_views = ProductView.objects.filter(
            user=self.user
        ).select_related('product').order_by('-created_at')[:20]
        
        if not recent_views:
            return []
        
        viewed_product_ids = [view.product.id for view in recent_views]
        viewed_products = Product.objects.filter(id__in=viewed_product_ids)
        
        # Analyze viewing patterns
        categories = set()
        food_types = set()
        toy_types = set()
        tags = set()
        
        for product in viewed_products:
            if product.category:
                categories.add(product.category.id)
            if product.food_type:
                food_types.add(product.food_type)
            if product.toy_type:
                toy_types.add(product.toy_type)
            if product.tags:
                tags.update(product.tags)
        
        # Build recommendation query
        query = Q(is_available=True)
        
        # Exclude already viewed
        query &= ~Q(id__in=viewed_product_ids)
        
        # Filter by species if provided
        if species:
            query &= Q(species=species)
        
        # Match categories, types, or tags
        match_query = Q()
        if categories:
            match_query |= Q(category_id__in=categories)
        if food_types:
            match_query |= Q(food_type__in=food_types)
        if toy_types:
            match_query |= Q(toy_type__in=toy_types)
        if tags:
            for tag in tags:
                match_query |= Q(tags__icontains=tag)
        
        if match_query:
            query &= match_query
        
        recommendations = Product.objects.filter(query).distinct().order_by(
            '-rating', '-review_count', '-view_count'
        )[:limit]
        
        return list(recommendations)
    
    def _recommendations_from_saved(self, species: Optional[str], limit: int) -> List[Product]:
        """
        Get recommendations based on user's saved products
        """
        saved_products = SavedProduct.objects.filter(
            user=self.user
        ).select_related('product').order_by('-created_at')[:10]
        
        if not saved_products:
            return []
        
        saved_product_ids = [sp.product.id for sp in saved_products]
        saved_prods = Product.objects.filter(id__in=saved_product_ids)
        
        # Find similar products to saved ones
        recommendations = []
        
        for product in saved_prods:
            similar = self._get_similar_products(product, limit=3)
            recommendations.extend(similar)
        
        # Filter by species
        if species:
            recommendations = [p for p in recommendations if p.species == species]
        
        # Remove saved products from recommendations
        recommendations = [p for p in recommendations if p.id not in saved_product_ids]
        
        return recommendations[:limit]
    
    def _get_context_recommendations(self, product: Product, limit: int) -> List[Product]:
        """
        Get context-aware recommendations when user is viewing a specific product
        
        If viewing dry cat food:
        - Show more dry cat food (same type)
        - Show wet cat food (complementary)
        - Show cat treats (complementary)
        - Show cat toys (related)
        """
        recommendations = []
        
        # Strategy 1: Similar products (same type, different brands)
        similar = self._get_similar_products(product, limit=limit // 2)
        recommendations.extend(similar)
        
        # Strategy 2: Complementary products
        complementary = self._get_complementary_products(product, limit=limit // 2)
        recommendations.extend(complementary)
        
        # Remove duplicates
        seen = set()
        unique_recs = []
        for p in recommendations:
            if p.id not in seen and p.id != product.id:
                seen.add(p.id)
                unique_recs.append(p)
        
        return unique_recs[:limit]
    
    def _get_similar_products(self, product: Product, limit: int = 6) -> List[Product]:
        """
        Get products similar to the given product
        """
        query = Q(
            species=product.species,
            is_available=True
        ) & ~Q(id=product.id)
        
        # Match by specific product types
        if product.food_type:
            query &= Q(food_type=product.food_type)
        elif product.toy_type:
            query &= Q(toy_type=product.toy_type)
        elif product.grooming_type:
            query &= Q(grooming_type=product.grooming_type)
        elif product.health_type:
            query &= Q(health_type=product.health_type)
        elif product.category:
            query &= Q(category=product.category)
        
        # Match by age group and size if applicable
        if product.age_group != 'all':
            query &= Q(age_group__in=[product.age_group, 'all'])
        
        if product.size_suitability != 'all':
            query &= Q(size_suitability__in=[product.size_suitability, 'all'])
        
        similar = Product.objects.filter(query).order_by('-rating', '-review_count')[:limit]
        
        return list(similar)
    
    def _get_complementary_products(self, product: Product, limit: int = 6) -> List[Product]:
        """
        Get products that complement the given product
        
        Smart pairing logic:
        - Dry food → Wet food, Treats, Bowls
        - Wet food → Dry food, Treats
        - Toys → More toys, Treats, Interactive items
        - Grooming brush → Shampoo, nail care
        - Food → Feeding accessories
        """
        query = Q(
            species=product.species,
            is_available=True
        ) & ~Q(id=product.id)
        
        complementary_query = Q()
        
        # Food complementary logic
        if product.food_type == 'dry':
            complementary_query = (
                Q(food_type='wet') |  # Suggest wet food
                Q(category__category_type='treats') |  # Suggest treats
                Q(category__name__icontains='bowl') |  # Suggest bowls
                Q(category__name__icontains='feeder')  # Suggest feeders
            )
        
        elif product.food_type == 'wet':
            complementary_query = (
                Q(food_type='dry') |
                Q(category__category_type='treats')
            )
        
        # Toy complementary logic
        elif product.toy_type:
            complementary_query = (
                Q(category__category_type='toys', toy_type__isnull=False) |  # More toys
                Q(category__category_type='treats')  # Treats for play rewards
            )
            # Exclude same toy type to show variety
            query &= ~Q(toy_type=product.toy_type)
        
        # Grooming complementary logic
        elif product.grooming_type == 'brush':
            complementary_query = (
                Q(grooming_type__in=['shampoo', 'dental', 'nail_care']) |
                Q(category__name__icontains='towel')
            )
        
        elif product.grooming_type == 'shampoo':
            complementary_query = Q(grooming_type__in=['brush', 'cologne', 'dental'])
        
        # Health product complementary logic
        elif product.health_type:
            complementary_query = Q(
                health_type__isnull=False
            ) & ~Q(health_type=product.health_type)
        
        # Default: same category different products
        else:
            if product.category:
                complementary_query = Q(category=product.category)
        
        query &= complementary_query
        
        complementary = Product.objects.filter(query).distinct().order_by(
            '-rating', '-review_count'
        )[:limit]
        
        return list(complementary)
    
    def _get_general_recommendations(self, species: Optional[str], limit: int) -> List[Product]:
        """
        Get general recommendations for anonymous users
        """
        query = Q(is_available=True)
        
        if species:
            query &= Q(species=species)
        
        # Prioritize featured, trending, and highly rated
        recommendations = Product.objects.filter(query).order_by(
            '-is_featured',
            '-is_trending',
            '-rating',
            '-review_count'
        )[:limit]
        
        return list(recommendations)
    
    def _get_trending(self, species: Optional[str], limit: int) -> List[Product]:
        """
        Get trending products
        """
        query = Q(is_trending=True, is_available=True)
        
        if species:
            query &= Q(species=species)
        
        trending = Product.objects.filter(query).order_by(
            '-view_count', '-rating'
        )[:limit]
        
        return list(trending)
    
    def get_category_recommendations(
        self,
        category: ProductCategory,
        limit: int = 12,
        exclude_ids: List[int] = None
    ) -> List[Product]:
        """
        Get top recommendations for a specific category
        """
        query = Q(category=category, is_available=True)
        
        if exclude_ids:
            query &= ~Q(id__in=exclude_ids)
        
        recommendations = Product.objects.filter(query).order_by(
            '-rating', '-review_count', '-view_count'
        )[:limit]
        
        return list(recommendations)
    
    def get_brand_recommendations(
        self,
        brand_id: int,
        species: Optional[str] = None,
        limit: int = 12
    ) -> List[Product]:
        """
        Get recommendations for a specific brand
        """
        query = Q(brand_id=brand_id, is_available=True)
        
        if species:
            query &= Q(species=species)
        
        recommendations = Product.objects.filter(query).order_by(
            '-rating', '-review_count'
        )[:limit]
        
        return list(recommendations)


# Helper function for quick access
def get_smart_recommendations(
    user: Optional[User] = None,
    session_id: Optional[str] = None,
    species: Optional[str] = None,
    context_product: Optional[Product] = None,
    limit: int = 12
) -> List[Product]:
    """
    Convenience function to get smart recommendations
    """
    engine = SmartRecommendationEngine(user=user, session_id=session_id)
    return engine.get_recommendations(
        species=species,
        limit=limit,
        context_product=context_product
    )