from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Post, Story, Comment, Like, Save, Follow, Notification, Report, StoryView

User = get_user_model()

class UserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'avatar', 'is_verified']

class LikeSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)
    class Meta:
        model = Like
        fields = ['id', 'user', 'created_at']

class CommentSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)
    class Meta:
        model = Comment
        fields = ['id', 'user', 'text', 'created_at']

class PostSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)
    likes_count = serializers.IntegerField(source='likes.count', read_only=True)
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'user', 'caption', 'hashtags', 'media_type', 'media', 
            'location', 'created_at', 'likes_count', 'comments_count', 
            'is_liked', 'is_saved'
        ]
        extra_kwargs = {
            'media_type': {'read_only': True}
        }

    def get_is_liked(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.likes.filter(user=user).exists()
        return False

    def get_is_saved(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.saves.filter(user=user).exists()
        return False

class StorySerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)
    views_count = serializers.IntegerField(source='views.count', read_only=True)
    is_viewed = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = ['id', 'user', 'media_type', 'media', 'created_at', 'expires_at', 'views_count', 'is_viewed']

    def get_is_viewed(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.views.filter(user=user).exists()
        return False

class UserProfileSerializer(serializers.ModelSerializer):
    followers_count = serializers.IntegerField(read_only=True)
    following_count = serializers.IntegerField(read_only=True)
    posts_count = serializers.IntegerField(read_only=True)
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'email', 'bio', 'avatar', 
            'website', 'is_private', 'is_verified', 'followers_count', 
            'following_count', 'posts_count', 'is_following'
        ]

    def get_is_following(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.followers.filter(follower=user).exists()
        return False

class NotificationSerializer(serializers.ModelSerializer):
    from_user = UserShortSerializer(read_only=True)
    class Meta:
        model = Notification
        fields = ['id', 'from_user', 'notification_type', 'post', 'text', 'is_read', 'created_at']

class FollowSerializer(serializers.ModelSerializer):
    follower = UserShortSerializer(read_only=True)
    followed = UserShortSerializer(read_only=True)
    class Meta:
        model = Follow
        fields = ['id', 'follower', 'followed', 'created_at']
