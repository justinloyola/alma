# Alma

A modern web application with a FastAPI backend and React + TypeScript frontend.

## Project Structure

```
alma/
├── backend/           # FastAPI backend
│   ├── app/          # Application package
│   │   ├── api/      # API routes
│   │   ├── core/     # Core functionality
│   │   └── main.py   # Main application
│   ├── tests/        # Backend tests
│   └── requirements/
│       ├── base.txt  # Main dependencies
│       └── dev.txt   # Development dependencies
├── frontend/         # React + TypeScript frontend
│   ├── public/       # Static files
│   ├── src/          # Source code
│   ├── .env.example  # Example environment variables
│   ├── index.html    # Main HTML file
│   ├── package.json  # Frontend dependencies
│   ├── tsconfig.json # TypeScript configuration
│   └── vite.config.ts # Vite configuration
├── .gitignore        # Git ignore file
└── README.md         # Project documentation
```

## Backend Setup

### Prerequisites

- Python 3.8+
- uv (https://github.com/astral-sh/uv)

### Installation

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   uv venv
   .venv\Scripts\activate  # On Windows
   source .venv/bin/activate  # On Unix/macOS
   ```

3. Install dependencies:
   ```bash
   uv pip install -r requirements/dev.txt
   ```

### Running the Backend

```bash
# From the backend directory
python run.py
```

The API will be available at http://localhost:8000

### API Documentation

- Interactive API docs: http://localhost:8000/docs
- Alternative API docs: http://localhost:8000/redoc

### Running Tests

```bash
pytest
```

## Frontend Setup

### Prerequisites

- Node.js 18+ and npm 8+

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Create a `.env` file:
   ```bash
   cp .env.example .env
   ```
   
   Update the `.env` file with your backend URL if needed.

3. Install dependencies:
   ```bash
   npm install
   # or
   yarn
   ```

### Running the Frontend

For development:
```bash
# From the frontend directory
npm run dev
# or
yarn dev
```

The frontend will be available at http://localhost:5173 and will automatically proxy API requests to the backend.

### Building for Production

```bash
# Build the frontend
npm run build

# Preview the production build
npm run preview
```

## Development Workflow

1. Start the backend server in one terminal:
   ```bash
   cd backend
   python run.py
   ```

2. In another terminal, start the frontend development server:
   ```bash
   cd frontend
   npm run dev
   ```

3. Access the application at http://localhost:5173

## Environment Variables

### Backend

Backend environment variables can be set in a `.env` file in the `backend` directory.

### Frontend

Frontend environment variables should be prefixed with `VITE_` and can be set in the `.env` file in the `frontend` directory. See `.env.example` for reference.

## Testing

### Backend Tests

```bash
# From the backend directory
pytest
```

### Frontend Tests

```bash
# From the frontend directory
npm test
# or
yarn test
```

## Deployment

Coming soon...
