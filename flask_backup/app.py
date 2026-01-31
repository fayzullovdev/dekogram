import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image
import secrets
import json

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dekogram.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'mov', 'avi'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100))
    bio = db.Column(db.String(500))
    avatar = db.Column(db.String(200), default='default-avatar.png')
    website = db.Column(db.String(200))
    is_private = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    posts = db.relationship('Post', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    stories = db.relationship('Story', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'bio': self.bio,
            'avatar': self.avatar,
            'website': self.website,
            'is_private': self.is_private,
            'is_verified': self.is_verified,
            'followers_count': Follow.query.filter_by(followed_id=self.id).count(),
            'following_count': Follow.query.filter_by(follower_id=self.id).count(),
            'posts_count': self.posts.count()
        }

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    caption = db.Column(db.Text)
    media_type = db.Column(db.String(20))  # 'image' or 'video'
    media_url = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    saves = db.relationship('Save', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self, current_user_id=None):
        data = {
            'id': self.id,
            'user': self.author.to_dict(),
            'caption': self.caption,
            'media_type': self.media_type,
            'media_url': self.media_url,
            'location': self.location,
            'created_at': self.created_at.isoformat(),
            'likes_count': self.likes.count(),
            'comments_count': self.comments.count(),
            'is_liked': False,
            'is_saved': False
        }
        
        if current_user_id:
            data['is_liked'] = Like.query.filter_by(user_id=current_user_id, post_id=self.id).first() is not None
            data['is_saved'] = Save.query.filter_by(user_id=current_user_id, post_id=self.id).first() is not None
        
        return data

class Story(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    media_type = db.Column(db.String(20))
    media_url = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user': self.author.to_dict(),
            'media_type': self.media_type,
            'media_url': self.media_url,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat()
        }

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user': self.author.to_dict(),
            'text': self.text,
            'created_at': self.created_at.isoformat()
        }

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='unique_like'),)

class Save(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='unique_save'),)

class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    follower = db.relationship('User', foreign_keys=[follower_id], backref='following')
    followed = db.relationship('User', foreign_keys=[followed_id], backref='followers')
    
    __table_args__ = (db.UniqueConstraint('follower_id', 'followed_id', name='unique_follow'),)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50))  # 'like', 'comment', 'follow', 'mention'
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    text = db.Column(db.String(200))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    from_user = db.relationship('User', foreign_keys=[from_user_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'from_user': self.from_user.to_dict() if self.from_user else None,
            'post_id': self.post_id,
            'text': self.text,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat()
        }

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reported_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    reason = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    reporter = db.relationship('User', foreign_keys=[reporter_id])
    reported_user = db.relationship('User', foreign_keys=[reported_user_id])

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Helper functions
def optimize_image(image_path, max_size=(1080, 1080)):
    """Optimize uploaded images"""
    try:
        img = Image.open(image_path)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        img.save(image_path, optimize=True, quality=85)
    except Exception as e:
        print(f"Error optimizing image: {e}")

def create_notification(user_id, notification_type, from_user_id, post_id=None, text=None):
    """Create a notification and emit via SocketIO"""
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        from_user_id=from_user_id,
        post_id=post_id,
        text=text
    )
    db.session.add(notification)
    db.session.commit()
    
    # Emit real-time notification
    socketio.emit('new_notification', notification.to_dict(), room=f'user_{user_id}')
    
    return notification

# Routes - Authentication
@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('feed.html')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        
        # Validate input
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            full_name=data.get('full_name', '')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return jsonify({'success': True, 'user': user.to_dict()})
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        user = User.query.filter_by(username=data['username']).first()
        
        if user and user.check_password(data['password']):
            login_user(user, remember=data.get('remember', False))
            return jsonify({'success': True, 'user': user.to_dict()})
        
        return jsonify({'error': 'Invalid username or password'}), 401
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Routes - Posts
@app.route('/api/posts', methods=['GET'])
@login_required
def get_posts():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get posts from followed users and own posts
    following_ids = [f.followed_id for f in Follow.query.filter_by(follower_id=current_user.id).all()]
    following_ids.append(current_user.id)
    
    posts = Post.query.filter(Post.user_id.in_(following_ids))\
        .order_by(Post.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'posts': [post.to_dict(current_user.id) for post in posts.items],
        'has_more': posts.has_next
    })

@app.route('/api/posts/explore', methods=['GET'])
@login_required
def explore_posts():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    posts = Post.query.order_by(Post.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'posts': [post.to_dict(current_user.id) for post in posts.items],
        'has_more': posts.has_next
    })

@app.route('/api/posts/create', methods=['POST'])
@login_required
def create_post():
    if 'media' not in request.files:
        return jsonify({'error': 'No media file provided'}), 400
    
    file = request.files['media']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file'}), 400
    
    # Save file
    filename = secure_filename(f"{secrets.token_hex(16)}_{file.filename}")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'posts', filename)
    file.save(filepath)
    
    # Determine media type
    media_type = 'video' if filename.lower().endswith(('.mp4', '.mov', '.avi')) else 'image'
    
    # Optimize image
    if media_type == 'image':
        optimize_image(filepath)
    
    # Create post
    post = Post(
        user_id=current_user.id,
        caption=request.form.get('caption', ''),
        media_type=media_type,
        media_url=f'/static/uploads/posts/{filename}',
        location=request.form.get('location', '')
    )
    
    db.session.add(post)
    db.session.commit()
    
    return jsonify({'success': True, 'post': post.to_dict(current_user.id)})

@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    existing_like = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    
    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
        return jsonify({'success': True, 'liked': False, 'likes_count': post.likes.count()})
    
    like = Like(user_id=current_user.id, post_id=post_id)
    db.session.add(like)
    db.session.commit()
    
    # Create notification
    if post.user_id != current_user.id:
        create_notification(
            user_id=post.user_id,
            notification_type='like',
            from_user_id=current_user.id,
            post_id=post_id,
            text=f'{current_user.username} liked your post'
        )
    
    return jsonify({'success': True, 'liked': True, 'likes_count': post.likes.count()})

@app.route('/api/posts/<int:post_id>/save', methods=['POST'])
@login_required
def save_post(post_id):
    post = Post.query.get_or_404(post_id)
    existing_save = Save.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    
    if existing_save:
        db.session.delete(existing_save)
        db.session.commit()
        return jsonify({'success': True, 'saved': False})
    
    save = Save(user_id=current_user.id, post_id=post_id)
    db.session.add(save)
    db.session.commit()
    
    return jsonify({'success': True, 'saved': True})

@app.route('/api/posts/<int:post_id>/comments', methods=['GET', 'POST'])
@login_required
def post_comments(post_id):
    post = Post.query.get_or_404(post_id)
    
    if request.method == 'POST':
        data = request.get_json()
        comment = Comment(
            user_id=current_user.id,
            post_id=post_id,
            text=data['text']
        )
        db.session.add(comment)
        db.session.commit()
        
        # Create notification
        if post.user_id != current_user.id:
            create_notification(
                user_id=post.user_id,
                notification_type='comment',
                from_user_id=current_user.id,
                post_id=post_id,
                text=f'{current_user.username} commented on your post'
            )
        
        return jsonify({'success': True, 'comment': comment.to_dict()})
    
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at.desc()).all()
    return jsonify({'comments': [c.to_dict() for c in comments]})

# Routes - Stories
@app.route('/api/stories', methods=['GET'])
@login_required
def get_stories():
    # Get stories from followed users
    following_ids = [f.followed_id for f in Follow.query.filter_by(follower_id=current_user.id).all()]
    following_ids.append(current_user.id)
    
    # Get active stories (not expired)
    stories = Story.query.filter(
        Story.user_id.in_(following_ids),
        Story.expires_at > datetime.utcnow()
    ).order_by(Story.created_at.desc()).all()
    
    # Group by user
    stories_by_user = {}
    for story in stories:
        if story.user_id not in stories_by_user:
            stories_by_user[story.user_id] = {
                'user': story.author.to_dict(),
                'stories': []
            }
        stories_by_user[story.user_id]['stories'].append(story.to_dict())
    
    return jsonify({'stories': list(stories_by_user.values())})

@app.route('/api/stories/create', methods=['POST'])
@login_required
def create_story():
    if 'media' not in request.files:
        return jsonify({'error': 'No media file provided'}), 400
    
    file = request.files['media']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file'}), 400
    
    # Save file
    filename = secure_filename(f"{secrets.token_hex(16)}_{file.filename}")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'stories', filename)
    file.save(filepath)
    
    # Determine media type
    media_type = 'video' if filename.lower().endswith(('.mp4', '.mov', '.avi')) else 'image'
    
    # Optimize image
    if media_type == 'image':
        optimize_image(filepath)
    
    # Create story
    story = Story(
        user_id=current_user.id,
        media_type=media_type,
        media_url=f'/static/uploads/stories/{filename}'
    )
    
    db.session.add(story)
    db.session.commit()
    
    return jsonify({'success': True, 'story': story.to_dict()})

# Routes - Users & Profile
@app.route('/api/users/<username>')
@login_required
def get_user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    is_following = Follow.query.filter_by(follower_id=current_user.id, followed_id=user.id).first() is not None
    
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
    
    return jsonify({
        'user': user.to_dict(),
        'is_following': is_following,
        'posts': [post.to_dict(current_user.id) for post in posts]
    })

@app.route('/api/users/<int:user_id>/follow', methods=['POST'])
@login_required
def follow_user(user_id):
    if user_id == current_user.id:
        return jsonify({'error': 'Cannot follow yourself'}), 400
    
    user = User.query.get_or_404(user_id)
    existing_follow = Follow.query.filter_by(follower_id=current_user.id, followed_id=user_id).first()
    
    if existing_follow:
        db.session.delete(existing_follow)
        db.session.commit()
        return jsonify({'success': True, 'following': False})
    
    follow = Follow(follower_id=current_user.id, followed_id=user_id)
    db.session.add(follow)
    db.session.commit()
    
    # Create notification
    create_notification(
        user_id=user_id,
        notification_type='follow',
        from_user_id=current_user.id,
        text=f'{current_user.username} started following you'
    )
    
    return jsonify({'success': True, 'following': True})

@app.route('/api/profile/update', methods=['POST'])
@login_required
def update_profile():
    data = request.form
    
    if 'avatar' in request.files:
        file = request.files['avatar']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{current_user.id}_{secrets.token_hex(8)}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'avatars', filename)
            file.save(filepath)
            optimize_image(filepath, max_size=(400, 400))
            current_user.avatar = f'/static/uploads/avatars/{filename}'
    
    if 'full_name' in data:
        current_user.full_name = data['full_name']
    if 'bio' in data:
        current_user.bio = data['bio']
    if 'website' in data:
        current_user.website = data['website']
    if 'is_private' in data:
        current_user.is_private = data['is_private'] == 'true'
    
    db.session.commit()
    
    return jsonify({'success': True, 'user': current_user.to_dict()})

# Routes - Notifications
@app.route('/api/notifications')
@login_required
def get_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc())\
        .limit(50).all()
    
    return jsonify({'notifications': [n.to_dict() for n in notifications]})

@app.route('/api/notifications/mark-read', methods=['POST'])
@login_required
def mark_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False)\
        .update({'is_read': True})
    db.session.commit()
    
    return jsonify({'success': True})

# Routes - Search
@app.route('/api/search')
@login_required
def search():
    query = request.args.get('q', '')
    
    users = User.query.filter(
        (User.username.ilike(f'%{query}%')) | 
        (User.full_name.ilike(f'%{query}%'))
    ).limit(20).all()
    
    return jsonify({'users': [u.to_dict() for u in users]})

# Routes - Reports
@app.route('/api/report', methods=['POST'])
@login_required
def create_report():
    data = request.get_json()
    
    report = Report(
        reporter_id=current_user.id,
        reported_user_id=data.get('user_id'),
        post_id=data.get('post_id'),
        reason=data['reason'],
        description=data.get('description', '')
    )
    
    db.session.add(report)
    db.session.commit()
    
    return jsonify({'success': True})

# SocketIO events
@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        join_room(f'user_{current_user.id}')
        emit('connected', {'user_id': current_user.id})

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        leave_room(f'user_{current_user.id}')

# Initialize database
with app.app_context():
    db.create_all()
    
    # Create default avatar if it doesn't exist
    default_avatar_path = os.path.join('static', 'images', 'default-avatar.png')
    if not os.path.exists(default_avatar_path):
        os.makedirs(os.path.dirname(default_avatar_path), exist_ok=True)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
