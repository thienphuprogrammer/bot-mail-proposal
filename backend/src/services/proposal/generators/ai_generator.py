"""
AI-powered proposal content generation.
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal

from src.services.proposal.core.interfaces import ProposalGenerator
from src.services.model.core import ModelServiceFactory
from src.core.config import settings
from src.repositories.base_repository import BaseRepository
from src.models.proposal import (
    ExtractedData, 
    ProposalVersion, 
    ProposalStatus, 
    Priority,
    ApprovalDecision,
    Proposal,
    ProposalCreate
)
from src.models.email import Email

logger = logging.getLogger(__name__)

class AIProposalGenerator(ProposalGenerator):
    """AI-powered proposal generator using language models."""
    
    def __init__(self, proposal_repository: Optional[BaseRepository] = None):
        """
        Initialize the AI proposal generator.
        
        Args:
            proposal_repository: Repository for storing and retrieving proposals
        """
        self.proposal_repository = proposal_repository
        
        # Initialize AI service based on configuration
        if settings.USE_AZURE_AI:
            self.ai_service = ModelServiceFactory.create_azure_model_service()
        else:
            self.ai_service = ModelServiceFactory.create_langchain_model_service()
            
        logger.info(f"Initialized AI proposal generator with {type(self.ai_service).__name__}")
    
    def extract_requirements(self, email: Email) -> Optional[ExtractedData]:
        """
        Extract project requirements from an email using AI.
        
        Args:
            email: Email object to analyze
            
        Returns:
            ExtractedData object with structured requirements or None if extraction failed
        """
        logger.info("Extracting requirements from email")    

        # Set deadline 30 days in the future by default
        future_deadline = datetime.now() + timedelta(days=30)
        
        try:    
            extracted_data = ExtractedData(
                project_name=str(email.subject).strip(),
                description=str(email.body).strip(),
                deadline=future_deadline,
                client_requirements=email.body,
                priority=Priority.MEDIUM
            )
                
            logger.info("Successfully extracted requirements")
            return extracted_data        
        except ValueError as e:
            logger.error(f"Failed to create ExtractedData object: {e}")
            return None
        except Exception as e:
            logger.error(f"Error extracting requirements: {str(e)}")
            return None
        
    def _clean_content():
        pass
    
    def generate_proposal(self, requirements: ExtractedData) -> Optional[str]:
        """
        Generate proposal HTML content from requirements using AI.
        
        Args:
            requirements: ExtractedData object with project requirements
            
        Returns:
            HTML content for the proposal or None if generation failed
        """
        logger.info("Generating proposal from requirements")
        
        try:
            # Convert the requirements to a string representation
            requirements_dict = requirements.model_dump()
            requirements_str = json.dumps(requirements_dict, indent=2, default=str)

            proposal = self.ai_service.generate_proposal(requirements_str)
            
            if not proposal:
                logger.error("Failed to generate proposal from requirements")
                return None
                
            logger.info("Successfully generated proposal")
            return proposal
            
        except Exception as e:
            logger.error(f"Error generating proposal: {str(e)}")
            return None
    
    def regenerate_proposal(self, proposal_id: str, additional_context: Dict[str, Any] = None) -> Optional[str]:
        """
        Regenerate proposal content using existing data and additional context.
        
        Args:
            proposal_id: ID of the existing proposal
            additional_context: Optional additional context to consider
            
        Returns:
            Updated HTML content for the proposal or None if regeneration failed
        """
        if not self.proposal_repository:
            logger.error("Cannot regenerate proposal without repository")
            return None
            
        logger.info(f"Regenerating proposal {proposal_id}")
        
        try:
            # Get existing proposal
            proposal = self.proposal_repository.find_by_id(proposal_id)
            if not proposal:
                logger.error(f"Proposal not found: {proposal_id}")
                return None
                
            # Get the latest version content
            if not proposal.proposal_versions:
                logger.error(f"Proposal has no versions: {proposal_id}")
                return None
                
            latest_version = max(proposal.proposal_versions, key=lambda v: v.version)
            current_html = latest_version.html_content
            
            # Combine existing data with additional context
            context = {
                "proposal_id": proposal_id,
                "project_name": proposal.extracted_data.project_name,
                "client_name": proposal.metadata.get("client_name", "Client"),
                "requirements": proposal.extracted_data.model_dump(),
                "current_html": current_html,
                "feedback": proposal.metadata.get("feedback", []),
            }
            
            if additional_context:
                context.update(additional_context)
                
            # Generate improved version
            prompt = self._build_regeneration_prompt(context)
            improved_html = self.ai_service.improve_proposal(prompt, current_html)
            
            if not improved_html:
                logger.error("Failed to regenerate proposal")
                return current_html
                
            logger.info(f"Successfully regenerated proposal {proposal_id}")
            return improved_html
            
        except Exception as e:
            logger.error(f"Error regenerating proposal: {str(e)}")
            return None
    
    def review_proposal(self, proposal_html: str) -> Dict[str, Any]:
        """
        Review a proposal for quality, completeness, and errors.
        
        Args:
            proposal_html: HTML content of the proposal to review
            
        Returns:
            Dictionary with review results and suggestions
        """
        logger.info("Reviewing proposal content")
        
        try:
            # Use AI service to review the proposal
            review_results = self.ai_service.review_document(proposal_html)
            
            if not review_results:
                logger.error("Failed to review proposal")
                return {
                    "status": "error",
                    "message": "Failed to review proposal",
                    "suggestions": []
                }
                
            # Parse review results if they're in JSON format
            try:
                if isinstance(review_results, str):
                    review_results = json.loads(review_results)
            except json.JSONDecodeError:
                pass
                
            # Ensure the review results have the expected structure
            if not isinstance(review_results, dict):
                review_results = {
                    "status": "success",
                    "message": "Proposal reviewed successfully",
                    "suggestions": []
                }
                
            # Add any missing fields
            review_results.setdefault("status", "success")
            review_results.setdefault("message", "Proposal reviewed successfully")
            review_results.setdefault("suggestions", [])
            
            return review_results
            
        except Exception as e:
            logger.error(f"Error reviewing proposal: {str(e)}")
            return {
                "status": "error",
                "message": f"Error reviewing proposal: {str(e)}",
                "suggestions": []
            }
    
    def _build_regeneration_prompt(self, context: Dict[str, Any]) -> str:
        """
        Build a prompt for regenerating a proposal.
        
        Args:
            context: Context information for regeneration
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""
        Please improve the following proposal based on the provided context:
        
        Project: {context['project_name']}
        Client: {context['client_name']}
        
        Current Requirements:
        {json.dumps(context['requirements'], indent=2, default=str)}
        
        Feedback:
        {json.dumps(context['feedback'], indent=2)}
        
        Current Proposal:
        {context['current_html']}
        
        Please provide an improved version of the proposal that:
        1. Addresses any feedback provided
        2. Maintains consistency with the requirements
        3. Improves clarity and professionalism
        4. Adds any missing important details
        """
        
        return prompt 