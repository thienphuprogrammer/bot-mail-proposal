"""Core interfaces and components for the proposal service."""

from src.services.proposal.core.interfaces import BaseProposalService, ProposalGenerator, ProposalRenderer
from src.services.proposal.core.proposal_facade import ProposalServiceFacade
from src.services.proposal.core.proposal_factory import ProposalServiceFactory

__all__ = [
    "BaseProposalService",
    "ProposalGenerator",
    "ProposalRenderer",
    "ProposalServiceFacade",
    "ProposalServiceFactory",
] 