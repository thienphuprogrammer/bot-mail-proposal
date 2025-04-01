"""
AI Model Service Interfaces
=========================

This module defines the core interfaces that all AI model service implementations must follow.
The design uses the Interface Segregation Principle to separate different concerns:

1. AIService: Core model operations
2. TextGenerationService: Text generation capabilities
3. RequirementsExtractionService: Requirements extraction from text
4. DocumentGenerationService: Document generation capabilities

Each implementation should respect these interfaces to ensure consistent behavior
across different AI models and providers.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

class AIService(ABC):
    """Base interface for AI services."""
    
    @abstractmethod
    def generate_text(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> Optional[str]:
        """
        Generate text using the AI model.
        
        Args:
            prompt: Text prompt to generate from
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (higher = more creative, lower = more focused)
            
        Returns:
            Generated text or None if generation failed
        """
        pass
    
    @abstractmethod
    def extract_requirements(self, email_body: str) -> Optional[str]:
        """
        Extract project requirements from an email.
        
        Args:
            email_body: Body of the email to analyze
            
        Returns:
            string with extracted requirements
        """
        pass
    
    @abstractmethod
    def generate_proposal(self, extracted_data: str) -> Optional[str]:
        """
        Generate a proposal from extracted requirements.
        
        Args:
            extracted_data: Dictionary with requirements and metadata
            
        Returns:
            HTML content for the proposal
        """
        pass
    
    @abstractmethod
    def improve_proposal(self, feedback: str, current_html: str) -> Optional[str]:
        """
        Improve a proposal based on feedback.
        
        Args:
            feedback: Feedback on what to improve
            current_html: Current HTML content of the proposal
            
        Returns:
            Improved HTML content
        """
        pass
    
    @abstractmethod
    def review_document(self, document_content: str) -> str:
        """
        Review a document for quality, completeness, and issues.
        
        Args:
            document_content: Content of the document to review
            
        Returns:
            string with review results
        """
        pass
    
    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """
        Check the health status of the AI service.
        
        Returns:
            Dictionary with status information
        """
        pass


class TextGenerationService(ABC):
    """Interface for text generation capabilities."""
    
    @abstractmethod
    def generate_text(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> Optional[str]:
        """
        Generate text using the AI model.
        
        Args:
            prompt: Text prompt to generate from
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (higher = more creative, lower = more focused)
            
        Returns:
            Generated text or None if generation failed
        """
        pass
    
    @abstractmethod
    def generate_completion(self, text: str, max_tokens: int = 1000, temperature: float = 0.7) -> Optional[str]:
        """
        Complete text using the AI model.
        
        Args:
            text: Text to complete
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (higher = more creative, lower = more focused)
            
        Returns:
            Completed text or None if completion failed
        """
        pass
    
    @abstractmethod
    def generate_chat_response(self, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.7) -> Optional[str]:
        """
        Generate a response in a chat context.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (higher = more creative, lower = more focused)
            
        Returns:
            Response text or None if generation failed
        """
        pass


class RequirementsExtractionService(ABC):
    """Interface for requirements extraction capabilities."""
    
    @abstractmethod
    def extract_requirements(self, email_body: str) -> Optional[Dict[str, Any]]:
        """
        Extract project requirements from an email.
        
        Args:
            email_body: Body of the email to analyze
            
        Returns:
            Dictionary with extracted requirements and metadata
        """
        pass
    
    @abstractmethod
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities from text.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            Dictionary with entity types as keys and lists of entities as values
        """
        pass
    
    @abstractmethod
    def extract_key_points(self, text: str) -> List[str]:
        """
        Extract key points from text.
        
        Args:
            text: Text to extract key points from
            
        Returns:
            List of key points
        """
        pass
    
    @abstractmethod
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment analysis results
        """
        pass


class DocumentGenerationService(ABC):
    """Interface for document generation capabilities."""
    
    @abstractmethod
    def generate_proposal(self, extracted_data: Dict[str, Any]) -> Optional[str]:
        """
        Generate a proposal from extracted requirements.
        
        Args:
            extracted_data: Dictionary with requirements and metadata
            
        Returns:
            HTML content for the proposal
        """
        pass
    
    @abstractmethod
    def improve_proposal(self, feedback: str, current_html: str) -> Optional[str]:
        """
        Improve a proposal based on feedback.
        
        Args:
            feedback: Feedback on what to improve
            current_html: Current HTML content of the proposal
            
        Returns:
            Improved HTML content
        """
        pass
    
    @abstractmethod
    def generate_email_response(self, email_content: str, response_type: str) -> str:
        """
        Generate an email response.
        
        Args:
            email_content: Content of the email to respond to
            response_type: Type of response (e.g., 'followup', 'clarification', 'acceptance')
            
        Returns:
            Email response text
        """
        pass
    
    @abstractmethod
    def generate_summary(self, text: str, max_length: int = 200) -> str:
        """
        Generate a summary of text.
        
        Args:
            text: Text to summarize
            max_length: Maximum length of the summary in characters
            
        Returns:
            Summary text
        """
        pass
    
    @abstractmethod
    def review_document(self, document_content: str) -> Dict[str, Any]:
        """
        Review a document for quality, completeness, and issues.
        
        Args:
            document_content: Content of the document to review
            
        Returns:
            Dictionary with review results
        """
        pass 