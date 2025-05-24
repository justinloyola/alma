# Alma

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/alma.git
   cd alma
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   Then edit the `.env` file with your configuration.

3. Start the application:
   ```bash
   docker-compose up --build
   ```

4. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Email Configuration
SENDGRID_API_KEY=your_sendgrid_api_key_here
FROM_EMAIL=your_verified_sendgrid_email@example.com  # Must be a verified sender in SendGrid
ADMIN_EMAIL=admin@example.com

# Database Configuration (SQLite by default)
DATABASE_URL=sqlite:////app/alma.db

# Security
SECRET_KEY=change-this-to-a-secure-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours

# Application Settings
APP_NAME=Alma
APP_ENV=development
DEBUG=True

# File Uploads
MAX_FILE_SIZE=5242880  # 5MB
UPLOAD_DIR=./uploads
STORAGE_TYPE=filesystem

# CORS (comma-separated list of allowed origins)
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# Email Server Configuration
SMTP_TLS=True
SMTP_PORT=587
SMTP_HOST=smtp.sendgrid.net
SMTP_USER=apikey
# SMTP_PASSWORD is set to SENDGRID_API_KEY by default

# Frontend URL (used for email links)
FRONTEND_URL=http://localhost:3000
```

## Project Structure

- `backend/` - FastAPI backend application
- `frontend/` - React frontend application
- `docker-compose.yml` - Docker Compose configuration
- `.env.example` - Example environment configuration

## Development

### Running Tests

```bash
docker-compose run --rm backend pytest
```

### Database Migrations

```bash
docker-compose run --rm backend alembic revision --autogenerate -m "Your migration message"
docker-compose run --rm backend alembic upgrade head
```

## Production Deployment

For production, make sure to:
1. Set `APP_ENV=production`
2. Set `DEBUG=False`
3. Use a proper database (PostgreSQL/MySQL) instead of SQLite
4. Set up proper SSL/TLS certificates
5. Configure proper CORS origins
6. Use a secure `SECRET_KEY`
