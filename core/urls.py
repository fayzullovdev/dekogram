from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views, urls_password

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'posts', views.PostViewSet, basename='post')
router.register(r'stories', views.StoryViewSet, basename='story')
router.register(r'notifications', views.NotificationViewSet, basename='notification')

urlpatterns = [
    # Template Views
    path('', views.feed_view, name='feed'),
    path('explore/', views.explore_view, name='explore'),
    path('search/', views.search_view, name='search'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # API Endpoints
    path('api/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Password Reset
    path('password-reset/', views.password_reset_simple_view, name='password_reset'),
]
