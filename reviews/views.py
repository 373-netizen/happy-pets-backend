# reviews/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.db.models import F

from .models import Review, ReviewHelpful
from .serializers import ReviewSerializer, ReviewCreateSerializer, ReviewUpdateSerializer
from products.models import Product


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for product reviews
    """
    queryset = Review.objects.filter(is_approved=True).select_related('user', 'product')
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ReviewCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ReviewUpdateSerializer
        return ReviewSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by product
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        # Filter by user
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by rating
        rating = self.request.query_params.get('rating')
        if rating:
            queryset = queryset.filter(rating=rating)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Create a review and update product rating"""
        review = serializer.save()
        return review
    
    def perform_update(self, serializer):
        """Update review and recalculate product rating"""
        review = serializer.save()
        review.update_product_rating()
        return review
    
    def perform_destroy(self, instance):
        """Delete review and update product rating"""
        product = instance.product
        instance.delete()
        
        # Recalculate product rating
        from django.db.models import Avg, Count
        stats = Review.objects.filter(
            product=product,
            is_approved=True
        ).aggregate(
            avg_rating=Avg('rating'),
            count=Count('id')
        )
        product.rating = round(stats['avg_rating'] or 0, 2)
        product.review_count = stats['count']
        product.save(update_fields=['rating', 'review_count'])
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def mark_helpful(self, request, pk=None):
        """Mark a review as helpful"""
        review = self.get_object()
        
        helpful, created = ReviewHelpful.objects.get_or_create(
            review=review,
            user=request.user
        )
        
        if created:
            # Increment helpful count
            review.helpful_count = F('helpful_count') + 1
            review.save(update_fields=['helpful_count'])
            
            return Response({
                'message': 'Review marked as helpful',
                'is_helpful': True
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'message': 'Already marked as helpful',
                'is_helpful': True
            })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unmark_helpful(self, request, pk=None):
        """Remove helpful mark from review"""
        review = self.get_object()
        
        deleted_count, _ = ReviewHelpful.objects.filter(
            review=review,
            user=request.user
        ).delete()
        
        if deleted_count:
            # Decrement helpful count
            review.helpful_count = F('helpful_count') - 1
            review.save(update_fields=['helpful_count'])
        
        return Response({
            'message': 'Helpful mark removed',
            'is_helpful': False
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_reviews(self, request):
        """Get current user's reviews"""
        reviews = self.get_queryset().filter(user=request.user)
        
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def product_stats(self, request):
        """Get review statistics for a product"""
        product_id = request.query_params.get('product')
        if not product_id:
            return Response(
                {'error': 'product parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        from django.db.models import Count
        
        # Rating breakdown
        rating_breakdown = Review.objects.filter(
            product=product,
            is_approved=True
        ).values('rating').annotate(count=Count('rating')).order_by('-rating')
        
        breakdown_dict = {str(i): 0 for i in range(1, 6)}
        total_reviews = 0
        
        for item in rating_breakdown:
            breakdown_dict[str(item['rating'])] = item['count']
            total_reviews += item['count']
        
        # Calculate percentages
        for rating in breakdown_dict:
            count = breakdown_dict[rating]
            breakdown_dict[rating] = {
                'count': count,
                'percentage': round((count / total_reviews) * 100, 1) if total_reviews > 0 else 0
            }
        
        stats = {
            'product_id': product.id,
            'product_name': product.name,
            'average_rating': float(product.rating),
            'total_reviews': product.review_count,
            'rating_breakdown': breakdown_dict,
            'verified_purchase_count': Review.objects.filter(
                product=product,
                is_verified_purchase=True,
                is_approved=True
            ).count()
        }
        
        return Response(stats)