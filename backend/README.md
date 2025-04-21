# Bot Mail Proposal System Backend

A FastAPI-based backend for automatically generating and sending proposals based on email inquiries.

## Features

- Email synchronization with Gmail
- Automated proposal generation from emails
- User authentication with JWT
- Proposal management

## Project Structure

```
backend/
├── src/                     # Source code
│   ├── api/                 # API endpoints
│   │   └── v1/              # API version 1
│   │       ├── auth/        # Authentication routes
│   │       ├── emails/      # Email management routes
│   │       └── proposals/   # Proposal management routes
│   ├── core/                # Core modules (config, constants)
│   ├── database/            # Database connections
│   ├── models/              # Pydantic models
│   ├── services/            # Business logic services
│   └── utils/               # Utility functions
├── templates/               # Email templates
├── scripts/                 # Utility scripts
├── logs/                    # Application logs
├── data/                    # Application data
├── credentials/             # Auth credentials (Gmail API, etc.)
├── run.py                   # Main entry point
├── requirements.txt         # Python dependencies
└── .env.example             # Example environment variables
```

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and update with your settings:
   ```
   cp .env.example .env
   ```
5. Set up the application environment:
   ```
   python run.py setup
   ```
   
## Running the Application

### API Server

```
python run.py api
```

The API will be available at http://localhost:8000

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

### Adding a New Route

1. Create your route file in the appropriate API module
2. Import and register the router in `src/api/v1/router.py`

### Database Migrations

MongoDB doesn't require formal migrations, but index updates are defined in `src/database/mongodb.py`.

## Code Optimization

The codebase has been optimized for clarity and maintainability:

1. **Base Repository**
   - Improved error handling with specific exception types
   - Added comprehensive logging
   - Enhanced type hints and documentation
   - Better null checks and validation

2. **PDF Renderer Service**
   - Extracted constants and configuration to module level
   - Improved component separation with smaller, focused methods
   - Enhanced error handling with fallbacks
   - Added input validation and better logging
   - Optimized markdown processing

3. **Code Style**
   - Consistent docstrings with Args/Returns sections
   - Improved method and parameter naming
   - Better folder structure with Path objects
   - More comprehensive error reporting

## API Structure

### Authentication

- POST `/api/v1/auth/token` - Get JWT token
- POST `/api/v1/auth/register` - Register new user
- GET `/api/v1/auth/me` - Get current user info

### Emails

- GET `/api/v1/emails/` - List all emails
- GET `/api/v1/emails/{email_id}` - Get specific email
- POST `/api/v1/emails/sync` - Sync emails from Gmail
- POST `/api/v1/emails/process/{email_id}` - Process an email into a proposal

### Proposals

- GET `/api/v1/proposals/` - List all proposals
- GET `/api/v1/proposals/{proposal_id}` - Get specific proposal
- POST `/api/v1/proposals/` - Create new proposal
- PUT `/api/v1/proposals/{proposal_id}` - Update proposal
- POST `/api/v1/proposals/{proposal_id}/send` - Send proposal to client 