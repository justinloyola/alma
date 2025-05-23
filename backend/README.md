# Alma Backend

This is the backend service for the Alma application, built with FastAPI.

## Development

### Setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   uv pip install -e .
   ```

3. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

## Project Structure

```
app/
├── api/              # API routes and endpoints
├── core/             # Core functionality and utilities
├── db/               # Database models and migrations
├── models/           # Pydantic models and schemas
├── repositories/     # Data access layer (database interactions)
├── services/        # Business logic and service layer
└── main.py           # Application entry point
```

### Directory Descriptions

- **api/**: Contains all API route definitions and request/response handling
- **core/**: Houses core application functionality, utilities, and configurations
- **db/**: Database models, migrations, and database connection setup
- **models/**: Pydantic models for request/response validation and data serialization
- **repositories/**: Data access layer that handles all database operations
- **services/**: Business logic layer that processes data between API and repositories

### Data Flow

1. **API Layer**: Receives HTTP requests and validates input using Pydantic models
2. **Service Layer**: Contains business logic and orchestrates operations
3. **Repository Layer**: Handles all database operations and data access
4. **Database**: Stores and retrieves data as requested by the repositories
