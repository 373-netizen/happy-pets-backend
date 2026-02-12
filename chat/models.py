from django.db import models

class ChatMessage(models.Model):
    user = models.CharField(max_length=100)  # Username from frontend
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user_id = models.IntegerField(null=True, blank=True)  # Optional link to User model
    file_url = models.URLField(max_length=500, blank=True, null=True)
    file_type = models.CharField(max_length=20, blank=True, null=True)  # 'image' or 'video'

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user}: {self.message[:50]}"

    def to_dict(self):
        return {
            'id': self.id,
            'user': self.user,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'file_url': self.file_url,
            'file_type': self.file_type
            
        }


class OnlineUser(models.Model):
    username = models.CharField(max_length=100)  # removed unique constraint
    channel_name = models.CharField(max_length=100, unique=True)  # unique per connection
    connected_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username
