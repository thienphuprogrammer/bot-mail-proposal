"""
Factory for creating model service components.
"""

import logging
from typing import Optional, Dict, Any

from services.model.core.interfaces import AIService
from services.model.providers.azure_service import AzureModelService
from services.model.providers.langchain_service import LangChainModelService

logger = logging.getLogger(__name__)

class ModelServiceFactory:
    """Factory for creating and configuring model service components."""
    
    @staticmethod
    def create_azure_model_service(api_key: Optional[str] = None, 
                                  endpoint: Optional[str] = None) -> AIService:
        """
        Create and configure an Azure model service.
        
        Args:
            api_key: Optional API key for Azure
            endpoint: Optional endpoint URL for Azure
            
        Returns:
            An instance of AIService implemented by AzureModelService
        """
        logger.info("Creating Azure model service")
        service = AzureModelService(api_key=api_key, endpoint=endpoint)
        return service
    
    @staticmethod
    def create_langchain_model_service(model_name: str = "gpt-4",
                                      api_key: Optional[str] = None) -> AIService:
        """
        Create and configure a LangChain model service.
        
        Args:
            model_name: Name of the LLM model to use
            api_key: Optional API key for the model provider
            
        Returns:
            An instance of AIService implemented by LangChainModelService
        """
        logger.info(f"Creating LangChain model service with model: {model_name}")
        service = LangChainModelService(model_name=model_name, api_key=api_key)
        return service
    
    @staticmethod
    def create_model_service(provider: str = "langchain", **kwargs) -> AIService:
        """
        Create a model service based on the specified provider.
        
        Args:
            provider: The provider to use ("azure" or "langchain")
            **kwargs: Additional configuration options to pass to the provider
            
        Returns:
            An instance of AIService
            
        Raises:
            ValueError: If the provider is not supported
        """
        logger.info(f"Creating model service with provider: {provider}")
        
        if provider.lower() == "azure":
            return ModelServiceFactory.create_azure_model_service(**kwargs)
        elif provider.lower() == "langchain":
            return ModelServiceFactory.create_langchain_model_service(**kwargs)
        else:
            raise ValueError(f"Unsupported model provider: {provider}")
    
    @staticmethod
    def create_default_model_service() -> AIService:
        """
        Create a default model service with recommended settings.
        
        Returns:
            An instance of AIService
        """
        logger.info("Creating default model service (LangChain with GPT-4)")
        return ModelServiceFactory.create_langchain_model_service(model_name="gpt-4") 