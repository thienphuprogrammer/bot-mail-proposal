# Initialize MongoDB connection
from src.database.mongodb import init_db, MongoDB
from src.repositories.email_repository import EmailRepository
from src.repositories.proposal_repository import ProposalRepository
from src.repositories.sent_email_repository import SentEmailRepository
from src.repositories.user_repository import UserRepository
from src.repositories.template_repository import TemplateRepository

# Import refactored services
from src.services.authentication import create_auth_service
from src.services.model import create_model_service
from src.services.mail.core.mail_facade import MailServiceFacade
from src.services.mail.core.mail_factory import MailServiceFactory
from src.services.proposal.core.proposal_facade import ProposalServiceFacade
from src.services.proposal.core.proposal_factory import ProposalServiceFactory
from src.services.mail.providers.outlook_service import OutlookService
from src.services.template.template_service import TemplateService
from src.core.config import settings
import httpx
import webbrowser
import os
import json

def initialize_services():
    # Initialize database
    init_db()
    
    # Create repositories
    email_repository = EmailRepository()
    proposal_repository = ProposalRepository()
    sent_email_repository = SentEmailRepository()
    user_repository = UserRepository()
    template_repository = TemplateRepository()
    
    # Create authentication service using the factory
    auth_service = create_auth_service(user_repository=user_repository)
    
    # Create model service using the factory
    model_service = create_model_service(
        provider="langchain" if not settings.USE_AZURE_AI else "azure"
    )
    
    # Create mail service using the factory
    mail_service = MailServiceFactory.create_gmail_service()
    mail_processor = MailServiceFactory.create_mail_processor(mail_service)
    mail_filter = MailServiceFactory.create_mail_filter()
    mail_facade = MailServiceFacade(
        mail_service=mail_service,
        mail_processor=mail_processor,
        mail_filter=mail_filter,
        email_repository=email_repository
    )
    
    # Create proposal service using the factory
    proposal_generator = ProposalServiceFactory.create_proposal_generator(proposal_repository=proposal_repository)
    proposal_renderer = ProposalServiceFactory.create_proposal_renderer(proposal_repository=proposal_repository)
    proposal_facade = ProposalServiceFacade(
        proposal_generator=proposal_generator,
        proposal_renderer=proposal_renderer,
        email_repository=email_repository,
        proposal_repository=proposal_repository,
         mail_service=mail_facade
    )
    
    template_service = TemplateService(
        template_repository=template_repository
    )

    # Create Outlook service
    outlook_service = OutlookService()  
    
    return {
        "mail_service": mail_service,
        "mail_facade": mail_facade,
        "email_repository": email_repository,
        "proposal_repository": proposal_repository,
        "sent_email_repository": sent_email_repository,
        "user_repository": user_repository,
        "template_repository": template_repository,
        "model_service": model_service,
        "proposal_service": proposal_facade,
        "auth_service": auth_service,
        "template_service": template_service,
        "outlook_service": outlook_service
    }

if __name__ == "__main__":
    services = initialize_services()
    proposal_id = "67ef635671a6606a0a0f591c"

    pdf = services["proposal_service"].generate_pdf(proposal_id)

    
    
