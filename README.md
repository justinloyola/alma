# Alma

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/justinloyola/alma.git
   cd alma
   ```

2. Set up environment variables
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
   - API Documentation: http://localhost:8000/api/docs

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Email Configuration
SENDGRID_API_KEY=your_sendgrid_api_key_here
FROM_EMAIL=your_verified_sendgrid_email@example.com  # Must be a verified sender in SendGrid
ADMIN_EMAIL=admin@example.com
```

## Project Structure

- `backend/` - FastAPI backend application
- `frontend/` - React frontend application
- `docker-compose.yml` - Docker Compose configuration
- `.env.example` - Example environment configuration
