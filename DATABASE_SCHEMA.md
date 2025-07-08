# VulnBook Database Schema

## Overview
VulnBook uses SQLite database with the following tables:

## Tables

### Users
- `id` (INTEGER, PRIMARY KEY)
- `username` (TEXT, UNIQUE, NOT NULL)
- `email` (TEXT, UNIQUE, NOT NULL)
- `password` (TEXT, NOT NULL) - **VULNERABLE: Plain text storage**
- `bio` (TEXT)
- `image_url` (TEXT)
- `created_at` (DATETIME, DEFAULT: CURRENT_TIMESTAMP)

### Posts
- `id` (INTEGER, PRIMARY KEY)
- `user_id` (INTEGER, FOREIGN KEY → users.id)
- `content` (TEXT, NOT NULL)
- `hashtags` (TEXT) - Comma-separated hashtags
- `created_at` (DATETIME, DEFAULT: CURRENT_TIMESTAMP)

### Comments
- `id` (INTEGER, PRIMARY KEY)
- `post_id` (INTEGER, FOREIGN KEY → posts.id)
- `user_id` (INTEGER, FOREIGN KEY → users.id)
- `content` (TEXT, NOT NULL)
- `parent_id` (INTEGER, FOREIGN KEY → comments.id) - For replies
- `created_at` (DATETIME, DEFAULT: CURRENT_TIMESTAMP)

### PostImages
- `id` (INTEGER, PRIMARY KEY)
- `post_id` (INTEGER, FOREIGN KEY → posts.id)
- `filename` (TEXT, NOT NULL)
- `file_type` (TEXT, NOT NULL) - 'image' or 'video'

### PostLikes
- `id` (INTEGER, PRIMARY KEY)
- `post_id` (INTEGER, FOREIGN KEY → posts.id)
- `user_id` (INTEGER, FOREIGN KEY → users.id)
- `created_at` (DATETIME, DEFAULT: CURRENT_TIMESTAMP)

### CommentLikes
- `id` (INTEGER, PRIMARY KEY)
- `comment_id` (INTEGER, FOREIGN KEY → comments.id)
- `user_id` (INTEGER, FOREIGN KEY → users.id)
- `created_at` (DATETIME, DEFAULT: CURRENT_TIMESTAMP)

### FriendRequests
- `id` (INTEGER, PRIMARY KEY)
- `from_user_id` (INTEGER, FOREIGN KEY → users.id)
- `to_user_id` (INTEGER, FOREIGN KEY → users.id)
- `status` (TEXT, DEFAULT: 'pending') - 'pending', 'accepted', 'rejected'
- `created_at` (DATETIME, DEFAULT: CURRENT_TIMESTAMP)

### Friendships
- `id` (INTEGER, PRIMARY KEY)
- `user_id` (INTEGER, FOREIGN KEY → users.id)
- `friend_id` (INTEGER, FOREIGN KEY → users.id)
- `created_at` (DATETIME, DEFAULT: CURRENT_TIMESTAMP)

### Notifications
- `id` (INTEGER, PRIMARY KEY)
- `user_id` (INTEGER, FOREIGN KEY → users.id)
- `message` (TEXT, NOT NULL)
- `is_read` (BOOLEAN, DEFAULT: False)
- `created_at` (DATETIME, DEFAULT: CURRENT_TIMESTAMP)

### Reports
- `id` (INTEGER, PRIMARY KEY)
- `user_id` (INTEGER, FOREIGN KEY → users.id)
- `post_id` (INTEGER, FOREIGN KEY → posts.id, NULLABLE)
- `comment_id` (INTEGER, FOREIGN KEY → comments.id, NULLABLE)
- `reason` (TEXT, NOT NULL)
- `created_at` (DATETIME, DEFAULT: CURRENT_TIMESTAMP)

### MarketplaceItems
- `id` (INTEGER, PRIMARY KEY)
- `user_id` (INTEGER, FOREIGN KEY → users.id)
- `description` (TEXT, NOT NULL)
- `price` (DECIMAL, NOT NULL)
- `image_url` (TEXT)
- `review` (TEXT) - Admin review notes
- `is_approved` (BOOLEAN, DEFAULT: False)
- `created_at` (DATETIME, DEFAULT: CURRENT_TIMESTAMP)

### Coupons
- `id` (INTEGER, PRIMARY KEY)
- `coupon_code` (TEXT, UNIQUE, NOT NULL)
- `percentage` (INTEGER, NOT NULL) - Discount percentage
- `max_discount` (DECIMAL, NOT NULL) - Maximum discount amount
- `created_at` (DATETIME, DEFAULT: CURRENT_TIMESTAMP)

## Relationships
- Users can have many Posts, Comments, Likes, Friend Requests, Notifications, Reports, and Marketplace Items
- Posts can have many Comments, Likes, Images, and Reports
- Comments can have many Likes, Reports, and nested Comments (replies)
- Friend Requests create Friendships when accepted

## Security Vulnerabilities (Intentional)
- **Plain text passwords** in Users table
- **No input validation** on most fields
- **SQL injection** vulnerable login system
- **No CSRF protection** on forms
- **No rate limiting** on actions
- **Open redirects** in share functionality
- **IDOR** (Insecure Direct Object Reference) in profile access
- **No coupon expiry validation**
- **No balance validation** in checkout
- **Multiple coupon application** allowed
