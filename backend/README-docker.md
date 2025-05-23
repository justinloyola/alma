# Alma Backend - Docker Setup

This guide explains how to set up and run the Alma backend using Docker.

## Prerequisites

- Docker (version 20.10.0 or higher)
- Docker Compose (version 1.29.0 or higher)
- Make (optional, but recommended for convenience)

## Quick Start

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone <repository-url>
   cd alma/backend
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   Then edit the `.env` file with your configuration.

3. **Build and start the services**:
   ```bash
   docker-compose up --build -d
   ```

4. **Access the application**:
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - pgAdmin: http://localhost:5050 (email: admin@example.com, password: admin)

## Available Commands

### Start services
```bash
docker-compose up -d
```

### Stop services
```bash
docker-compose down
```

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
```

### Run database migrations
```bash
docker-compose exec backend alembic upgrade head
```

### Create a superuser
```bash
docker-compose exec backend python -m app.initial_data
```

### Run tests
```bash
docker-compose exec backend pytest
```

## Environment Variables

Copy `.env.example` to `.env` and update the values as needed. The main variables are:

- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: Secret key for JWT token generation
- `EMAILS_ENABLED`: Set to `True` to enable email notifications
- `SMTP_*`: SMTP server configuration for sending emails
- `ADMIN_EMAIL`: Admin email for notifications
- `CORS_ORIGINS`: Allowed origins for CORS

## Volumes

- PostgreSQL data is persisted in a Docker volume named `alma_backend_postgres_data`
- pgAdmin data is persisted in a Docker volume named `alma_backend_pgadmin_data`
- Uploads are stored in the `./uploads` directory (mounted to `/app/uploads` in the container)

## Troubleshooting

### Database Connection Issues
If the backend can't connect to the database, make sure:
1. The database service is running (`docker-compose ps`)
2. The `DATABASE_URL` in `.env` matches the service name (`db`)
3. The database credentials match those in the `docker-compose.yml`

### Port Conflicts
If you get port conflicts, either:
1. Stop the conflicting service, or
2. Update the port mappings in `docker-compose.yml`

### Rebuilding Containers
If you make changes to the `Dockerfile` or dependencies:
```bash
docker-compose up --build -d
```

## Production Deployment

For production, you should:
1. Set `DEBUG=False` in `.env`
2. Use a proper database (not SQLite)
3. Set up proper SSL/TLS
4. Configure proper logging and monitoring
5. Set up backups for the database
6. Use environment-specific configuration files

## License

[Your License Here]
