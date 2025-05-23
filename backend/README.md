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
├── api/              # API routes
├── core/             # Core functionality
├── db/               # Database models and migrations
├── models/           # Pydantic models
└── main.py           # Application entry point
```
