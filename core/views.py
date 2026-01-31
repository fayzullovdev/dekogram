from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
import json
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.utils import timezone
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django_filters.rest_framework import DjangoFilterBackend

from .models import User, Post, Story, Comment, Like, Save, Follow, Notification, Report, StoryView
from .serializers import (
    UserShortSerializer, PostSerializer, StorySerializer, 
    CommentSerializer, UserProfileSerializer, NotificationSerializer
)

# Template Views (For the main shell)
@login_required
def feed_view(request):
    return render(request, 'feed.html')

@login_required
def explore_view(request):
    return render(request, 'explore.html')

@login_required
def search_view(request):
    query = request.GET.get('q', '')
    return render(request, 'search.html', {'query': query})

def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    is_following = False
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(follower=request.user, followed=profile_user).exists()
    
    posts = profile_user.posts.all().order_by('-created_at')
    
    context = {
        'user_profile': profile_user,
        'posts': posts,
        'posts_count': posts.count(),
        'is_following': is_following,
    }
    return render(request, 'profile.html', context)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('feed')
        
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                refresh = RefreshToken.for_user(user)
                return JsonResponse({
                    'status': 'success',
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                })
            else:
                return JsonResponse({'error': 'Invalid username or password'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
            
    return render(request, 'login.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('feed')
        
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            full_name = data.get('full_name', '')
            
            if User.objects.filter(username=username).exists():
                return JsonResponse({'error': 'Username already exists'}, status=400)
            if User.objects.filter(email=email).exists():
                return JsonResponse({'error': 'Email already exists'}, status=400)
                
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                full_name=full_name
            )
            login(request, user)
            refresh = RefreshToken.for_user(user)
            return JsonResponse({
                'status': 'success',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
            
    return render(request, 'register.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def password_reset_simple_view(request):
    if request.user.is_authenticated:
        return redirect('feed')
        
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            identity = data.get('identity')
            new_password = data.get('password')
            
            try:
                user = User.objects.get(Q(username=identity) | Q(email=identity))
                user.set_password(new_password)
                user.save()
                return JsonResponse({'status': 'success'})
            except User.DoesNotExist:
                return JsonResponse({'error': 'No account found with that username or email.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
            
    return render(request, 'password_reset_simple.html')

# API ViewSets
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    lookup_field = 'username'

    def get_queryset(self):
        return User.objects.annotate(
            followers_count=Count('followers', distinct=True),
            following_count=Count('following', distinct=True),
            posts_count=Count('posts', distinct=True)
        )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def follow(self, request, username=None):
        user_to_follow = self.get_object()
        if user_to_follow == request.user:
            return Response({'error': 'You cannot follow yourself'}, status=status.HTTP_400_BAD_REQUEST)
        
        follow, created = Follow.objects.get_or_create(follower=request.user, followed=user_to_follow)
        
        if not created:
            follow.delete()
            return Response({'status': 'unfollowed'})
        
        # Create notification
        Notification.objects.create(
            user=user_to_follow,
            from_user=request.user,
            notification_type='follow',
            text=f'{request.user.username} started following you'
        )
        return Response({'status': 'followed'})

    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        users = User.objects.filter(
            Q(username__icontains=query) | Q(full_name__icontains=query)
        ).exclude(id=request.user.id)[:20]
        serializer = UserShortSerializer(users, many=True)
        return Response(serializer.data)

class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        query_type = self.request.query_params.get('type', 'feed')
        
        if query_type == 'explore':
            # Trending/Explore: show all users' videos as requested
            return Post.objects.select_related('user').prefetch_related('likes', 'comments').filter(media_type='video').order_by('-created_at')
        
        # Default Feed: followed users + own posts
        following_ids = self.request.user.following.values_list('followed_id', flat=True)
        return Post.objects.select_related('user').prefetch_related('likes', 'comments').filter(
            Q(user_id__in=following_ids) | Q(user=self.request.user)
        ).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        post = self.get_object()
        like, created = Like.objects.get_or_create(user=request.user, post=post)
        
        if not created:
            like.delete()
            return Response({'status': 'unliked', 'likes_count': post.likes.count()})
        
        # Notify
        if post.user != request.user:
            Notification.objects.create(
                user=post.user,
                from_user=request.user,
                notification_type='like',
                post=post,
                text=f'{request.user.username} liked your post'
            )
        return Response({'status': 'liked', 'likes_count': post.likes.count()})

    @action(detail=True, methods=['post'])
    def save_post(self, request, pk=None):
        post = self.get_object()
        save, created = Save.objects.get_or_create(user=request.user, post=post)
        if not created:
            save.delete()
            return Response({'status': 'unsaved'})
        return Response({'status': 'saved'})

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        post = self.get_object()
        if request.method == 'POST':
            text = request.data.get('text')
            comment = Comment.objects.create(user=request.user, post=post, text=text)
            # Notify
            if post.user != request.user:
                Notification.objects.create(
                    user=post.user,
                    from_user=request.user,
                    notification_type='comment',
                    post=post,
                    text=f'{request.user.username} commented: {text[:20]}...'
                )
            serializer = CommentSerializer(comment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        comments = post.comments.all()
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

class StoryViewSet(viewsets.ModelViewSet):
    serializer_class = StorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Active stories from followed users + own
        following_ids = list(self.request.user.following.values_list('followed_id', flat=True)) + [self.request.user.id]
        return Story.objects.filter(
            user_id__in=following_ids,
            expires_at__gt=timezone.now()
        ).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def view(self, request, pk=None):
        story = self.get_object()
        StoryView.objects.get_or_create(story=story, user=request.user)
        return Response({'status': 'viewed'})

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.notifications.all().order_by('-created_at')

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        request.user.notifications.filter(is_read=False).update(is_read=True)
        return Response({'status': 'read'})
