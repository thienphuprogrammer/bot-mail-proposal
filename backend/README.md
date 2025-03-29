# Automated Proposal Generation System

This system automates the generation of business proposals based on incoming customer emails.

## Key Features

- **Email Processing**: Automatically retrieves and processes customer emails
- **AI-Powered Extraction**: Extracts requirements from email content using AI
- **Proposal Generation**: Creates professional proposals based on extracted requirements
- **PDF Generation**: Generates PDF version of the proposal
- **Email Response**: Sends the proposal to the customer
- **Workflow Management**: Tracks the entire process from email receipt to proposal delivery
- **Multiple AI Models**: Supports both OpenAI and Azure OpenAI models
- **Admin Interface**: Simple web interface for managing proposals

## Architecture

The system follows a clean architecture pattern with proper separation of concerns:

- **Models**: Pydantic models for data representation
- **Repositories**: Data access layer for MongoDB
- **Services**: Business logic layer with clear interfaces
- **API**: FastAPI endpoints for frontend integration
- **Prompts**: Organized AI prompt management

## Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and configure the environment variables
6. Set up MongoDB (local or cloud)
7. Set up Gmail API credentials (follow [Google's guide](https://developers.google.com/gmail/api/quickstart/python))
8. Configure OpenAI or Azure OpenAI credentials

## Starting the Application

```bash
uvicorn src.main:app --reload
```

## API Endpoints

- **Authentication**:
  - `POST /token`: Authenticate and get JWT token
  - `POST /users`: Register a new user
  - `GET /users/me`: Get current user information

- **Email Management**:
  - `POST /emails/process`: Process new emails
  - `GET /emails`: List all emails
  - `GET /emails/{email_id}`: Get email details

- **Proposal Management**:
  - `GET /proposals`: List all proposals
  - `GET /proposals/{proposal_id}`: Get proposal details
  - `POST /proposals/{proposal_id}/approve`: Approve a proposal
  - `POST /proposals/{proposal_id}/generate-pdf`: Generate PDF for proposal
  - `POST /proposals/{proposal_id}/send`: Send proposal to customer

- **Workflow**:
  - `GET /workflow/{email_id}`: Get complete workflow information

## Folder Structure

```
src/
├── api/            # API endpoints
├── core/           # Core configuration
├── database/       # Database connections
├── models/         # Pydantic models
├── prompts/        # AI prompts
├── repositories/   # Data access layer
├── services/       # Business logic
│   ├── authentication/  # Authentication services
│   ├── gmail/           # Email services
│   ├── model/           # AI model services
│   └── proposal/        # Proposal processing services
├── utils/          # Utility functions
├── .env.example    # Example environment variables
├── main.py         # FastAPI application entry point
├── streamlit_app.py # Streamlit admin interface
└── requirements.txt # Project dependencies
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b my-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin my-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License. 