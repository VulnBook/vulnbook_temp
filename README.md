# VulnBook - Intentionally Vulnerable Social Network

VulnBook is a social networking application intentionally designed with security vulnerabilities for educational and testing purposes. It includes features like user registration, posts, comments, friend requests, marketplace, and more.

## ⚠️ Security Warning

**This application contains intentional security vulnerabilities and should NEVER be deployed in production!** It is designed for:
- Security education and training
- Penetration testing practice
- Vulnerability assessment learning
- Security research

## Features

### Core Social Features
- User registration and login (with plain-text password storage)
- Profile management with bio and image upload
- Create posts with media attachments and hashtags
- Comment system with nested replies
- Like system for posts and comments
- Friend request system
- Real-time notifications
- Search functionality for posts and users

### Marketplace & E-commerce
- Users can list items for sale
- Admin approval system for marketplace items
- Shopping cart functionality
- Coupon system with discount codes
- Virtual balance system (VulnCash)
- Checkout and payment processing

### Admin Panel
- User management (view/delete users)
- Content moderation (view reports)
- Marketplace item approval/rejection
- Coupon management

## Intentional Vulnerabilities

- **Plain-text password storage**
- **SQL Injection** in login system
- **Cross-Site Scripting (XSS)** in posts and comments
- **Insecure Direct Object Reference (IDOR)** in profiles
- **Open Redirect** in share functionality
- **No CSRF protection**
- **No input validation**
- **No rate limiting**
- **Coupon system vulnerabilities** (multiple applications, no expiry check)
- **Balance bypass** in checkout
- **File upload vulnerabilities**

## Installation & Setup

### Prerequisites
- Python 3.8+
- PostgreSQL (recommended) or SQLite for development
- Virtual environment (recommended)

### Quick Start

### Installation

To quickly set up the VulnBook application, you can use Docker or run it locally without Docker.

1. **Clone the repository**:
   ```bash
   git clone https://github.com/VulnBook/vulnbook_temp.git
   cd vulnbook_temp
   ```

2. **Docker Setup (Optional)**:
   If you prefer using Docker, you can set up the application with Docker Compose:
   ```bash
   docker-compose up -d --build
   ```

This will build the Docker images and start the application along with the database.
Now go to `http://localhost:5000` to access the application. If any error occurs, check the logs with:
   ```bash
    docker logs vulnbook_flask # Check logs for the Flask app
    docker logs vulnbook_postgres    # Check logs for the database
   ```

Or, if you want to run it without Docker, follow the steps below.


1. **Clone the repository**:
   ```bash
   git clone https://github.com/VulnBook/vulnbook_temp.git
   cd vulnbook_temp
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database**:
   ```bash
   python database_setup.py
   ```
   
   Choose option 2 to create tables and populate with demo data.

5. **Run the application**:
   ```bash
   python run.py
   ```

6. **Access the application**:
   - Main app: http://localhost:5000
   - Admin panel: http://localhost:5000/admin

### Demo Login Credentials

**Regular Users:**
- Username: `alice`, Password: `password123`
- Username: `bob`, Password: `qwerty`
- Username: `charlie`, Password: `123456`
- Username: `diana`, Password: `password`
- Username: `eve`, Password: `letmein`

**Admin Access:**
- Username: `admin`, Password: `admin123`

### Demo Coupons
- `WELCOME10` - 10% discount
- `SAVE20` - 20% discount
- `STUDENT50` - 50% discount
- `FREEBIE` - 100% discount (for testing vulnerabilities)

## Database Schema

See [SCHEMA.md](SCHEMA.md) for detailed database schema documentation, including:
- Table structures and relationships
- Security vulnerabilities in each component
- Demo data descriptions
- Testing scenarios

## Project Structure

```
VulnBook/
├── app/
│   ├── __init__.py
│   ├── models.py          # Database models
│   ├── routes.py          # Application routes
│   ├── db.py             # Database configuration
│   ├── static/           # CSS, JS, images
│   └── templates/        # HTML templates
├── ├── database_setup.py     # Database setup script
├── ├── db_reset.py          # Database reset utility
├── run.py               # Application entry point
├── requirements.txt     # Python dependencies
├── docker-compose.yml   # Docker configuration
├── README.md           # This file
└── SCHEMA.md          # Database schema documentation
```

## Contributing

This project is designed for educational purposes. When contributing:

1. **Maintain vulnerabilities**: Don't fix the intentional security issues
2. **Document new vulnerabilities**: Add any new vulnerabilities to the documentation
3. **Test thoroughly**: Ensure all features work as expected
4. **Update documentation**: Keep README and SCHEMA.md up to date

### Setting Up Development Environment

1. Fork the repository
2. Create a new branch for your feature
3. Follow the installation steps above
4. Make your changes
5. Test with the demo data
6. Submit a pull request

## Security Testing Examples

### SQL Injection
Try logging in with:
- Username: `' OR '1'='1'--`
- Password: `anything`

### XSS (Cross-Site Scripting)
Create a post with:
```html
<script>alert('XSS vulnerability!')</script>
```

### IDOR (Insecure Direct Object Reference)
- Log in as any user
- Change the user ID in the URL: `/profile/1`, `/profile/2`, etc.

### Coupon Abuse
- Use expired coupons
- Apply multiple coupons: `WELCOME10,SAVE20,STUDENT50`
- Use `FREEBIE` coupon for 100% discount

### File Upload
- Upload files with dangerous extensions
- Test directory traversal in file names

## Troubleshooting

### Database Issues
If you encounter database errors:
```bash
python database_setup.py
# Choose option 3 to reset the database
```

### Missing Dependencies
```bash
pip install -r requirements.txt
```

### Port Already in Use
Change the port in `run.py`:
```python
app.run(debug=True, port=5001)
```

## License

This project is for educational purposes only. See LICENSE file for details.

## Disclaimer

This application is intentionally vulnerable and should never be used in production environments. The developers are not responsible for any misuse of this application.
