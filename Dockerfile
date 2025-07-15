# # Use Python 3.9 slim base image for smaller size
# FROM python:3.12-slim

# # Set working directory
# WORKDIR /app

# # Copy requirements file (if you have one) and install dependencies
# COPY requirements.txt .
# # RUN pip install --no-cache-dir -r requirements.txt
# RUN pip install -r requirements.txt

# # Copy the entire application code
# COPY . .

# # Expose port 5000 for Flask app
# EXPOSE 5000

# # Set environment variables
# ENV FLASK_APP=run.py
# ENV FLASK_ENV=production

# # Command to run the Flask app
# CMD ["flask", "run"]

# Use Python 3.12 slim base image for smaller size
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code
COPY . .

# Expose port 5000 for Flask app
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=run.py
ENV FLASK_ENV=production

# Command to run the Flask app, binding to 0.0.0.0 for external access
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]