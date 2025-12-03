# Contacts REST API

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   Create a `.env` file in the project root. Example:
   ```env
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/contacts_db
   ```

3. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

API docs: http://127.0.0.1:8000/docs
