# Dekogram - Instagram Clone

A modern, mobile-first social media platform built with Django, focused on visual content sharing.

## Features

✅ **User Authentication**
- Email/username registration and login
- Secure password hashing
- Session management

✅ **User Profiles**
- Custom avatars
- Bio and website links
- Public/private account options
- Follower/following system

✅ **Posts**
- Photo and video uploads
- Captions and location tagging
- Like, comment, and save functionality
- Infinite scroll feed

✅ **Stories**
- 24-hour temporary content
- Photo and video support
- Auto-expiration

✅ **Social Features**
- Follow/unfollow users
- Real-time notifications
- User search
- Suggested users

✅ **Content Moderation**
- Report posts and users
- Admin review system

✅ **Design**
- Mobile-first responsive design
- Smooth animations and transitions
- Dark mode support
- Modern UI with Dekogram branding

## Tech Stack

- **Backend**: Django 5.2.9
- **Database**: SQLite (development)
- **Frontend**: HTML, CSS, JavaScript
- **Image Processing**: Pillow
- **Icons**: Font Awesome

## Installation

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Run migrations** (already done):
```bash
python manage.py makemigrations
python manage.py migrate
```

3. **Create a superuser**:
```bash
python manage.py createsuperuser
```

4. **Run the development server**:
```bash
python manage.py runserver
```

5. **Access the application**:
- Main site: http://127.0.0.1:8000/
- Admin panel: http://127.0.0.1:8000/admin/

## Project Structure

```
dekogram/
├── core/                      # Main Django app
│   ├── models.py             # Database models
│   ├── views.py              # View functions
│   ├── urls.py               # URL routing
│   ├── admin.py              # Admin configuration
│   └── migrations/           # Database migrations
├── dekogram_project/         # Django project settings
│   ├── settings.py           # Project settings
│   ├── urls.py               # Main URL configuration
│   └── wsgi.py               # WSGI configuration
├── templates/                # HTML templates
│   ├── login.html           # Login page
│   ├── register.html        # Registration page
│   ├── feed.html            # Main feed
│   └── explore.html         # Explore page
├── static/                   # Static files
│   ├── css/
│   │   ├── style.css        # Design system
│   │   └── app.css          # App-specific styles
│   └── js/
│       └── app.js           # JavaScript functionality
├── media/                    # User uploads
│   ├── avatars/             # User avatars
│   ├── posts/               # Post media
│   └── stories/             # Story media
├── manage.py                # Django management script
└── requirements.txt         # Python dependencies
```

## Usage

### Creating an Account

1. Navigate to http://127.0.0.1:8000/register/
2. Fill in your details (email, full name, username, password)
3. Click "Sign Up"
4. You'll be automatically logged in and redirected to the feed

### Creating Posts

1. Click the "+" icon in the header
2. Select a photo or video
3. Add a caption and location (optional)
4. Click "Share"

### Creating Stories

1. Click on "Your Story" in the stories bar
2. Select a photo or video
3. Story will be automatically uploaded and expire after 24 hours

### Following Users

1. Search for users using the search bar
2. Click on suggested users in the sidebar
3. Click "Follow" to follow them
4. Their posts will appear in your feed

### Admin Panel

Access the admin panel at http://127.0.0.1:8000/admin/ to:
- Manage users
- Moderate content
- Review reports
- View statistics

## API Endpoints

### Authentication
- `POST /login/` - User login
- `POST /register/` - User registration
- `GET /logout/` - User logout

### Posts
- `GET /api/posts/` - Get feed posts
- `GET /api/posts/explore/` - Get explore posts
- `POST /api/posts/create/` - Create a post
- `POST /api/posts/<id>/like/` - Like/unlike a post
- `POST /api/posts/<id>/save/` - Save/unsave a post
- `GET /api/posts/<id>/comments/` - Get post comments
- `POST /api/posts/<id>/comments/` - Add a comment

### Stories
- `GET /api/stories/` - Get active stories
- `POST /api/stories/create/` - Create a story

### Users
- `GET /api/users/<username>/` - Get user profile
- `POST /api/users/<id>/follow/` - Follow/unfollow user
- `POST /api/profile/update/` - Update profile

### Notifications
- `GET /api/notifications/` - Get notifications
- `POST /api/notifications/mark-read/` - Mark notifications as read

### Search
- `GET /api/search/?q=<query>` - Search users

### Reports
- `POST /api/report/` - Report content

## Development

### Running Tests
```bash
python manage.py test
```

### Creating Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Collecting Static Files (for production)
```bash
python manage.py collectstatic
```

## Production Deployment

For production deployment:

1. Update `settings.py`:
   - Set `DEBUG = False`
   - Update `ALLOWED_HOSTS`
   - Configure a production database (PostgreSQL recommended)
   - Set up proper `SECRET_KEY`

2. Use a production server (Gunicorn, uWSGI)
3. Set up a reverse proxy (Nginx, Apache)
4. Configure media file serving
5. Enable HTTPS

## Contributing

This is a demonstration project. Feel free to fork and customize for your needs.

## License

This project is for educational purposes.

## Credits

Built with ❤️ using Django and modern web technologies.

---

**Dekogram** - Share your moments with the world! 🚀
