# Alma

## Quick Start

```bash
docker-compose up --build
```

## Environment Setup

### Backend (.env)

Create a `.env` file in the `backend` directory with the following content:

```env
# Application Settings
APP_NAME=Alma
APP_ENV=development
DEBUG=True

# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@db:5432/alma

# File Uploads
MAX_FILE_SIZE=5242880  # 5MB in bytes
UPLOAD_DIR=/app/uploads
STORAGE_TYPE=filesystem

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8000

# Email Configuration
SMTP_TLS=True
SMTP_PORT=587
SMTP_HOST=smtp.sendgrid.net
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
EMAILS_ENABLED=False  # Set to True to enable email sending
EMAILS_FROM_EMAIL=noreply@yourdomain.com
EMAILS_FROM_NAME="Alma Team"
ADMIN_EMAIL=admin@yourdomain.com
```

### Frontend (.env)

Create a `.env` file in the `frontend` directory with:

```env
VITE_API_BASE_URL=http://localhost:8000
