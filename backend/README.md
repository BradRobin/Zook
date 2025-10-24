# Zook Authentication Server (FastAPI)

Python/FastAPI-based authentication and session management server for the Zook AI surveillance platform.

## Features

- **User Registration** (`POST /api/auth`)
- **User Login** (`POST /api/login`) with JWT tokens
- **Session Management** - Track active sessions with device information
- **Stream Validation** (`POST /api/stream/validate`) for MediaMTX integration
- **Token Verification** (`GET /api/verify`)
- **Secure Password Hashing** - bcrypt with 12 rounds
- **PostgreSQL Database** - Async SQLAlchemy with proper relationships
- **CORS Support** - Configurable origins
- **HTTPS Redirect** - Production-ready security

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Or use a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the `backend/` directory:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/zook
JWT_SECRET_KEY=your-secret-key-here-generate-with-openssl-rand-hex-32
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
CORS_ORIGINS=http://localhost:3500,http://localhost:3000
ENVIRONMENT=development
```

**Generate a secure JWT secret key:**
```bash
openssl rand -hex 32
```

### 3. Setup Database

Make sure PostgreSQL is running, then create the database:

```bash
psql -U postgres
CREATE DATABASE zook;
\q
```

Run the migration script:

```bash
psql -U postgres -d zook -f migrations/init.sql
```

### 4. Start the Server

```bash
# Development mode (auto-reload)
uvicorn app.main:app --reload --port 8000

# Or using Python directly
python -m app.main

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Server will start on: `http://localhost:8000`

### 5. Test the API

Visit the interactive API docs:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Authentication

#### Register User
```http
POST /api/auth
Content-Type: application/json

{
  "username": "john_doe",
  "password": "securepass123"
}
```

#### Login
```http
POST /api/login
Content-Type: application/json

{
  "username": "john_doe",
  "password": "securepass123"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "session_id": "uuid-here",
  "username": "john_doe",
  "expires_in": 86400
}
```

#### Verify Token
```http
GET /api/verify
Authorization: Bearer <your-jwt-token>

Response:
{
  "id": "uuid",
  "username": "john_doe",
  "created_at": "2025-10-24T...",
  "last_login": "2025-10-24T..."
}
```

#### Logout
```http
POST /api/logout
Authorization: Bearer <your-jwt-token>

Response:
{
  "message": "Logged out successfully"
}
```

### Stream Validation (MediaMTX)

#### Validate Stream Access
```http
POST /api/stream/validate
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
  "action": "read",
  "protocol": "webrtc",
  "path": "/mystream"
}

Response:
{
  "authorized": true,
  "user_id": "uuid",
  "username": "john_doe",
  "message": "Stream access granted"
}
```

## Database Schema

### Users Table
- `id` - UUID primary key
- `username` - Unique username
- `password_hash` - bcrypt hashed password
- `created_at` - Registration timestamp
- `last_login` - Last login timestamp

### Sessions Table
- `id` - UUID primary key
- `user_id` - Foreign key to users
- `session_token` - JWT token
- `created_at` - Session creation time
- `expires_at` - Expiration time
- `is_active` - Active status
- `ip_address` - Client IP
- `user_agent` - Browser/client info
- `last_activity` - Last activity timestamp
- `device_info` - Additional device metadata

## Security Features

1. **Password Hashing**: bcrypt with 12 rounds (4096 iterations)
2. **JWT Tokens**: HS256 algorithm with 24-hour expiry
3. **Session Tracking**: Active session management with device info
4. **CORS Protection**: Configurable allowed origins
5. **HTTPS Redirect**: Automatic redirect in production
6. **Input Validation**: Pydantic schemas for all requests
7. **SQL Injection Protection**: SQLAlchemy parameterized queries

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Environment configuration
│   ├── database.py          # Database connection setup
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── auth.py              # JWT utilities
│   ├── security.py          # Password hashing
│   └── routers/
│       ├── __init__.py
│       ├── auth_routes.py   # Authentication endpoints
│       └── stream_routes.py # Stream validation endpoints
├── migrations/
│   └── init.sql             # Database schema
├── requirements.txt
├── .env.example
└── README.md
```

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Code Formatting
```bash
pip install black isort
black app/
isort app/
```

### Type Checking
```bash
pip install mypy
mypy app/
```

## Deployment

### Docker (Recommended)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables for Production
- Set `ENVIRONMENT=production`
- Use strong `JWT_SECRET_KEY`
- Configure proper `CORS_ORIGINS`
- Use connection pooling for database
- Enable HTTPS

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running
- Check `DATABASE_URL` format
- Verify database exists: `psql -U postgres -l`

### Token Validation Errors
- Check JWT_SECRET_KEY matches between sessions
- Verify token hasn't expired (24 hours)
- Ensure proper Authorization header: `Bearer <token>`

### CORS Errors
- Add frontend URL to `CORS_ORIGINS` in `.env`
- Check browser console for specific CORS error

## License

Part of the Zook project - Open-source foundation

## Contact

For issues and questions, refer to the main Zook project documentation.


