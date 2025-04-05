import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings."""
    
    # App Config
    APP_NAME: str = "Bot Mail Proposal System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False") == "True"
    
    # MongoDB
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "bot_mail_proposal")
    
    # Gmail API
    GMAIL_CREDENTIALS_PATH: str = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials/credentials.json")
    GMAIL_TOKEN_PATH: str = os.getenv("GMAIL_TOKEN_PATH", "credentials/token.json")
    GMAIL_SCOPES: list = ["https://www.googleapis.com/auth/gmail.readonly", 
                          "https://www.googleapis.com/auth/gmail.send"]

    # Outlook API
    OUTLOOK_TENANT_ID: str = os.getenv("OUTLOOK_TENANT_ID", "")
    OUTLOOK_CLIENT_ID: str = os.getenv("OUTLOOK_CLIENT_ID", "")
    OUTLOOK_CLIENT_SECRET: str = os.getenv("OUTLOOK_CLIENT_SECRET", "")
    OUTLOOK_USER_ID: str = os.getenv("OUTLOOK_USER_ID", "")
    OUTLOOK_AUTHORIZATION_URL: str = os.getenv("OUTLOOK_AUTHORIZATION_URL", "https://login.microsoftonline.com/common/oauth2/v2.0/authorize")
    OUTLOOK_AUTHORIZATION_KEY: str = os.getenv("OUTLOOK_AUTHORIZATION_KEY", "")
    # OpenAI API
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Azure OpenAI API (if applicable)
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_DEPLOYMENT: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
    OUTLOOK_TOKEN_PATH: str = os.getenv("OUTLOOK_TOKEN_PATH", "credentials/outlook_token.txt")
    
    # Use Azure instead of OpenAI
    USE_AZURE_AI: bool = os.getenv("USE_AZURE_AI", "False") == "True"
    
    # JWT Authentication
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # SMTP Settings (if not using Gmail API)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    
    # Security Settings
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")
    HASH_PASSWORD_KEY: str = os.getenv("HASH_PASSWORD_KEY", "")
    
    # LangChain Settings
    LANGCHAIN_MODEL: str = os.getenv("LANGCHAIN_MODEL", "gpt-3.5-turbo")
    LANGCHAIN_TEMPERATURE: float = float(os.getenv("LANGCHAIN_TEMPERATURE", "0.7"))
    
    # Email Processing Settings
    EMAIL_FETCH_LIMIT: int = int(os.getenv("EMAIL_FETCH_LIMIT", "10"))
    EMAIL_PROCESSING_INTERVAL: int = int(os.getenv("EMAIL_PROCESSING_INTERVAL", "60"))  # seconds
    
    # Template Settings
    EMAIL_TEMPLATE_PATH: str = os.getenv("EMAIL_TEMPLATE_PATH", "templates/email_template.html")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create global settings instance
settings = Settings() 