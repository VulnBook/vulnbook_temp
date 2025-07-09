#!/usr/bin/env python3
"""
VulnBook Database Setup Script
==============================

This script creates the database tables and populates them with demo data
for the VulnBook vulnerable social networking application.

Usage:
    python database_setup.py

Requirements:
    - Flask application configured with SQLAlchemy
    - PostgreSQL database running (or SQLite for development)
    - All dependencies installed from requirements.txt
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app
from app.db import db
from app.db import create_app
from app.models import (
    User, Post, Comment, PostImage, PostLike, CommentLike, 
    Report, FriendRequest, Notification, Friendship, 
    MarketplaceItem, Coupon
)

def create_demo_data():
    """Create demo data for the VulnBook application"""
    
    print("Creating demo users...")
    
    # Create demo users with intentionally vulnerable plain text passwords
    # Remove existing users with the same usernames to avoid UNIQUE constraint errors
    usernames = ['alice', 'bob', 'charlie', 'diana', 'eve']
    for uname in usernames:
        existing = User.query.filter_by(username=uname).first()
        if existing:
            # Remove related friendships first to avoid NOT NULL constraint errors
            Friendship.query.filter((Friendship.user_id == existing.id) | (Friendship.friend_id == existing.id)).delete(synchronize_session=False)
            # Remove related marketplace items
            MarketplaceItem.query.filter_by(user_id=existing.id).delete(synchronize_session=False)
            # Remove related posts and their dependencies
            user_posts = Post.query.filter_by(user_id=existing.id).all()
            for post in user_posts:
                # Remove post likes
                PostLike.query.filter_by(post_id=post.id).delete(synchronize_session=False)
                # Remove post images
                PostImage.query.filter_by(post_id=post.id).delete(synchronize_session=False)
                # Remove comments and their likes
                comments = Comment.query.filter_by(post_id=post.id).all()
                for comment in comments:
                    CommentLike.query.filter_by(comment_id=comment.id).delete(synchronize_session=False)
                    db.session.delete(comment)
                db.session.delete(post)
            # Remove comments made by the user and their likes
            user_comments = Comment.query.filter_by(user_id=existing.id).all()
            for comment in user_comments:
                CommentLike.query.filter_by(comment_id=comment.id).delete(synchronize_session=False)
                db.session.delete(comment)
            # Remove likes made by the user
            PostLike.query.filter_by(user_id=existing.id).delete(synchronize_session=False)
            CommentLike.query.filter_by(user_id=existing.id).delete(synchronize_session=False)
            # Remove notifications, reports, friend requests
            Notification.query.filter_by(user_id=existing.id).delete(synchronize_session=False)
            Report.query.filter_by(user_id=existing.id).delete(synchronize_session=False)
            FriendRequest.query.filter((FriendRequest.from_user_id == existing.id) | (FriendRequest.to_user_id == existing.id)).delete(synchronize_session=False)
            db.session.delete(existing)
    db.session.commit()

    users = [
        User(
            username='alice',
            firstname='Alice',
            lastname='Smith',
            dob=datetime(1995, 5, 15).date(),
            password='password123',  # Intentionally vulnerable: plain text
            bio='Software developer who loves coding and coffee ☕',
            image_url='/static/uploads/0ef067dd-073e-4c5f-8ce0-1e2f04a727e3.jpg',
            created_at=datetime.now(timezone.utc)
        ),
        User(
            username='bob',
            firstname='Bob',
            lastname='Brown',
            dob=datetime(1992, 8, 22).date(),
            password='qwerty',  # Intentionally vulnerable: weak password
            bio='Security researcher and bug bounty hunter 🔍',
            image_url='/static/uploads/0ef067dd-073e-4c5f-8ce0-1e2f04a727e3.jpg',
            created_at=datetime.now(timezone.utc)
        ),
        User(
            username='charlie',
            firstname='Charlie',
            lastname='Davis',
            dob=datetime(1998, 3, 10).date(),
            password='123456',  # Intentionally vulnerable: weak password
            bio='Web designer and UI/UX enthusiast 🎨',
            image_url='/static/uploads/0ef067dd-073e-4c5f-8ce0-1e2f04a727e3.jpg',
            created_at=datetime.now(timezone.utc)
        ),
        User(
            username='diana',
            firstname='Diana',
            lastname='Evans',
            dob=datetime(1994, 12, 5).date(),
            password='password',  # Intentionally vulnerable: common password
            bio='Data scientist working with machine learning 🤖',
            image_url='/static/uploads/0ef067dd-073e-4c5f-8ce0-1e2f04a727e3.jpg',
            created_at=datetime.now(timezone.utc)
        ),
        User(
            username='eve',
            firstname='Eve',
            lastname='Foster',
            dob=datetime(2000, 7, 20).date(),
            password='letmein',  # Intentionally vulnerable: weak password
            bio='Cybersecurity student learning ethical hacking 🛡️',
            image_url='/static/uploads/0ef067dd-073e-4c5f-8ce0-1e2f04a727e3.jpg',
            created_at=datetime.now(timezone.utc)
        )
    ]
    
    for user in users:
        db.session.add(user)
    
    db.session.commit()
    print(f"Created {len(users)} demo users")
    
    # Create friendships
    print("Creating friendships...")
    friendships = [
        Friendship(user_id=1, friend_id=2),  # alice <-> bob
        Friendship(user_id=2, friend_id=3),  # bob <-> charlie
        Friendship(user_id=3, friend_id=4),  # charlie <-> diana
        Friendship(user_id=4, friend_id=5),  # diana <-> eve
    ]
    
    for friendship in friendships:
        db.session.add(friendship)
    
    db.session.commit()
    print(f"Created {len(friendships)} friendships")
    
    # Create demo posts
    print("Creating demo posts...")
    posts = [
        Post(
            user_id=1,
            content='Welcome to VulnBook! 🎉 This is a vulnerable social networking app for security testing. #vulnbook #security',
            created_at=datetime.now(timezone.utc) - timedelta(days=5)
        ),
        Post(
            user_id=2,
            content='Just deployed my new Flask application! Love working with Python 🐍 #python #flask #webdev',
            created_at=datetime.now(timezone.utc) - timedelta(days=4)
        ),
        Post(
            user_id=3,
            content='Found an interesting SQL injection vulnerability today. Always validate your inputs! #sqli #security #bugbounty',
            created_at=datetime.now(timezone.utc) - timedelta(days=3)
        ),
        Post(
            user_id=4,
            content='Working on a new UI design for mobile apps. User experience is everything! 📱 #ui #ux #design',
            created_at=datetime.now(timezone.utc) - timedelta(days=2)
        ),
        Post(
            user_id=5,
            content='Training a neural network to detect malware. Machine learning + cybersecurity = ❤️ #ml #ai #cybersecurity',
            created_at=datetime.now(timezone.utc) - timedelta(days=1)
        ),
        Post(
            user_id=2,
            content='Coffee break! ☕ Nothing beats a good cup of coffee while coding.',
            created_at=datetime.now(timezone.utc) - timedelta(hours=6)
        ),
        Post(
            user_id=3,
            content='Check out this awesome security tool I found: https://github.com/example/security-tool #tools #security',
            created_at=datetime.now(timezone.utc) - timedelta(hours=3)
        )
    ]
    
    for post in posts:
        db.session.add(post)
    
    db.session.commit()
    print(f"Created {len(posts)} demo posts")
    
    # Create demo comments
    print("Creating demo comments...")
    comments = [
        Comment(
            post_id=1,
            user_id=2,
            content='Great initiative! Looking forward to testing this.',
            created_at=datetime.now(timezone.utc) - timedelta(days=4, hours=23)
        ),
        Comment(
            post_id=1,
            user_id=3,
            content='Perfect for my security research! Thanks for sharing.',
            created_at=datetime.now(timezone.utc) - timedelta(days=4, hours=22)
        ),
        Comment(
            post_id=2,
            user_id=1,
            content='Flask is awesome! Keep up the good work.',
            created_at=datetime.now(timezone.utc) - timedelta(days=3, hours=23)
        ),
        Comment(
            post_id=3,
            user_id=4,
            content='Very informative! Input validation is crucial.',
            created_at=datetime.now(timezone.utc) - timedelta(days=2, hours=23)
        ),
        Comment(
            post_id=4,
            user_id=5,
            content='Love the design! User experience is indeed everything.',
            created_at=datetime.now(timezone.utc) - timedelta(days=1, hours=23)
        )
    ]
    
    for comment in comments:
        db.session.add(comment)
    
    db.session.commit()
    print(f"Created {len(comments)} demo comments")
    
    # Create demo likes
    print("Creating demo likes...")
    # Remove all existing likes to avoid UNIQUE constraint errors
    PostLike.query.delete()
    db.session.commit()
    likes = [
        PostLike(post_id=1, user_id=2, created_at=datetime.now(timezone.utc)),
        PostLike(post_id=1, user_id=3, created_at=datetime.now(timezone.utc)),
        PostLike(post_id=1, user_id=4, created_at=datetime.now(timezone.utc)),
        PostLike(post_id=2, user_id=1, created_at=datetime.now(timezone.utc)),
        PostLike(post_id=2, user_id=3, created_at=datetime.now(timezone.utc)),
        PostLike(post_id=3, user_id=1, created_at=datetime.now(timezone.utc)),
        PostLike(post_id=3, user_id=4, created_at=datetime.now(timezone.utc)),
        PostLike(post_id=4, user_id=5, created_at=datetime.now(timezone.utc)),
        PostLike(post_id=5, user_id=2, created_at=datetime.now(timezone.utc)),
        PostLike(post_id=6, user_id=3, created_at=datetime.now(timezone.utc)),
        PostLike(post_id=7, user_id=4, created_at=datetime.now(timezone.utc)),
        # Intentionally vulnerable: Allow multiple likes from same user (but only one will be inserted due to UNIQUE constraint)
        # PostLike(post_id=1, user_id=2),  # Duplicate like
        # PostLike(post_id=2, user_id=1),  # Duplicate like
    ]
    for like in likes:
        db.session.add(like)
    
    db.session.commit()
    print(f"Created {len(likes)} demo likes")
    
    # Create demo marketplace items
    print("Creating demo marketplace items...")
    marketplace_items = [
        MarketplaceItem(
            user_id=2,
            description='Python Programming Course - Complete Guide',
            price=29.99,
            image_url='static/uploads/python_course.jpg',
            review='Comprehensive Python course covering basics to advanced topics. Perfect for beginners!',
            approved=True
        ),
        MarketplaceItem(
            user_id=3,
            description='Security Testing Tools Bundle',
            price=49.99,
            image_url='static/uploads/security_tools.jpg',
            review='Professional security testing tools for penetration testing and vulnerability assessment.',
            approved=True
        ),
        MarketplaceItem(
            user_id=4,
            description='UI/UX Design Templates Pack',
            price=19.99,
            image_url='static/uploads/ui_templates.jpg',
            review='Modern and responsive UI/UX templates for web and mobile applications.',
            approved=True
        ),
        MarketplaceItem(
            user_id=5,
            description='Machine Learning Algorithms eBook',
            price=15.99,
            image_url='static/uploads/ml_ebook.jpg',
            review='Detailed explanation of popular machine learning algorithms with code examples.',
            approved=True
        ),
        MarketplaceItem(
            user_id=1,
            description='Web Development Bootcamp',
            price=99.99,
            image_url='static/uploads/web_bootcamp.jpg',
            review='Full-stack web development bootcamp with hands-on projects.',
            approved=True
        )
    ]
    
    for item in marketplace_items:
        db.session.add(item)
    
    db.session.commit()
    print(f"Created {len(marketplace_items)} demo marketplace items")
    
    # Create demo coupons
    print("Creating demo coupons...")
    # Remove existing coupons with the same codes to avoid UNIQUE constraint errors
    coupon_codes = ['WELCOME10', 'SAVE20', 'STUDENT50', 'EXPIRED', 'FREEBIE']
    for code in coupon_codes:
        Coupon.query.filter_by(coupon_code=code).delete(synchronize_session=False)
    db.session.commit()
    coupons = [
        Coupon(
            coupon_code='WELCOME10',
            percentage=10,
            max_discount=10.0,
            price=5.0,
            expiry_date=datetime.now(timezone.utc) + timedelta(days=30),
            created_at=datetime.now(timezone.utc)
        ),
        Coupon(
            coupon_code='SAVE20',
            percentage=20,
            max_discount=20.0,
            price=8.0,
            expiry_date=datetime.now(timezone.utc) + timedelta(days=15),
            created_at=datetime.now(timezone.utc)
        ),
        Coupon(
            coupon_code='STUDENT50',
            percentage=50,
            max_discount=50.0,
            price=15.0,
            expiry_date=datetime.now(timezone.utc) + timedelta(days=7),
            created_at=datetime.now(timezone.utc)
        ),
        Coupon(
            coupon_code='EXPIRED',
            percentage=25,
            max_discount=25.0,
            price=10.0,
            expiry_date=datetime.now(timezone.utc) - timedelta(days=1),
            created_at=datetime.now(timezone.utc)
        ),
        Coupon(
            coupon_code='FREEBIE',
            percentage=100,
            max_discount=1000.0,
            price=0.0,
            expiry_date=datetime.now(timezone.utc) + timedelta(days=365),
            created_at=datetime.now(timezone.utc)
        )
    ]
    
    for coupon in coupons:
        db.session.add(coupon)
    
    db.session.commit()
    print(f"Created {len(coupons)} demo coupons")
    
    # Create demo notifications
    print("Creating demo notifications...")
    notifications = [
        Notification(
            user_id=2,
            message='Welcome to VulnBook! Start by creating your first post.',
            link=None,
            is_read=False,
            created_at=datetime.now(timezone.utc) - timedelta(days=5)
        ),
        Notification(
            user_id=3,
            message='You have a new friend request.',
            link=None,
            is_read=False,
            created_at=datetime.now(timezone.utc) - timedelta(days=3)
        ),
        Notification(
            user_id=4,
            message='Someone liked your post!',
            link=None,
            is_read=False,
            created_at=datetime.now(timezone.utc) - timedelta(days=2)
        ),
        Notification(
            user_id=5,
            message='Your marketplace item has been approved!',
            link=None,
            is_read=False,
            created_at=datetime.now(timezone.utc) - timedelta(days=1)
        )
    ]
    
    for notification in notifications:
        db.session.add(notification)
    
    db.session.commit()
    print(f"Created {len(notifications)} demo notifications")

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    db.create_all()
    print("Database tables created successfully!")

def reset_database():
    """Drop all tables and recreate them"""
    print("Dropping all database tables...")
    db.drop_all()
    print("All tables dropped.")
    create_tables()

def main():
    """Main function to set up the database"""
    print("VulnBook Database Setup")
    print("=" * 50)

    # Create Flask app context using the same config as in db.py
    app = create_app()

    with app.app_context():
        # Ask user what they want to do
        print("\nWhat would you like to do?")
        print("1. Create tables only")
        print("2. Create tables and populate with demo data")
        print("3. Reset database (drop all tables and recreate)")
        print("4. Add demo data to existing database")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            create_tables()
        elif choice == '2':
            create_tables()
            create_demo_data()
        elif choice == '3':
            confirm = input("Are you sure you want to reset the database? This will DELETE ALL DATA! (y/N): ").strip().lower()
            if confirm == 'y':
                reset_database()
                create_demo_data()
            else:
                print("Operation cancelled.")
        elif choice == '4':
            create_demo_data()
        else:
            print("Invalid choice. Please run the script again.")
            return
    
    print("\n" + "=" * 50)
    print("Database setup completed successfully!")
    print("\nDemo Login Credentials:")
    print("- Username: alice, Password: password123")
    print("- Username: bob, Password: qwerty")
    print("- Username: charlie, Password: 123456")
    print("- Username: diana, Password: password")
    print("- Username: eve, Password: letmein")
    print("\nAdmin Panel Access:")
    print("\nDemo Coupons:")
    print("- WELCOME10 (10% off)")
    print("- SAVE20 (20% off)")
    print("- STUDENT50 (50% off)")
    print("- FREEBIE (100% off - for testing vulnerabilities)")
    print("\nNOTE: All passwords are intentionally weak for security testing purposes!")

if __name__ == '__main__':
    main()
