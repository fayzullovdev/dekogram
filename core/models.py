from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
from PIL import Image
import os


class User(AbstractUser):
    """Custom User model for Dekogram"""
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True, unique=True, db_index=True)
    full_name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png')
    website = models.URLField(max_length=200, blank=True)
    is_private = models.BooleanField(default=False, db_index=True)
    is_verified = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Optimize avatar image
        if self.avatar and hasattr(self.avatar, 'path') and os.path.exists(self.avatar.path):
            img = Image.open(self.avatar.path)
            if img.height > 400 or img.width > 400:
                output_size = (400, 400)
                img.thumbnail(output_size, Image.Resampling.LANCZOS)
                img.save(self.avatar.path, optimize=True, quality=85)
    
    def followers_count(self):
        return self.followers.count()
    
    def following_count(self):
        return self.following.count()
    
    def posts_count(self):
        return self.posts.count()
    
    def __str__(self):
        return self.username


class Follow(models.Model):
    """Follow relationship between users"""
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    followed = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'followed')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.follower.username} follows {self.followed.username}"


class Post(models.Model):
    """Post model for photos and videos"""
    MEDIA_TYPES = (
        ('image', 'Image'),
        ('video', 'Video'),
    )
    
    user = models.ForeignKey(User, related_name='posts', on_delete=models.CASCADE)
    caption = models.TextField(blank=True)
    hashtags = models.CharField(max_length=500, blank=True)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    media = models.FileField(upload_to='posts/')
    location = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if self.media:
            ext = os.path.splitext(self.media.name)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                self.media_type = 'image'
            elif ext in ['.mp4', '.mov', '.avi', '.wmv']:
                self.media_type = 'video'
        super().save(*args, **kwargs)

        
        # Optimize image
        if self.media and hasattr(self.media, 'path') and self.media_type == 'image' and os.path.exists(self.media.path):
            img = Image.open(self.media.path)
            if img.height > 1080 or img.width > 1080:
                output_size = (1080, 1080)
                img.thumbnail(output_size, Image.Resampling.LANCZOS)
                img.save(self.media.path, optimize=True, quality=85)
    
    def likes_count(self):
        return self.likes.count()
    
    def comments_count(self):
        return self.comments.count()
    
    def is_liked_by(self, user):
        return self.likes.filter(user=user).exists()
    
    def is_saved_by(self, user):
        return self.saves.filter(user=user).exists()
    
    def __str__(self):
        return f"Post by {self.user.username} - {self.created_at}"


class Story(models.Model):
    """Story model for temporary 24-hour content"""
    MEDIA_TYPES = (
        ('image', 'Image'),
        ('video', 'Video'),
    )
    
    user = models.ForeignKey(User, related_name='stories', on_delete=models.CASCADE)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    media = models.FileField(upload_to='stories/')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Stories'
    
    def save(self, *args, **kwargs):
        if self.media:
            ext = os.path.splitext(self.media.name)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                self.media_type = 'image'
            elif ext in ['.mp4', '.mov', '.avi', '.wmv']:
                self.media_type = 'video'
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)
        
        # Optimize image
        if self.media and hasattr(self.media, 'path') and self.media_type == 'image' and os.path.exists(self.media.path):
            img = Image.open(self.media.path)
            if img.height > 1080 or img.width > 1080:
                output_size = (1080, 1080)
                img.thumbnail(output_size, Image.Resampling.LANCZOS)
                img.save(self.media.path, optimize=True, quality=85)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"Story by {self.user.username} - {self.created_at}"


class StoryView(models.Model):
    """Tracks users who viewed a story"""
    story = models.ForeignKey(Story, related_name='views', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='stories_viewed', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('story', 'user')

    def __str__(self):
        return f"{self.user.username} viewed {self.story.id}"


class Comment(models.Model):
    """Comment model for posts"""
    user = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.id}"


class Like(models.Model):
    """Like model for posts"""
    user = models.ForeignKey(User, related_name='likes', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='likes', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'post')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} likes {self.post.id}"


class Save(models.Model):
    """Save model for bookmarking posts"""
    user = models.ForeignKey(User, related_name='saved_posts', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='saves', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'post')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} saved {self.post.id}"


class Notification(models.Model):
    """Notification model for user activities"""
    NOTIFICATION_TYPES = (
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('follow', 'Follow'),
        ('mention', 'Mention'),
    )
    
    user = models.ForeignKey(User, related_name='notifications', on_delete=models.CASCADE)
    from_user = models.ForeignKey(User, related_name='sent_notifications', on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    post = models.ForeignKey(Post, null=True, blank=True, on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.user.username} - {self.notification_type}"


class Report(models.Model):
    """Report model for content moderation"""
    REASON_CHOICES = (
        ('spam', 'Spam'),
        ('inappropriate', 'Inappropriate Content'),
        ('harassment', 'Harassment'),
        ('violence', 'Violence'),
        ('hate_speech', 'Hate Speech'),
        ('false_info', 'False Information'),
        ('other', 'Other'),
    )
    
    reporter = models.ForeignKey(User, related_name='reports_made', on_delete=models.CASCADE)
    reported_user = models.ForeignKey(User, null=True, blank=True, related_name='reports_received', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, null=True, blank=True, on_delete=models.CASCADE)
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_reviewed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Report by {self.reporter.username} - {self.reason}"
