# Contacts REST API

## Quick Start

1. Clone the repository and navigate to the project folder.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root (or use `.env.example` as a template) and fill in your environment variables.
4. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Documentation

Swagger UI: http://127.0.0.1:8000/docs

## Docker (optional)

To run with Docker Compose:
```bash
docker-compose up --build
```

This will start both the server and a PostgreSQL database.
