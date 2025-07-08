# VulnBook Database Schema

This document describes the database schema for the VulnBook vulnerable social networking application.

## Database Tables

### Users Table
Stores user account information.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,  -- Intentionally stored as plain text (vulnerability)
    bio TEXT,
    image_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Vulnerabilities:**
- Passwords stored in plain text
- No password complexity requirements
- No email verification

### Posts Table
Stores user posts/status updates.

```sql
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    hashtags TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Comments Table
Stores comments on posts.

```sql
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Post Images Table
Stores images associated with posts.

```sql
CREATE TABLE post_images (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL
);
```

### Post Likes Table
Stores likes on posts.

```sql
CREATE TABLE post_likes (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
);
```

**Vulnerabilities:**
- No unique constraint on (post_id, user_id) - allows multiple likes from same user
- Uses raw SQL inserts without parameterized queries

### Comment Likes Table
Stores likes on comments.

```sql
CREATE TABLE comment_likes (
    id SERIAL PRIMARY KEY,
    comment_id INTEGER REFERENCES comments(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
);
```

### Friend Requests Table
Stores friend requests between users.

```sql
CREATE TABLE friend_requests (
    id SERIAL PRIMARY KEY,
    from_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    to_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, accepted, rejected
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Friendships Table
Stores accepted friendships (bidirectional).

```sql
CREATE TABLE friendships (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    friend_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Notifications Table
Stores user notifications.

```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Reports Table
Stores user reports for posts and comments.

```sql
CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    comment_id INTEGER REFERENCES comments(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Marketplace Items Table
Stores items for sale in the marketplace.

```sql
CREATE TABLE marketplace_items (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    image_url VARCHAR(255),
    review TEXT,
    approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Coupons Table
Stores discount coupons.

```sql
CREATE TABLE coupons (
    id SERIAL PRIMARY KEY,
    coupon_code VARCHAR(50) UNIQUE NOT NULL,
    percentage INTEGER NOT NULL,
    max_discount DECIMAL(10,2) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    expiry_date TIMESTAMP NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Relationships

### One-to-Many Relationships
- **Users → Posts**: A user can have many posts
- **Users → Comments**: A user can have many comments
- **Posts → Comments**: A post can have many comments
- **Posts → Post Images**: A post can have many images
- **Posts → Post Likes**: A post can have many likes
- **Comments → Comment Likes**: A comment can have many likes
- **Users → Friend Requests (from)**: A user can send many friend requests
- **Users → Friend Requests (to)**: A user can receive many friend requests
- **Users → Notifications**: A user can have many notifications
- **Users → Reports**: A user can make many reports
- **Posts → Reports**: A post can be reported many times
- **Comments → Reports**: A comment can be reported many times
- **Users → Marketplace Items**: A user can sell many items
- **Users → Friendships**: A user can have many friendships

### Many-to-Many Relationships
- **Users ↔ Users (Friends)**: Implemented through the Friendships table
- **Users ↔ Posts (Likes)**: Implemented through the Post Likes table
- **Users ↔ Comments (Likes)**: Implemented through the Comment Likes table

## Security Vulnerabilities (Intentional)

### Authentication & Authorization
1. **Plain Text Passwords**: All passwords stored without hashing
2. **Weak JWT Secret**: Uses a hardcoded weak secret
3. **No Session Management**: Basic session handling with vulnerabilities
4. **No Rate Limiting**: No protection against brute force attacks

### SQL Injection
1. **Login Form**: Uses raw SQL with string concatenation
2. **Like Functionality**: Direct SQL execution without parameterized queries
3. **Search Functions**: Potential SQL injection in search queries

### Insecure Direct Object References (IDOR)
1. **Profile Pages**: Access any user's profile by changing ID in URL
2. **Post Access**: No authorization checks on post access
3. **Friend Requests**: Can manipulate friend request IDs

### Cross-Site Scripting (XSS)
1. **Post Content**: No input sanitization on user posts
2. **Comments**: Comments not properly escaped
3. **Profile Information**: Bio and other fields vulnerable to XSS

### Business Logic Vulnerabilities
1. **Multiple Likes**: Users can like the same post multiple times
2. **Coupon Abuse**: 
   - No expiry date validation
   - No maximum discount enforcement
   - Can apply multiple coupons
   - No balance validation
3. **Marketplace**: Items can be purchased with negative balance

### File Upload Vulnerabilities
1. **Image Uploads**: No file type validation
2. **Directory Traversal**: No path sanitization
3. **File Size Limits**: No proper file size restrictions

### Open Redirect
1. **Share Functionality**: Redirects to any URL without validation

## Demo Data

The `database_setup.py` script creates the following demo data:

### Users
- **admin** (admin@vulnbook.com) - Password: admin123
- **alice** (alice@example.com) - Password: password123
- **bob** (bob@example.com) - Password: qwerty
- **charlie** (charlie@example.com) - Password: 123456
- **diana** (diana@example.com) - Password: password
- **eve** (eve@example.com) - Password: letmein

### Sample Posts
- Welcome post from admin
- Technology-related posts from various users
- Posts with hashtags for testing search functionality
- Posts with potential XSS payloads

### Sample Marketplace Items
- Various digital products (courses, tools, templates)
- Mix of approved and pending items
- Different price ranges for testing

### Sample Coupons
- **WELCOME10** - 10% discount
- **SAVE20** - 20% discount
- **STUDENT50** - 50% discount
- **EXPIRED** - Expired coupon for testing
- **FREEBIE** - 100% discount (for testing vulnerabilities)

## Setup Instructions

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Up Database**:
   ```bash
   python database_setup.py
   ```

3. **Choose Setup Option**:
   - Option 1: Create tables only
   - Option 2: Create tables and populate with demo data
   - Option 3: Reset database (drop all and recreate)
   - Option 4: Add demo data to existing database

4. **Run Application**:
   ```bash
   python run.py
   ```

## Admin Panel Access

- URL: `/admin`
- Username: `admin`
- Password: `admin123`

The admin panel provides access to:
- User management (view/delete users)
- Content moderation (view reports)
- Marketplace management (approve/reject items)
- Coupon management (create coupons)

## Testing Vulnerabilities

This application is intentionally vulnerable for security testing and educational purposes. Some example attacks to test:

1. **SQL Injection**: Try `' OR '1'='1'--` in the login form
2. **XSS**: Post content with `<script>alert('XSS')</script>`
3. **IDOR**: Change user IDs in URLs to access other profiles
4. **Coupon Abuse**: Use expired coupons or apply multiple coupons
5. **File Upload**: Upload malicious files through profile image upload

**⚠️ WARNING**: This application contains intentional security vulnerabilities and should only be used in isolated testing environments. Never deploy this application in production or on public networks.
