"""
Factory for creating proposal service components with proper dependency injection.
"""

import logging
from typing import Dict, Any, Optional

from services.proposal.core.interfaces import BaseProposalService, ProposalGenerator, ProposalRenderer
from services.proposal.core.proposal_facade import ProposalServiceFacade
from services.proposal.generators.ai_generator import AIProposalGenerator
from services.proposal.renderers.pdf_renderer import PDFProposalRenderer
from services.mail.core.mail_facade import MailServiceFacade
from services.mail.core.mail_factory import MailServiceFactory

logger = logging.getLogger(__name__)

class ProposalServiceFactory:
    """Factory for creating proposal service components."""
    
    @staticmethod
    def create_proposal_generator(proposal_repository: Optional[Any] = None) -> ProposalGenerator:
        """
        Create and configure a proposal generator.
        
        Args:
            proposal_repository: Optional repository for proposal storage
            
        Returns:
            Configured ProposalGenerator instance
        """
        logger.info("Creating AI proposal generator")
        return AIProposalGenerator(proposal_repository=proposal_repository)
    
    @staticmethod
    def create_proposal_renderer(proposal_repository: Any) -> ProposalRenderer:
        """
        Create and configure a proposal renderer.
        
        Args:
            proposal_repository: Repository for proposal storage
            
        Returns:
            Configured ProposalRenderer instance
        """
        logger.info("Creating PDF proposal renderer")
        return PDFProposalRenderer(proposal_repository=proposal_repository)
    
    # Convenient factory function
    @staticmethod
    def create_mail_service() -> MailServiceFacade:
        """
        Create a default mail service facade with all necessary components.
        
        Returns:
            A configured MailServiceFacade ready for fetching and processing emails
        """
        return MailServiceFactory.create_default_gmail_facade()

    @staticmethod
    def create_proposal_facade(
        proposal_generator: Optional[ProposalGenerator] = None,
        proposal_renderer: Optional[ProposalRenderer] = None,
        email_repository: Optional[Any] = None,
        proposal_repository: Optional[Any] = None,
        sent_email_repository: Optional[Any] = None,
        mail_service: Optional[Any] = None
    ) -> ProposalServiceFacade:
        """
        Create a complete proposal service facade with all dependencies.
        
        Args:
            proposal_generator: Optional proposal generator component
            proposal_renderer: Optional proposal renderer component
            email_repository: Optional email repository
            proposal_repository: Optional proposal repository
            sent_email_repository: Optional sent email repository
            mail_service: Optional mail service
            
        Returns:
            Configured ProposalServiceFacade instance
        """
        # Ensure repositories are provided
        if not email_repository or not proposal_repository:
            raise ValueError("Email and proposal repositories must be provided")
            
        # Create components if not provided
        if proposal_generator is None:
            proposal_generator = ProposalServiceFactory.create_proposal_generator(
                proposal_repository=proposal_repository
            )
            
        if proposal_renderer is None:
            proposal_renderer = ProposalServiceFactory.create_proposal_renderer(
                proposal_repository=proposal_repository
            )
            
        # Use existing mail service or create one if not provided
        if mail_service is None:
            mail_service = ProposalServiceFactory.create_mail_service()

        # Create and return the facade
        logger.info("Creating proposal service facade")
        return ProposalServiceFacade(
            proposal_generator=proposal_generator,
            proposal_renderer=proposal_renderer,
            email_repository=email_repository,
            proposal_repository=proposal_repository,
            sent_email_repository=sent_email_repository,
            mail_service=mail_service,
        )
    
    @staticmethod
    def create_default_proposal_service(
        email_repository: Any,
        proposal_repository: Any,
        sent_email_repository: Any
    ) -> BaseProposalService:
        """
        Create a default proposal service with all necessary components.
        
        Args:
            email_repository: Repository for email storage
            proposal_repository: Repository for proposal storage
            sent_email_repository: Repository for sent email storage
            
        Returns:
            Ready-to-use proposal service
        """
        return ProposalServiceFactory.create_proposal_facade(
            email_repository=email_repository,
            proposal_repository=proposal_repository,
            sent_email_repository=sent_email_repository
        ) 