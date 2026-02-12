# breeding/models.py
from django.db import models
from django.conf import settings
from pets.models import Pet

class BreedingSwipe(models.Model):
    """Track swipes (likes/passes) for breeding matchmaking"""
    ACTION_CHOICES = [
        ('like', 'Like'),
        ('pass', 'Pass'),
    ]
    
    user_pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='swipes_made')
    target_pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='swipes_received')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'breeding_swipes'
        unique_together = ('user_pet', 'target_pet')
        indexes = [
            models.Index(fields=['user_pet', 'action']),
            models.Index(fields=['target_pet', 'action']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user_pet.name} {self.action}d {self.target_pet.name}"


class BreedingMatch(models.Model):
    """Store breeding matches when both pets like each other"""
    pet1 = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='matches_as_pet1')
    pet2 = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='matches_as_pet2')
    created_at = models.DateTimeField(auto_now_add=True)
    chat_unlocked = models.BooleanField(default=True)  # Auto-unlock on match
    
    class Meta:
        db_table = 'breeding_matches'
        unique_together = ('pet1', 'pet2')
        indexes = [
            models.Index(fields=['pet1', 'pet2']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Match: {self.pet1.name} & {self.pet2.name}"
    
    def get_other_pet(self, pet):
        """Get the other pet in the match"""
        return self.pet2 if self.pet1 == pet else self.pet1


class BreedingChatMessage(models.Model):
    """Chat messages between matched pet owners"""
    match = models.ForeignKey(BreedingMatch, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'breeding_chat_messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['match', 'created_at']),
            models.Index(fields=['sender', 'read']),
        ]
    
    def __str__(self):
        return f"{self.sender.username}: {self.message[:50]}"
    