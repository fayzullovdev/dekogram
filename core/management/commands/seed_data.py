import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Post, Story, Comment, Like, Follow
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with initial users, posts, and stories'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')

        # 1. Create Users
        users_data = [
            {'username': 'admin', 'email': 'admin@dekogram.com', 'full_name': 'Admin User', 'is_staff': True, 'is_superuser': True},
            {'username': 'johndoe', 'email': 'john@example.com', 'full_name': 'John Doe', 'bio': 'Travel Enthusiast 🌍'},
            {'username': 'janedoe', 'email': 'jane@example.com', 'full_name': 'Jane Doe', 'bio': 'Foodie & Nomad 🍝'},
            {'username': 'alexsmith', 'email': 'alex@example.com', 'full_name': 'Alex Smith', 'bio': 'Photography is life 📸'},
            {'username': 'techguru', 'email': 'tech@example.com', 'full_name': 'Tech Guru', 'bio': 'Building the future 🚀'},
        ]

        created_users = []
        for u_data in users_data:
            user, created = User.objects.get_or_create(
                username=u_data['username'],
                defaults={
                    'email': u_data['email'],
                    'full_name': u_data.get('full_name', ''),
                    'bio': u_data.get('bio', ''),
                    'is_staff': u_data.get('is_staff', False),
                    'is_superuser': u_data.get('is_superuser', False),
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            created_users.append(user)

        self.stdout.write(f'Created {len(created_users)} users.')

        # 2. Create Follows
        for user in created_users:
            others = [u for u in created_users if u != user]
            to_follow = random.sample(others, random.randint(1, 3))
            for other in to_follow:
                Follow.objects.get_or_create(follower=user, followed=other)

        self.stdout.write('Created follows.')

        # 3. Create Posts
        captions = [
            "Great day today!", "Exploring the city 🏙️", "Best coffee in town ☕",
            "Working on new projects 💻", "Sunset vibes 🌅", "New photo alert! 📸"
        ]
        
        # Placeholder for media (optional)
        # Since we don't have actual files, we leave them blank or use a default
        
        for user in created_users:
            for _ in range(random.randint(2, 5)):
                Post.objects.create(
                    user=user,
                    caption=random.choice(captions),
                    media_type='image',
                    # media='posts/default.png' # In real life we'd have files
                )

        self.stdout.write('Created posts.')

        # 4. Create Stories
        for user in created_users:
            Story.objects.create(
                user=user,
                media_type='image',
                expires_at=timezone.now() + timedelta(hours=24)
            )

        self.stdout.write('Created stories.')

        self.stdout.write(self.style.SUCCESS('Successfully seeded database!'))
