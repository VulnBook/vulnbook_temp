# from .db import db
# from datetime import datetime

# # Association table for post likes
# post_likes = db.Table('post_likes',
#     db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
#     db.Column('post_id', db.Integer, db.ForeignKey('post.id'))
# )

# # Association table for comment likes
# comment_likes = db.Table('comment_likes',
#     db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
#     db.Column('comment_id', db.Integer, db.ForeignKey('comment.id'))
# )

# class User(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(80), unique=True, nullable=False)
#     firstname = db.Column(db.String(80), nullable=False)
#     lastname = db.Column(db.String(80), nullable=False)
#     dob = db.Column(db.Date, nullable=False)
#     password = db.Column(db.String(128), nullable=False)  # Store plain-text password (insecure)
#     bio = db.Column(db.Text, nullable=True)
#     image_url = db.Column(db.String(255), nullable=True)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)

# class Post(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     content = db.Column(db.Text, nullable=False)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     user = db.relationship('User', backref='posts')
#     images = db.relationship('PostMedia', backref='post', lazy=True)
#     likes = db.relationship('User', secondary=post_likes, backref='liked_posts')
#     reports = db.relationship('PostReport', backref='post', lazy=True)

# class PostMedia(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
#     media_url = db.Column(db.String(255), nullable=False)
#     media_type = db.Column(db.String(10), nullable=False)  # 'image' or 'video'

# class PostReport(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
#     reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     resolved = db.Column(db.Boolean, default=False)

# class Comment(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     content = db.Column(db.Text, nullable=False)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     post = db.relationship('Post', backref='comments')
#     user = db.relationship('User', backref='comments')
#     likes = db.relationship('User', secondary=comment_likes, backref='liked_comments')
#     reports = db.relationship('CommentReport', backref='comment', lazy=True)

# class CommentReport(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=False)
#     reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     resolved = db.Column(db.Boolean, default=False)
from .db import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    firstname = db.Column(db.String(80), nullable=False)
    lastname = db.Column(db.String(80), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    password = db.Column(db.String(128), nullable=False)  # Store plain-text password (insecure)
    bio = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship('Post', backref='user')
    comments = db.relationship('Comment', backref='user')
    post_likes = db.relationship('PostLike', backref='user')
    comment_likes = db.relationship('CommentLike', backref='user')
    reports = db.relationship('Report', backref='user')
    friend_requests_sent = db.relationship('FriendRequest', foreign_keys='FriendRequest.from_user_id', backref='sender')
    friend_requests_received = db.relationship('FriendRequest', foreign_keys='FriendRequest.to_user_id', backref='receiver')
    notifications = db.relationship('Notification', backref='user')
    friendships = db.relationship('Friendship', foreign_keys='Friendship.user_id', backref='user_friend')
    marketplace_items = db.relationship('MarketplaceItem', backref='user')

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    comments = db.relationship('Comment', backref='post')
    images = db.relationship('PostImage', backref='post')
    likes = db.relationship('PostLike', backref='post')
    reports = db.relationship('Report', backref='post', primaryjoin="and_(Post.id==Report.post_id)")

class PostImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)  # 'image' or 'video'

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    likes = db.relationship('CommentLike', backref='comment')
    reports = db.relationship('Report', backref='comment', primaryjoin="and_(Comment.id==Report.comment_id)")

class PostLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='unique_post_like'),)

class CommentLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'comment_id', name='unique_comment_like'),)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    reason = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'friend_id', name='unique_friendship'),)

class MarketplaceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)  # No validation, vulnerable
    price = db.Column(db.String(32), nullable=False)  # Stored as string for easy injection
    description = db.Column(db.Text, nullable=False)
    review = db.Column(db.Text, nullable=True)
    approved = db.Column(db.Boolean, default=False)  # Only approved items are shown
    created_at = db.Column(db.DateTime, default=datetime.utcnow)