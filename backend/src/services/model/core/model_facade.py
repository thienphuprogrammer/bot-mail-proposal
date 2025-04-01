"""
Facade for the model service providing a simplified interface.
"""

import logging
from typing import Dict, Any, Optional, List

from services.model.core.interfaces import AIService, TextGenerationService, RequirementsExtractionService, DocumentGenerationService

logger = logging.getLogger(__name__)

class ModelServiceFacade:
    """
    Facade for interacting with AI model services.
    
    This class provides a simplified interface for working with various AI services,
    including text generation, requirements extraction, and document generation.
    
    It delegates specific tasks to the appropriate service components.
    """
    
    def __init__(self, 
                 ai_service: AIService,
                 text_generation_service: Optional[TextGenerationService] = None,
                 requirements_extraction_service: Optional[RequirementsExtractionService] = None,
                 document_generation_service: Optional[DocumentGenerationService] = None):
        """
        Initialize the model service facade.
        
        Args:
            ai_service: Core AI service for general operations
            text_generation_service: Optional specialized service for text generation
            requirements_extraction_service: Optional specialized service for requirements extraction
            document_generation_service: Optional specialized service for document generation
        """
        self.ai_service = ai_service
        self.text_generation_service = text_generation_service or ai_service
        self.requirements_extraction_service = requirements_extraction_service or ai_service
        self.document_generation_service = document_generation_service or ai_service
        
        logger.info("Model service facade initialized")
    
    def generate_text(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> Optional[str]:
        """
        Generate text based on a prompt.
        
        Args:
            prompt: Text prompt to generate from
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated text or None if generation failed
        """
        logger.info(f"Generating text, max_tokens={max_tokens}, temp={temperature}")
        return self.text_generation_service.generate_text(prompt, max_tokens, temperature)
    
    def complete_text(self, text: str, max_tokens: int = 500, temperature: float = 0.7) -> Optional[str]:
        """
        Complete the given text.
        
        Args:
            text: Text to complete
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Completed text or None if completion failed
        """
        logger.info(f"Completing text, max_tokens={max_tokens}")
        return self.text_generation_service.complete_text(text, max_tokens, temperature)
    
    def generate_chat_response(self, conversation: List[Dict[str, str]], temperature: float = 0.7) -> Optional[str]:
        """
        Generate a response to a chat conversation.
        
        Args:
            conversation: List of conversation messages with 'role' and 'content'
            temperature: Sampling temperature
            
        Returns:
            Response text or None if generation failed
        """
        logger.info(f"Generating chat response, conversation length={len(conversation)}")
        return self.text_generation_service.generate_chat_response(conversation, temperature)
    
    def extract_requirements(self, email_body: str) -> Optional[Dict[str, Any]]:
        """
        Extract project requirements from an email.
        
        Args:
            email_body: Body of the email to analyze
            
        Returns:
            Dictionary with extracted requirements or None if extraction failed
        """
        logger.info("Extracting requirements from email")
        return self.requirements_extraction_service.extract_requirements(email_body)
    
    def extract_entities(self, text: str) -> Optional[Dict[str, List[str]]]:
        """
        Extract named entities from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary mapping entity types to lists of entities
        """
        logger.info("Extracting entities from text")
        return self.requirements_extraction_service.extract_entities(text)
    
    def extract_key_points(self, text: str) -> Optional[List[str]]:
        """
        Extract key points from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of key points
        """
        logger.info("Extracting key points from text")
        return self.requirements_extraction_service.extract_key_points(text)
    
    def analyze_sentiment(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Analyze the sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment analysis results
        """
        logger.info("Analyzing sentiment of text")
        return self.requirements_extraction_service.analyze_sentiment(text)
    
    def generate_proposal(self, extracted_data: Dict[str, Any]) -> Optional[str]:
        """
        Generate a proposal from extracted requirements.
        
        Args:
            extracted_data: Dictionary with requirements and metadata
            
        Returns:
            HTML content for the proposal
        """
        logger.info("Generating proposal")
        return self.document_generation_service.generate_proposal(extracted_data)
    
    def improve_proposal(self, feedback: str, current_html: str) -> Optional[str]:
        """
        Improve a proposal based on feedback.
        
        Args:
            feedback: Feedback on what to improve
            current_html: Current HTML content of the proposal
            
        Returns:
            Improved HTML content
        """
        logger.info("Improving proposal")
        return self.document_generation_service.improve_proposal(feedback, current_html)
    
    def generate_email_response(self, email_body: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Generate an email response.
        
        Args:
            email_body: Body of the email to respond to
            context: Optional additional context for the response
            
        Returns:
            Email response text
        """
        logger.info("Generating email response")
        return self.document_generation_service.generate_email_response(email_body, context)
    
    def generate_summary(self, text: str, max_length: int = 200) -> Optional[str]:
        """
        Generate a summary of text.
        
        Args:
            text: Text to summarize
            max_length: Maximum length of the summary
            
        Returns:
            Summary text
        """
        logger.info(f"Generating summary, max_length={max_length}")
        return self.document_generation_service.generate_summary(text, max_length)
    
    def review_document(self, document_content: str) -> Dict[str, Any]:
        """
        Review a document for quality, completeness, and issues.
        
        Args:
            document_content: Content of the document to review
            
        Returns:
            Dictionary with review results
        """
        logger.info("Reviewing document")
        return self.document_generation_service.review_document(document_content)
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Check the health status of model services.
        
        Returns:
            Dictionary with status information
        """
        status = {
            "service": "model_service_facade",
            "components": {}
        }
        
        # Check main AI service
        ai_service_status = self.ai_service.get_health_status()
        status["components"]["ai_service"] = ai_service_status
        
        # Determine overall status
        if ai_service_status.get("status") == "healthy":
            status["status"] = "healthy"
        else:
            status["status"] = "error"
            status["details"] = "AI service is not healthy"
        
        return status 