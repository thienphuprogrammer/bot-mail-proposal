import os
from dotenv import load_dotenv
from pydantic import BaseSettings

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    
    # App Config
    APP_NAME: str = "Automated Proposal Generation System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False") == "True"
    
    # MongoDB
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "proposal_system")
    
    # Gmail API
    GMAIL_CREDENTIALS_PATH: str = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
    GMAIL_TOKEN_PATH: str = os.getenv("GMAIL_TOKEN_PATH", "token.json")
    GMAIL_SCOPES: list = ["https://www.googleapis.com/auth/gmail.readonly", 
                          "https://www.googleapis.com/auth/gmail.send"]
    
    # OpenAI API
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Azure OpenAI API
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_DEPLOYMENT: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "deepseek-deployment")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
    
    # Use Azure instead of OpenAI
    USE_AZURE_AI: bool = os.getenv("USE_AZURE_AI", "True") == "True"
    
    # JWT Authentication
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # SMTP Settings
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    
    # LangChain Settings
    LANGCHAIN_MODEL: str = os.getenv("LANGCHAIN_MODEL", "gpt-3.5-turbo")
    LANGCHAIN_TEMPERATURE: float = float(os.getenv("LANGCHAIN_TEMPERATURE", "0.7"))
    
    # Proposal Settings
    PROPOSAL_TEMPLATE_PATH: str = os.getenv("PROPOSAL_TEMPLATE_PATH", "templates/proposal_template.html")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create global settings instance
settings = Settings() 