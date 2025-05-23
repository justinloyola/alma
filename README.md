# Alma

```bash
docker-compose up --build
```
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
