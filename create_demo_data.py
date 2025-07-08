#!/usr/bin/env python3
"""
Demo Database Setup Script for VulnBook
Creates sample data for testing and demonstration purposes.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import User, Post, Comment, PostImage, PostLike, CommentLike, FriendRequest, Notification, Friendship, Report, MarketplaceItem, Coupon
from app.db import db
from app import create_app
from datetime import datetime

def create_demo_data():
    """Create demo data for VulnBook"""
    
    print("Creating demo users...")
    # Create demo users (passwords are plain text - vulnerability!)
    users = [
        User(username='alice', email='alice@example.com', password='password123', bio='Hi, I\'m Alice!'),
        User(username='bob', email='bob@example.com', password='secret456', bio='Bob here, love tech!'),
        User(username='charlie', email='charlie@example.com', password='pass789', bio='Charlie - security enthusiast'),
        User(username='admin', email='admin@example.com', password='admin123', bio='System Administrator'),
        User(username='eve', email='eve@example.com', password='hacker', bio='Eve - testing security'),
    ]
    
    for user in users:
        db.session.add(user)
    db.session.commit()
    
    print("Creating demo posts...")
    # Create demo posts
    posts = [
        Post(user_id=1, content='Welcome to VulnBook! #socialnetwork #demo', hashtags='#socialnetwork,#demo'),
        Post(user_id=2, content='Just discovered some interesting #security vulnerabilities! #hacking', hashtags='#security,#hacking'),
        Post(user_id=3, content='Anyone interested in #cybersecurity meetup? #networking', hashtags='#cybersecurity,#networking'),
        Post(user_id=1, content='Beautiful sunset today! #nature #photography', hashtags='#nature,#photography'),
        Post(user_id=4, content='System maintenance scheduled for tonight. #admin #maintenance', hashtags='#admin,#maintenance'),
    ]
    
    for post in posts:
        db.session.add(post)
    db.session.commit()
    
    print("Creating demo comments...")
    # Create demo comments
    comments = [
        Comment(post_id=1, user_id=2, content='Great to be here!'),
        Comment(post_id=1, user_id=3, content='Looking forward to exploring!'),
        Comment(post_id=2, user_id=1, content='Interesting findings, Bob!'),
        Comment(post_id=3, user_id=2, content='Count me in for the meetup!'),
        Comment(post_id=4, user_id=3, content='Beautiful shot!'),
    ]
    
    for comment in comments:
        db.session.add(comment)
    db.session.commit()
    
    print("Creating demo likes...")
    # Create demo likes
    likes = [
        PostLike(post_id=1, user_id=2),
        PostLike(post_id=1, user_id=3),
        PostLike(post_id=2, user_id=1),
        PostLike(post_id=3, user_id=1),
        PostLike(post_id=4, user_id=2),
        CommentLike(comment_id=1, user_id=1),
        CommentLike(comment_id=2, user_id=1),
    ]
    
    for like in likes:
        db.session.add(like)
    db.session.commit()
    
    print("Creating demo friend requests and friendships...")
    # Create demo friend requests
    friend_requests = [
        FriendRequest(from_user_id=1, to_user_id=2, status='accepted'),
        FriendRequest(from_user_id=2, to_user_id=3, status='pending'),
        FriendRequest(from_user_id=3, to_user_id=1, status='accepted'),
    ]
    
    for fr in friend_requests:
        db.session.add(fr)
    db.session.commit()
    
    # Create friendships for accepted requests
    friendships = [
        Friendship(user_id=1, friend_id=2),
        Friendship(user_id=2, friend_id=1),
        Friendship(user_id=3, friend_id=1),
        Friendship(user_id=1, friend_id=3),
    ]
    
    for friendship in friendships:
        db.session.add(friendship)
    db.session.commit()
    
    print("Creating demo notifications...")
    # Create demo notifications
    notifications = [
        Notification(user_id=2, message='alice sent you a friend request.'),
        Notification(user_id=3, message='bob sent you a friend request.'),
        Notification(user_id=1, message='charlie sent you a friend request.'),
        Notification(user_id=1, message='You have a new like on your post!'),
    ]
    
    for notif in notifications:
        db.session.add(notif)
    db.session.commit()
    
    print("Creating demo marketplace items...")
    # Create demo marketplace items
    items = [
        MarketplaceItem(user_id=1, description='Vintage Camera', price=150.00, is_approved=True),
        MarketplaceItem(user_id=2, description='Programming Book Collection', price=75.50, is_approved=True),
        MarketplaceItem(user_id=3, description='Security Tools Kit', price=200.00, is_approved=False),
        MarketplaceItem(user_id=4, description='Laptop Stand', price=45.00, is_approved=True),
    ]
    
    for item in items:
        db.session.add(item)
    db.session.commit()
    
    print("Creating demo coupons...")
    # Create demo coupons
    coupons = [
        Coupon(coupon_code='WELCOME10', percentage=10, max_discount=50.00),
        Coupon(coupon_code='SAVE20', percentage=20, max_discount=100.00),
        Coupon(coupon_code='STUDENT15', percentage=15, max_discount=75.00),
        Coupon(coupon_code='MEGA50', percentage=50, max_discount=500.00),  # Vulnerable: High discount
    ]
    
    for coupon in coupons:
        db.session.add(coupon)
    db.session.commit()
    
    print("Creating demo reports...")
    # Create demo reports
    reports = [
        Report(user_id=5, post_id=2, reason='Suspicious content about security vulnerabilities'),
        Report(user_id=1, comment_id=1, reason='Spam comment'),
    ]
    
    for report in reports:
        db.session.add(report)
    db.session.commit()
    
    print("✅ Demo data created successfully!")
    print("\nDemo Accounts:")
    print("- alice:password123 (Regular user)")
    print("- bob:secret456 (Regular user)")
    print("- charlie:pass789 (Regular user)")
    print("- admin:admin123 (Admin account)")
    print("- eve:hacker (Security tester)")
    print("\nDemo Coupons:")
    print("- WELCOME10 (10% off, max $50)")
    print("- SAVE20 (20% off, max $100)")
    print("- STUDENT15 (15% off, max $75)")
    print("- MEGA50 (50% off, max $500) - Vulnerable!")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        # Reset database
        print("Resetting database...")
        db.drop_all()
        db.create_all()
        
        # Create demo data
        create_demo_data()
