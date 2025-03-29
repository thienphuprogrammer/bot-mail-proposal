from abc import ABC, abstractmethod
from typing import Optional

from src.models.proposal import ExtractedData


class AIService(ABC):
    """Base interface for AI services."""
    
    @abstractmethod
    def extract_requirements(self, email_body: str) -> Optional[ExtractedData]:
        """Extract requirements from email body."""
        pass
    
    @abstractmethod
    def generate_proposal(self, extracted_data: ExtractedData) -> Optional[str]:
        """Generate a proposal from extracted data."""
        pass
    
    @abstractmethod
    def generate_pdf(self, html_content: str, output_path: str) -> bool:
        """Generate a PDF from HTML content."""
        pass
