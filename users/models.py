from django.contrib.auth.models import AbstractUser
from django.db import models
import os

def avatar_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{instance.username}.{ext}"
    return os.path.join('avatars', str(instance.username), filename)

class CustomUser(AbstractUser): 
    address = models.CharField(max_length=255, blank=True, null=True)
    avatar = models.ImageField(upload_to=avatar_upload_path, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    location = models.TextField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    push_notifications_enabled = models.BooleanField(default=False)

    def __str__(self):
        return self.username or self.email
    
    @property
    def initials(self):
        if self.first_name and self.last_name:
            return f"{self.first_name[0].upper()}{self.last_name[0].upper()}"
        elif self.first_name:
            return self.first_name[0].upper()
        elif self.last_name:
            return self.last_name[0].upper()
        elif self.username:
            return self.username[0].upper()
        else:
            return "U"

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old = CustomUser.objects.get(pk=self.pk)
                if old.avatar and old.avatar != self.avatar:
                    if os.path.isfile(old.avatar.path):
                        os.remove(old.avatar.path)
            except CustomUser.DoesNotExist:
                pass
        super().save(*args, **kwargs)


# --------------------------
# Messaging
# --------------------------
class Message(models.Model):
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"From {self.sender} to {self.receiver}: {self.subject or 'No subject'}"


# --------------------------
# Notifications
# --------------------------
class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} - {self.title}"


 # Push notification preferences
    push_notifications_enabled = models.BooleanField(
        default=False,
        help_text='Enable push notifications for new messages'
    )
    notification_sound_enabled = models.BooleanField(
        default=True,
        help_text='Play sound for new messages'
    )
    
    # Web Push subscription data (for Web Push API if you want to use it later)
    web_push_subscription = models.JSONField(
        blank=True,
        null=True,
        help_text='Web Push API subscription data'
    )
    
    def __str__(self):
        return self.username
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'










