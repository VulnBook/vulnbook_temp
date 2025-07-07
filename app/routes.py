from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, send_from_directory
from flask_paginate import Pagination, get_page_args
from .models import User, Post, Comment, PostImage, PostLike, CommentLike, Report, FriendRequest, Notification, Friendship
from .db import db
import jwt
from jwt.exceptions import PyJWTError
import datetime
import os
import uuid
import re

bp = Blueprint('main', __name__)

# VULNERABLE: Weak JWT secret and no algorithm validation
JWT_SECRET = 'weak-jwt-secret'

def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def extract_hashtags(text):
    return re.findall(r'#\w+', text)

@bp.route('/')
def index():
    if 'token' not in session:
        return redirect(url_for('main.login'))
    try:
        decoded = jwt.decode(session['token'], JWT_SECRET, algorithms=['HS256'])
        user = User.query.get(decoded['user_id'])
        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
        per_page = 10
        total = Post.query.count()
        posts = Post.query.order_by(Post.created_at.desc()).offset(offset).limit(per_page).all()
        pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap5')
        return render_template('home.html', user=user, posts=posts, pagination=pagination)
    except PyJWTError:
        return redirect(url_for('main.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        dob = request.form['dob']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        user = User(
            username=username,
            firstname=firstname,
            lastname=lastname,
            dob=dob,
            password=password  # VULNERABLE: Plain-text password
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()  # VULNERABLE: Plain-text password check
        if user:
            session['token'] = generate_token(user.id)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('main.index'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@bp.route('/post', methods=['POST'])
def create_post():
    if 'token' not in session:
        return redirect(url_for('main.login'))
    decoded = jwt.decode(session['token'], JWT_SECRET, algorithms=['HS256'])
    content = request.form['content']  # VULNERABLE: No sanitization (XSS)
    post = Post(user_id=decoded['user_id'], content=content)
    db.session.add(post)
    db.session.commit()
    # Handle hashtags (store as plain text in a new field or table if needed)
    hashtags = extract_hashtags(content)
    if hasattr(post, 'hashtags'):
        post.hashtags = ','.join(hashtags)
        db.session.commit()
    # Handle file uploads
    files = request.files.getlist('files')
    for file in files:
        if file and allowed_file(file.filename):
            filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            file_type = 'image' if file.mimetype.startswith('image') else 'video'
            post_image = PostImage(post_id=post.id, file_path=f'static/uploads/{filename}', file_type=file_type)
            db.session.add(post_image)
    db.session.commit()
    flash('Post created successfully!', 'success')
    return redirect(url_for('main.index'))

@bp.route('/post/<int:post_id>', methods=['GET', 'POST'])
def single_post(post_id):
    if 'token' not in session:
        return redirect(url_for('main.login'))
    try:
        decoded = jwt.decode(session['token'], JWT_SECRET, algorithms=['HS256'])
        user = User.query.get(decoded['user_id'])
        post = Post.query.get_or_404(post_id)
        page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
        per_page = 5
        total = Comment.query.filter_by(post_id=post_id).count()
        comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at.asc()).offset(offset).limit(per_page).all()
        pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap5')
        if request.method == 'POST':
            content = request.form['content']  # VULNERABLE: No sanitization (XSS)
            comment = Comment(post_id=post_id, user_id=decoded['user_id'], content=content)
            db.session.add(comment)
            db.session.commit()
            flash('Comment added successfully!', 'success')
            return redirect(url_for('main.single_post', post_id=post_id))
        return render_template('post.html', user=user, post=post, comments=comments, pagination=pagination)
    except jwt.InvalidTokenError:
        return redirect(url_for('main.login'))

@bp.route('/post/<int:post_id>/edit', methods=['POST'])
def edit_post(post_id):
    if 'token' not in session:
        return redirect(url_for('main.login'))
    decoded = jwt.decode(session['token'], JWT_SECRET, algorithms=['HS256'])
    post = Post.query.get_or_404(post_id)
    if post.user_id != decoded['user_id']:
        flash('Unauthorized action', 'danger')
        return redirect(url_for('main.single_post', post_id=post_id))
    post.content = request.form['content']  # VULNERABLE: No sanitization (XSS)
    db.session.commit()
    flash('Post updated successfully!', 'success')
    return redirect(url_for('main.single_post', post_id=post_id))

@bp.route('/post/<int:post_id>/delete', methods=['POST'])
def delete_post(post_id):
    if 'token' not in session:
        return redirect(url_for('main.login'))
    decoded = jwt.decode(session['token'], JWT_SECRET, algorithms=['HS256'])
    post = Post.query.get_or_404(post_id)
    if post.user_id != decoded['user_id']:
        flash('Unauthorized action', 'danger')
        return redirect(url_for('main.single_post', post_id=post_id))
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('main.index'))

@bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
def delete_comment(comment_id):
    if 'token' not in session:
        return redirect(url_for('main.login'))
    decoded = jwt.decode(session['token'], JWT_SECRET, algorithms=['HS256'])
    comment = Comment.query.get_or_404(comment_id)
    if comment.user_id != decoded['user_id']:
        flash('Unauthorized action', 'danger')
        return redirect(url_for('main.single_post', post_id=comment.post_id))
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted successfully!', 'success')
    return redirect(url_for('main.single_post', post_id=comment.post_id))

@bp.route('/comment/<int:comment_id>/like', methods=['POST'])
def like_comment(comment_id):
    if 'token' not in session:
        return redirect(url_for('main.login'))
    decoded = jwt.decode(session['token'], JWT_SECRET, algorithms=['HS256'])
    existing_like = CommentLike.query.filter_by(user_id=decoded['user_id'], comment_id=comment_id).first()
    if not existing_like:
        like = CommentLike(user_id=decoded['user_id'], comment_id=comment_id)
        db.session.add(like)
        db.session.commit()
        flash('Comment liked!', 'success')
    return redirect(url_for('main.single_post', post_id=Comment.query.get_or_404(comment_id).post_id))

@bp.route('/post/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    if 'token' not in session:
        return redirect(url_for('main.login'))
    decoded = jwt.decode(session['token'], JWT_SECRET, algorithms=['HS256'])
    existing_like = PostLike.query.filter_by(user_id=decoded['user_id'], post_id=post_id).first()
    if not existing_like:
        like = PostLike(user_id=decoded['user_id'], post_id=post_id)
        db.session.add(like)
        db.session.commit()
        flash('Post liked!', 'success')
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/report', methods=['POST'])
def report():
    if 'token' not in session:
        return redirect(url_for('main.login'))
    decoded = jwt.decode(session['token'], JWT_SECRET, algorithms=['HS256'])
    post_id = request.form.get('post_id')
    comment_id = request.form.get('comment_id')
    reason = request.form['reason']  # VULNERABLE: No sanitization (XSS, SQLi potential)
    report = Report(user_id=decoded['user_id'], post_id=post_id, comment_id=comment_id, reason=reason)
    db.session.add(report)
    db.session.commit()
    flash('Report submitted successfully!', 'success')
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/profile/<int:id>', methods=['GET', 'POST'])
def profile(id):
    user = User.query.get(id)
    if not user:
        return "User not found", 404
    editable = False
    current_user = None
    if 'token' in session:
        try:
            decoded = jwt.decode(session['token'], JWT_SECRET, algorithms=['HS256'])
            current_user = User.query.get(decoded['user_id'])
            if decoded['user_id'] == id:
                editable = True
        except PyJWTError:
            pass
    if request.method == 'POST' and editable:
        bio = request.form.get('bio')
        image_url = request.form.get('image_url')
        user.bio = bio
        user.image_url = image_url
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    return render_template('profile.html', user=user, editable=editable, current_user=current_user)

@bp.route('/share/<int:post_id>', methods=['POST'])
def share_post(post_id):
    # VULNERABLE: Open redirect using user-supplied 'next' parameter
    next_url = request.args.get('next')
    if next_url:
        return redirect(next_url)
    flash('Post shared!', 'success')
    return redirect(url_for('main.index'))

@bp.route('/robots.txt')
def robots_txt():
    import os
    robots_path = os.path.join(current_app.root_path, '..', 'robot.txt')
    return send_from_directory(os.path.dirname(robots_path), os.path.basename(robots_path), mimetype='text/plain')

@bp.route('/create_post')
def create_post_page():
    if 'token' not in session:
        return redirect(url_for('main.login'))
    decoded = jwt.decode(session['token'], JWT_SECRET, algorithms=['HS256'])
    user = User.query.get(decoded['user_id'])
    return render_template('create_post.html', user=user)

@bp.route('/search_posts')
def search_posts():
    if 'token' not in session:
        return redirect(url_for('main.login'))
    q = request.args.get('q', '')
    if q.startswith('#'):
        posts = Post.query.filter(Post.content.ilike(f'%{q}%')).order_by(Post.created_at.desc()).all()
    else:
        posts = Post.query.filter(Post.content.ilike(f'%{q}%')).order_by(Post.created_at.desc()).all()
    decoded = jwt.decode(session['token'], JWT_SECRET, algorithms=['HS256'])
    user = User.query.get(decoded['user_id'])
    return render_template('search_posts.html', user=user, posts=posts, query=q)

@bp.route('/search_profile')
def search_profile():
    if 'token' not in session:
        return redirect(url_for('main.login'))
    username = request.args.get('username', '').lstrip('@')
    user_obj = User.query.filter_by(username=username).first()
    if user_obj:
        return redirect(url_for('main.profile', id=user_obj.id))
    flash('Profile not found', 'danger')
    return redirect(url_for('main.index'))

@bp.route('/friends')
def friends():
    if 'token' not in session:
        return redirect(url_for('main.login'))
    decoded = jwt.decode(session['token'], JWT_SECRET, algorithms=['HS256'])
    user = User.query.get(decoded['user_id'])
    # Only show users who are friends via Friendship table
    friend_ids = [f.friend_id for f in Friendship.query.filter_by(user_id=user.id).all()]
    friends = User.query.filter(User.id.in_(friend_ids)).all() if friend_ids else []
    return render_template('friends.html', user=user, friends=friends)

@bp.route('/notifications')
def notifications():
    if 'token' not in session:
        return redirect(url_for('main.login'))
    decoded = jwt.decode(session['token'], JWT_SECRET, algorithms=['HS256'])
    user = User.query.get(decoded['user_id'])
    notifications = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).all()
    # Do NOT show friend requests here anymore
    return render_template('notifications.html', user=user, notifications=notifications)

@bp.route('/logout')
def logout():
    session.pop('token', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('main.login'))

@bp.route('/friend_request/<int:to_user_id>', methods=['POST'])
def send_friend_request(to_user_id):
    if 'token' not in session:
        return redirect(url_for('main.login'))
    decoded = jwt.decode(session['token'], JWT_SECRET, algorithms=['HS256'])
    from_user_id = decoded['user_id']
    # Check if already friends or request exists
    existing = FriendRequest.query.filter_by(from_user_id=from_user_id, to_user_id=to_user_id).first()
    if not existing:
        fr = FriendRequest(from_user_id=from_user_id, to_user_id=to_user_id)
        db.session.add(fr)
        # Create notification for receiver
        notif = Notification(user_id=to_user_id, message='You have a new friend request.', link=url_for('main.friend_requests_page'))
        db.session.add(notif)
        db.session.commit()
        flash('Friend request sent!', 'success')
    else:
        flash('Friend request already sent or exists.', 'warning')
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/cancel_friend_request/<int:to_user_id>', methods=['POST'])
def cancel_friend_request(to_user_id):
    if 'token' not in session:
        return redirect(url_for('main.login'))
    decoded = jwt.decode(session['token'], JWT_SECRET, algorithms=['HS256'])
    from_user_id = decoded['user_id']
    fr = FriendRequest.query.filter_by(from_user_id=from_user_id, to_user_id=to_user_id, status='pending').first()
    if fr:
        db.session.delete(fr)
        db.session.commit()
        flash('Friend request cancelled.', 'info')
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/respond_friend_request/<int:request_id>/<action>', methods=['POST'])
def respond_friend_request(request_id, action):
    if 'token' not in session:
        return redirect(url_for('main.login'))
    decoded = jwt.decode(session['token'], JWT_SECRET, algorithms=['HS256'])
    user_id = decoded['user_id']
    fr = FriendRequest.query.get_or_404(request_id)
    if fr.to_user_id != user_id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('main.notifications'))
    if action == 'accept':
        fr.status = 'accepted'
        # Create friendship for both users
        friendship1 = Friendship(user_id=fr.from_user_id, friend_id=fr.to_user_id)
        friendship2 = Friendship(user_id=fr.to_user_id, friend_id=fr.from_user_id)
        db.session.add(friendship1)
        db.session.add(friendship2)
        notif = Notification(user_id=fr.from_user_id, message='Your friend request was accepted.', link=url_for('main.profile', id=user_id))
        db.session.add(notif)
    elif action == 'reject':
        fr.status = 'rejected'
        notif = Notification(user_id=fr.from_user_id, message='Your friend request was rejected.', link=url_for('main.profile', id=user_id))
        db.session.add(notif)
    db.session.commit()
    flash('Friend request updated.', 'success')
    return redirect(url_for('main.friend_requests_page'))

@bp.route('/friend_requests')
def friend_requests_page():
    if 'token' not in session:
        return redirect(url_for('main.login'))
    decoded = jwt.decode(session['token'], JWT_SECRET, algorithms=['HS256'])
    user = User.query.get(decoded['user_id'])
    # Show friend requests received and sent
    received = FriendRequest.query.filter_by(to_user_id=user.id, status='pending').all()
    sent = FriendRequest.query.filter_by(from_user_id=user.id, status='pending').all()
    return render_template('friend_requests.html', user=user, received=received, sent=sent)

@bp.route('/unfriend/<int:user_id>', methods=['POST'])
def unfriend(user_id):
    if 'token' not in session:
        return redirect(url_for('main.login'))
    decoded = jwt.decode(session['token'], JWT_SECRET, algorithms=['HS256'])
    current_user_id = decoded['user_id']
    # Remove both directions of friendship
    Friendship.query.filter_by(user_id=current_user_id, friend_id=user_id).delete()
    Friendship.query.filter_by(user_id=user_id, friend_id=current_user_id).delete()
    db.session.commit()
    flash('Unfriended successfully.', 'info')
    return redirect(url_for('main.profile', id=user_id))