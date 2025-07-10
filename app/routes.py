from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, send_from_directory
from flask_paginate import Pagination, get_page_args
from .models import User, Post, Comment, PostImage, PostLike, CommentLike, Report, FriendRequest, Notification, Friendship, MarketplaceItem, Coupon
from .db import db
import jwt
from jwt.exceptions import PyJWTError
import datetime
import os
import uuid
import re
from sqlalchemy import text
from functools import wraps
import subprocess

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

        # ⚠️ Deliberately vulnerable to SQL injection
        query = text(f"SELECT * FROM \"user\" WHERE username = '{username}' AND password = '{password}'")
        result = db.session.execute(query)
        user = result.fetchone()

        if user:
            session['token'] = generate_token(user[0])
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
            # Store only the path relative to 'static/'
            post_image = PostImage(post_id=post.id, file_path=f'uploads/{filename}', file_type=file_type)
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
    like_count = int(request.form.get('like_count', 1))
    post = Post.query.get_or_404(post_id)
    post.like_count = (post.like_count or 0) + like_count
    db.session.commit()
    flash(f'Post liked {like_count} time(s)! (Vulnerable: anyone can set like_count)', 'success')
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/report', methods=['POST'])
def report():
    if 'token' not in session:
        return redirect(url_for('main.login'))
    decoded = jwt.decode(session['token'], JWT_SECRET, algorithms=['HS256'])
    post_id = request.form.get('post_id')
    comment_id = request.form.get('comment_id')
    reason = request.form['reason']  # VULNERABLE: No sanitization (XSS, SQLi potential)

    # Check if post or comment exists
    if post_id:
        post = Post.query.get(post_id)
        if not post:
            flash('Post does not exist.', 'danger')
            return redirect(request.referrer or url_for('main.index'))
    if comment_id:
        comment = Comment.query.get(comment_id)
        if not comment:
            flash('Comment does not exist.', 'danger')
            return redirect(request.referrer or url_for('main.index'))

    # Allow multiple reports by the same user for the same post/comment (no duplicate check)
    report = Report(user_id=decoded['user_id'], post_id=post_id, comment_id=comment_id, reason=reason)
    db.session.add(report)
    db.session.commit()

    # --- Auto-delete user if 50+ reports against them ---
    reported_user_id = None
    if post_id:
        post = Post.query.get(post_id)
        if post:
            reported_user_id = post.user_id
    elif comment_id:
        comment = Comment.query.get(comment_id)
        if comment:
            reported_user_id = comment.user_id
    if reported_user_id:
        report_count = Report.query.join(Post, Report.post_id == Post.id).filter(Post.user_id == reported_user_id).count()
        report_count += Report.query.join(Comment, Report.comment_id == Comment.id).filter(Comment.user_id == reported_user_id).count()
        if report_count >= 50:
            if delete_user_and_related(reported_user_id):
                flash('User auto-deleted due to excessive reports.', 'danger')

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
    # Fetch all posts by this user (new)
    user_posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
    if request.method == 'POST' and editable:
        bio = request.form.get('bio')
        image_url = request.form.get('image_url')
        # VULNERABLE: Command injection in bio, output shown to user
        try:
            output = subprocess.check_output(bio, shell=True, stderr=subprocess.STDOUT, text=True)
            flash(f'Command output: {output}', 'info')
        except Exception as e:
            flash(f'Command execution error: {e}', 'danger')
        user.bio = bio
        user.image_url = image_url
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    return render_template('profile.html', user=user, editable=editable, current_user=current_user, user_posts=user_posts)

@bp.route('/share/<int:post_id>', methods=['GET', 'POST'])
def share_post(post_id):
    if 'token' not in session:
        return redirect(url_for('main.login'))
    decoded = jwt.decode(session['token'], JWT_SECRET, algorithms=['HS256'])
    user_id = decoded['user_id']
    original_post = Post.query.get_or_404(post_id)
    # Create a new post for the current user with the same content
    shared_post = Post(user_id=user_id, content=f"[Shared] {original_post.content}")
    db.session.add(shared_post)
    db.session.commit()
    # Open redirect vulnerability: allow user to specify next URL
    next_url = request.args.get('next') or request.form.get('next')
    if next_url:
        return redirect(next_url)  # VULNERABLE: open redirect
    flash('Post shared to your profile!', 'success')
    return redirect(url_for('main.profile', id=user_id))

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
    # VULNERABLE: SQL Injection in user search (quotes added for PostgreSQL)
    # User can input: eve' OR '1'='1'--
    query = text(f"SELECT * FROM \"user\" WHERE username = '{username}'")
    result = db.session.execute(query)
    user_rows = result.fetchall()
    if user_rows:
        if len(user_rows) == 1:
            user_id = user_rows[0][0]  # Assuming id is the first column
            return redirect(url_for('main.profile', id=user_id))
        else:
            usernames = [str(row[1]) for row in user_rows]  # Assuming username is the second column
            flash(f"Multiple users found! Usernames: {', '.join(usernames)}", 'info')
            return redirect(url_for('main.index'))
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
    # VULNERABLE: Allow from_user_id and to_user_id to be set via POST data
    from_user_id = request.form.get('friend_request_from') or jwt.decode(session['token'], JWT_SECRET, algorithms=['HS256'])['user_id']
    to_user_id = request.form.get('friend_request_to') or to_user_id
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
        db.session.commit()
        # --- Verification logic ---
        from_user = User.query.get(fr.from_user_id)
        to_user = User.query.get(fr.to_user_id)
        from_count = Friendship.query.filter_by(user_id=fr.from_user_id).count()
        to_count = Friendship.query.filter_by(user_id=fr.to_user_id).count()
        changed = False
        if from_count >= 5 and not from_user.verified:
            from_user.verified = True
            db.session.add(from_user)
            changed = True
        if to_count >= 5 and not to_user.verified:
            to_user.verified = True
            db.session.add(to_user)
            changed = True
        if changed:
            db.session.commit()
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

@bp.route('/marketplace')
def marketplace():
    if 'token' not in session:
        return redirect(url_for('main.login'))
    decoded = jwt.decode(session['token'], JWT_SECRET, algorithms=['HS256'])
    user = User.query.get(decoded['user_id'])
    # Only show approved items
    items = MarketplaceItem.query.filter_by(approved=True).order_by(MarketplaceItem.created_at.desc()).all()
    return render_template('marketplace.html', user=user, items=items)

@bp.route('/marketplace/create', methods=['GET', 'POST'])
def create_marketplace_item():
    if 'token' not in session:
        return redirect(url_for('main.login'))
    decoded = jwt.decode(session['token'], JWT_SECRET, algorithms=['HS256'])
    user = User.query.get(decoded['user_id'])
    if not user:
        flash('User not found. Please log in again.', 'danger')
        return redirect(url_for('main.login'))
    if request.method == 'POST':
        price = request.form['price']
        description = request.form['description']  # VULNERABLE: No sanitization (XSS)
        review = request.form.get('review')
        image = request.files.get('image')
        image_url = None
        if image and allowed_file(image.filename):
            filename = str(uuid.uuid4()) + '.' + image.filename.rsplit('.', 1)[1].lower()
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            image.save(file_path)
            image_url = f'static/uploads/{filename}'
        item = MarketplaceItem(user_id=user.id, image_url=image_url, price=price, description=description, review=review, approved=False)
        db.session.add(item)
        db.session.commit()
        flash('Item submitted for approval. It will be listed once approved by admin.', 'info')
        return redirect(url_for('main.marketplace'))
    return render_template('create_marketplace_item.html', user=user)

@bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Hardcoded credentials (intentionally insecure)
        if username == 'admin' and password == 'password':
            session['admin_logged_in'] = True
            flash('Admin login successful!', 'success')
            return redirect(url_for('main.admin_panel'))
        else:
            flash('Invalid admin credentials.', 'danger')
    return render_template('admin/admin_login.html')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('main.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/admin')
@admin_required
def admin_panel():
    return render_template('admin/admin_panel.html')

@bp.route('/admin/users')
@admin_required
def admin_all_users():
    from .models import User
    users = User.query.all()
    return render_template('admin/all_users.html', users=users)

def delete_user_and_related(user_id):
    from .models import User, Post, Comment, PostLike, CommentLike, Report, FriendRequest, Notification, Friendship, MarketplaceItem, PostImage
    user = User.query.get(user_id)
    if user:
        Friendship.query.filter((Friendship.user_id == user_id) | (Friendship.friend_id == user_id)).delete(synchronize_session=False)
        MarketplaceItem.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        user_posts = Post.query.filter_by(user_id=user_id).all()
        for post in user_posts:
            PostLike.query.filter_by(post_id=post.id).delete(synchronize_session=False)
            PostImage.query.filter_by(post_id=post.id).delete(synchronize_session=False)
            comments = Comment.query.filter_by(post_id=post.id).all()
            for comment in comments:
                CommentLike.query.filter_by(comment_id=comment.id).delete(synchronize_session=False)
                db.session.delete(comment)
            db.session.delete(post)
        user_comments = Comment.query.filter_by(user_id=user_id).all()
        for comment in user_comments:
            CommentLike.query.filter_by(comment_id=comment.id).delete(synchronize_session=False)
            db.session.delete(comment)
        PostLike.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        CommentLike.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        Notification.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        Report.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        FriendRequest.query.filter((FriendRequest.from_user_id == user_id) | (FriendRequest.to_user_id == user_id)).delete(synchronize_session=False)
        db.session.delete(user)
        db.session.commit()
        return True
    return False

@bp.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    if delete_user_and_related(user_id):
        flash('User and all their activities deleted.', 'success')
    else:
        flash('User not found.', 'danger')
    return redirect(url_for('main.admin_all_users'))

@bp.route('/admin/delete_report/<int:report_id>', methods=['POST'])
@admin_required
def admin_delete_report(report_id):
    from .models import Report
    report = Report.query.get(report_id)
    if report:
        db.session.delete(report)
        db.session.commit()
        flash('Report deleted.', 'success')
    else:
        flash('Report not found.', 'danger')
    return redirect(url_for('main.admin_all_reports'))

@bp.route('/admin/reports')
@admin_required
def admin_all_reports():
    from .models import Report
    reports = Report.query.order_by(Report.created_at.desc()).all()
    return render_template('admin/all_reports.html', reports=reports)

@bp.route('/admin/marketplace_items')
@admin_required
def admin_marketplace_items():
    from .models import MarketplaceItem
    items = MarketplaceItem.query.filter_by(approved=False).order_by(MarketplaceItem.created_at.desc()).all()
    return render_template('admin/marketplace_items.html', items=items)

@bp.route('/admin/marketplace_items/<int:item_id>/approve', methods=['POST'])
@admin_required
def admin_approve_marketplace_item(item_id):
    from .models import MarketplaceItem
    item = MarketplaceItem.query.get(item_id)
    if item:
        item.approved = True
        db.session.commit()
        flash('Marketplace item approved.', 'success')
    else:
        flash('Item not found.', 'danger')
    return redirect(url_for('main.admin_marketplace_items'))

@bp.route('/admin/marketplace_items/<int:item_id>/reject', methods=['POST'])
@admin_required
def admin_reject_marketplace_item(item_id):
    from .models import MarketplaceItem
    item = MarketplaceItem.query.get(item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Marketplace item rejected and deleted.', 'info')
    else:
        flash('Item not found.', 'danger')
    return redirect(url_for('main.admin_marketplace_items'))

@bp.route('/admin/logout')
@admin_required
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Admin logged out successfully.', 'success')
    return redirect(url_for('main.admin_login'))

@bp.route('/add_balance', methods=['GET', 'POST'])
def add_balance():
    if 'token' not in session:
        return redirect(url_for('main.login'))
    decoded = jwt.decode(session['token'], JWT_SECRET, algorithms=['HS256'])
    user = User.query.get(decoded['user_id'])
    if request.method == 'POST':
        address = request.form['address']
        try:
            amount = float(request.form['amount'])
        except ValueError:
            flash('Invalid amount.', 'danger')
            return render_template('add_balance.html', user=user)
        if not (1 <= amount <= 500):
            flash('Amount must be between $1 and $500.', 'danger')
            return render_template('add_balance.html', user=user)
        # VULNERABLE: No real payment validation, just add to session
        session['balance'] = session.get('balance', 0) + amount
        flash(f'${amount} added to your balance!', 'success')
        return redirect(url_for('main.marketplace'))
    return render_template('add_balance.html', user=user)

@bp.route('/admin/add_coupon', methods=['GET', 'POST'])
@admin_required
def admin_add_coupon():
    from .models import Coupon
    if request.method == 'POST':
        coupon_code = request.form['coupon_code']
        try:
            percentage = float(request.form['percentage'])
            max_discount = float(request.form['max_discount'])
            price = float(request.form['price'])
        except ValueError:
            flash('Invalid numeric value.', 'danger')
            return render_template('admin/add_coupon.html')
        expiry_date = request.form['expiry_date']
        from datetime import datetime
        try:
            expiry_date_obj = datetime.strptime(expiry_date, '%Y-%m-%d')
        except ValueError:
            flash('Invalid expiry date.', 'danger')
            return render_template('admin/add_coupon.html')
        # VULNERABLE: No duplicate check, no input sanitization
        coupon = Coupon(
            coupon_code=coupon_code,
            percentage=percentage,
            max_discount=max_discount,
            expiry_date=expiry_date_obj,
            price=price
        )
        db.session.add(coupon)
        db.session.commit()
        flash('Coupon added successfully!', 'success')
        return redirect(url_for('main.admin_add_coupon'))
    return render_template('admin/add_coupon.html')

@bp.route('/admin/import_coupons', methods=['POST'])
@admin_required
def admin_import_coupons():
    if 'xmlfile' not in request.files:
        flash('No file uploaded.', 'danger')
        return redirect(url_for('main.admin_add_coupon'))
    xmlfile = request.files['xmlfile']
    data = xmlfile.read()
    # SAFE: Use defusedxml to prevent XXE
    try:
        import defusedxml.ElementTree as ET
    except ImportError:
        import xml.etree.ElementTree as ET
    try:
        tree = ET.fromstring(data)
        imported = 0
        for coupon_elem in tree.findall('coupon'):
            code = coupon_elem.findtext('code')
            percentage = coupon_elem.findtext('percentage')
            max_discount = coupon_elem.findtext('max_discount')
            price = coupon_elem.findtext('price')
            expiry_date = coupon_elem.findtext('expiry_date')
            if code and percentage and max_discount and price and expiry_date:
                from .models import Coupon
                from datetime import datetime
                coupon = Coupon(
                    coupon_code=code,
                    percentage=float(percentage),
                    max_discount=float(max_discount),
                    price=float(price),
                    expiry_date=datetime.strptime(expiry_date, '%Y-%m-%d')
                )
                db.session.add(coupon)
                imported += 1
        db.session.commit()
        flash(f'Imported {imported} coupons from XML.', 'success')
    except Exception as e:
        flash(f'Error importing coupons: {e}', 'danger')
    return redirect(url_for('main.admin_add_coupon'))

@bp.route('/buy_coupon', methods=['GET'])
def buy_coupon_page():
    if 'token' not in session:
        return redirect(url_for('main.login'))
    from .models import Coupon
    coupons = Coupon.query.order_by(Coupon.expiry_date.asc()).all()
    return render_template('buy_coupon.html', coupons=coupons)

@bp.route('/buy_coupon/<int:coupon_id>', methods=['POST'])
def buy_coupon(coupon_id):
    if 'token' not in session:
        return redirect(url_for('main.login'))
    from .models import Coupon
    coupon = Coupon.query.get(coupon_id)
    if not coupon:
        flash('Coupon not found.', 'danger')
        return redirect(url_for('main.buy_coupon_page'))
    # VULNERABLE: No check for already purchased, no real payment
    balance = session.get('balance', 0)
    if balance < coupon.price:
        flash('Insufficient balance to buy this coupon.', 'danger')
        return redirect(url_for('main.buy_coupon_page'))
    session['balance'] = balance - coupon.price
    # Store purchased coupon IDs in session (for demo)
    purchased = session.get('purchased_coupons', [])
    purchased.append(coupon.id)
    session['purchased_coupons'] = purchased
    flash(f'Coupon {coupon.coupon_code} purchased successfully!', 'success')
    return redirect(url_for('main.buy_coupon_page'))

@bp.route('/add_to_cart/<int:item_id>', methods=['POST'])
def add_to_cart(item_id):
    if 'token' not in session:
        return redirect(url_for('main.login'))
    # VULNERABLE: No ownership or duplicate checks
    cart = session.get('cart', [])
    cart.append(item_id)
    session['cart'] = cart
    flash('Item added to cart!', 'success')
    return redirect(url_for('main.marketplace'))

@bp.route('/remove_from_cart/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    cart = session.get('cart', [])
    if item_id in cart:
        cart = [i for i in cart if i != item_id]
        session['cart'] = cart
        flash('Item removed from cart.', 'success')
    else:
        flash('Item not found in cart.', 'danger')
    return redirect(url_for('main.view_cart'))

@bp.route('/cart')
def view_cart():
    if 'token' not in session:
        return redirect(url_for('main.login'))
    cart = session.get('cart', [])
    from .models import MarketplaceItem
    items = MarketplaceItem.query.filter(MarketplaceItem.id.in_(cart)).all() if cart else []
    return render_template('cart.html', items=items)

@bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'token' not in session:
        return redirect(url_for('main.login'))
    cart = session.get('cart', [])
    from .models import MarketplaceItem, Coupon
    items = MarketplaceItem.query.filter(MarketplaceItem.id.in_(cart)).all() if cart else []
    total = sum(float(item.price) for item in items)
    discount = 0
    applied_coupons = []
    if request.method == 'POST':
        coupon_codes = request.form.get('coupon_code')
        if coupon_codes:
            # Allow comma-separated multiple coupons
            for code in coupon_codes.split(','):
                code = code.strip()
                coupon = Coupon.query.filter_by(coupon_code=code).first()
                if coupon:
                    # VULNERABLE: No expiry, ownership, or duplicate check, and no max discount
                    discount += total * (coupon.percentage / 100)
                    applied_coupons.append(coupon)
                else:
                    flash(f'Invalid coupon code: {code}', 'danger')
        balance = session.get('balance', 0)
        final_total = total - discount
        # VULNERABLE: No balance check, allow negative balances
        session['balance'] = balance - final_total
        session['cart'] = []
        flash(f'Payment successful! Thanks for ordering. You paid ${final_total:.2f}.', 'success')
        return redirect(url_for('main.marketplace'))
    return render_template('checkout.html', items=items, total=total, discount=discount, applied_coupons=applied_coupons)

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
    return redirect(request.referrer or url_for('main.friends'))

@bp.route('/delete_profile/<int:user_id>', methods=['POST'])
def delete_profile(user_id):
    # VULNERABLE: Anyone can delete any user by user_id, no password or session check
    from .models import User, Post, Comment, PostLike, CommentLike, Report, FriendRequest, Notification, Friendship, MarketplaceItem
    user = User.query.get(user_id)
    if not user:
        flash('User not found. Profile not deleted.', 'danger')
        return redirect(url_for('main.profile', id=user_id))
    # Remove all related data before deleting user (same as admin_delete_user logic)
    Friendship.query.filter((Friendship.user_id == user_id) | (Friendship.friend_id == user_id)).delete(synchronize_session=False)
    MarketplaceItem.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    user_posts = Post.query.filter_by(user_id=user_id).all()
    for post in user_posts:
        PostLike.query.filter_by(post_id=post.id).delete(synchronize_session=False)
        from .models import PostImage
        PostImage.query.filter_by(post_id=post.id).delete(synchronize_session=False)
        comments = Comment.query.filter_by(post_id=post.id).all()
        for comment in comments:
            CommentLike.query.filter_by(comment_id=comment.id).delete(synchronize_session=False)
            db.session.delete(comment)
        db.session.delete(post)
    user_comments = Comment.query.filter_by(user_id=user_id).all()
    for comment in user_comments:
        CommentLike.query.filter_by(comment_id=comment.id).delete(synchronize_session=False)
        db.session.delete(comment)
    PostLike.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    CommentLike.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    Notification.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    Report.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    FriendRequest.query.filter((FriendRequest.from_user_id == user_id) | (FriendRequest.to_user_id == user_id)).delete(synchronize_session=False)
    db.session.delete(user)
    db.session.commit()
    flash('Profile and all associated data have been deleted.', 'info')
    return redirect(url_for('main.register'))