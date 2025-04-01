"""Core interfaces and components for the proposal service."""

from services.proposal.core.interfaces import BaseProposalService, ProposalGenerator, ProposalRenderer
from services.proposal.core.proposal_facade import ProposalServiceFacade
from services.proposal.core.proposal_factory import ProposalServiceFactory

__all__ = [
    "BaseProposalService",
    "ProposalGenerator",
    "ProposalRenderer",
    "ProposalServiceFacade",
    "ProposalServiceFactory",
] 