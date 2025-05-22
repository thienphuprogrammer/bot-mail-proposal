"""
Model service package providing AI-powered functionalities.

This package provides a comprehensive AI system that handles text generation,
requirements extraction, and document generation/improvement using various
AI model providers.

Directory Structure:
- core/: Core interfaces and service orchestration.
- providers/: Model service implementations for different providers.

Example usage:
```python
# Create a model service using the factory
from src.services.model import create_model_service

# Create a default model service (LangChain with GPT-4)
model_service = create_model_service()

# Extract requirements from an email
requirements = model_service.extract_requirements(email_body)

# Generate a proposal
proposal_html = model_service.generate_proposal(requirements)
```
"""

# Export core interfaces
from src.services.model.core.interfaces import (
    AIService,
    TextGenerationService,
    RequirementsExtractionService,
    DocumentGenerationService
)

# Export factory and facade
from src.services.model.core.model_factory import ModelServiceFactory
from src.services.model.core.model_facade import ModelServiceFacade

# Export providers
from src.services.model.providers.azure_service import AzureModelService
from src.services.model.providers.langchain_service import LangChainModelService

# Convenient factory function
def create_model_service(provider: str = "langchain", **kwargs) -> ModelServiceFacade:
    """
    Create a model service with the specified provider.
    
    Args:
        provider: The provider to use ("azure" or "langchain")
        **kwargs: Additional configuration options
        
    Returns:
        A configured ModelServiceFacade
    """
    ai_service = ModelServiceFactory.create_model_service(provider, **kwargs)
    return ModelServiceFacade(ai_service)
