from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Post, Story, Comment, Like, Save, Follow, Notification, Report


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'full_name', 'is_verified', 'is_private', 'created_at')
    list_filter = ('is_verified', 'is_private', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'full_name')
    ordering = ('-created_at',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Dekogram Profile', {
            'fields': ('full_name', 'bio', 'avatar', 'website', 'phone', 'is_private', 'is_verified')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Dekogram Profile', {
            'fields': ('email', 'full_name')
        }),
    )


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'media_type', 'location', 'created_at', 'likes_count', 'comments_count')
    list_filter = ('media_type', 'created_at')
    search_fields = ('user__username', 'caption', 'location')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    def likes_count(self, obj):
        return obj.likes.count()
    likes_count.short_description = 'Likes'
    
    def comments_count(self, obj):
        return obj.comments.count()
    comments_count.short_description = 'Comments'


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'media_type', 'created_at', 'expires_at', 'is_expired')
    list_filter = ('media_type', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post', 'text_preview', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'text')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Comment'


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(Save)
class SaveAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'follower', 'followed', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('follower__username', 'followed__username')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'from_user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'from_user__username', 'text')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'reporter', 'reported_user', 'reason', 'is_reviewed', 'created_at')
    list_filter = ('reason', 'is_reviewed', 'created_at')
    search_fields = ('reporter__username', 'reported_user__username', 'description')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    actions = ['mark_as_reviewed']
    
    def mark_as_reviewed(self, request, queryset):
        queryset.update(is_reviewed=True)
    mark_as_reviewed.short_description = 'Mark selected reports as reviewed'
