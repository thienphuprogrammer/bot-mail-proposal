"""
Proposal Service Package
=======================

A comprehensive proposal generation system that handles email analysis, content
generation, and document rendering. The architecture follows a clean separation 
of concerns with dependency injection for better testability.

Directory Structure:
- core/: Core interfaces and service orchestration
- generators/: Proposal content generation implementations
- renderers/: Proposal format rendering implementations

Usage Example:
    ```python
    from src.services.proposal import create_proposal_service
    from src.repositories.email_repository import EmailRepository
    from src.repositories.proposal_repository import ProposalRepository
    from src.repositories.sent_email_repository import SentEmailRepository
    
    # Set up repositories
    email_repo = EmailRepository()
    proposal_repo = ProposalRepository()
    sent_email_repo = SentEmailRepository()
    
    # Get a configured proposal service
    proposal_service = create_proposal_service(
        email_repository=email_repo,
        proposal_repository=proposal_repo,
        sent_email_repository=sent_email_repo
    )
    
    # Process emails and generate proposals
    results = proposal_service.process_new_emails(max_emails=20)
    ```
"""

# Export core interfaces and classes
from src.services.proposal.core import (
    BaseProposalService,
    ProposalGenerator,
    ProposalRenderer,
    ProposalServiceFacade,
    ProposalServiceFactory,
)

# Export generator implementations
from src.services.proposal.generators import AIProposalGenerator

# Export renderer implementations
from src.services.proposal.renderers import PDFProposalRenderer

# Convenient factory function
def create_proposal_service(
    email_repository: any,
    proposal_repository: any,
    sent_email_repository: any
) -> BaseProposalService:
    """
    Create a default proposal service with all necessary components.
    
    Args:
        email_repository: Repository for email storage
        proposal_repository: Repository for proposal storage
        sent_email_repository: Repository for sent email storage
        
    Returns:
        A configured proposal service ready for processing emails and generating proposals
    """
    return ProposalServiceFactory.create_default_proposal_service(
        email_repository=email_repository,
        proposal_repository=proposal_repository,
        sent_email_repository=sent_email_repository
    )

__all__ = [
    # Core interfaces
    "BaseProposalService",
    "ProposalGenerator", 
    "ProposalRenderer",
    "ProposalServiceFacade",
    "ProposalServiceFactory",
    
    # Generators
    "AIProposalGenerator",
    
    # Renderers
    "PDFProposalRenderer",
    
    # Helper functions
    "create_proposal_service",
]
