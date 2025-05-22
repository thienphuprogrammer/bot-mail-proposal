"""
Mail service façade for simplified access to mail functionality.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.services.mail.core.interfaces import BaseMailService
from src.services.mail.core.interfaces import MailProcessor
from src.services.mail.core.interfaces import MailFilter
from src.models.email import Email
from src.repositories.email_repository import EmailRepository
logger = logging.getLogger(__name__)

class MailServiceFacade:
    """
    Façade for interacting with mail services, processors, and filters.
    Provides a simplified interface for common operations.
    """
    
    def __init__(
        self, 
        mail_service: BaseMailService,
        mail_processor: MailProcessor,
        mail_filter: MailFilter,
        email_repository: EmailRepository
    ):
        """Initialize with required service components."""
        self.mail_service = mail_service
        self.mail_processor = mail_processor
        self.mail_filter = mail_filter
        self.email_repository = email_repository

    def fetch_and_process_emails(self, 
                                query: str = None, 
                                max_results: int = 20,
                                folder: str = None,
                                include_spam_trash: bool = None,
                                only_recent: bool = None
                                ) -> List[Email]:
        """
        Fetch, process, and categorize emails.
        
        Args:
            query: Email search query
            max_results: Maximum number of emails to fetch
            include_spam_trash: Whether to include spam and trash
            
        Returns:
            List of Email objects fetched from the mail service
        """
        start_time = datetime.utcnow()
        
        # Stats dictionary for tracking results
        stats = {
            "fetched": 0,
            "processed": 0,
            "categories": {
                "spam": 0,
                "proposal_requests": 0,
                "inquiries": 0,
                "other": 0
            },
            "errors": []
        }
        
        try:
            # Fetch emails from the mail service
            emails = self.mail_service.fetch_emails(
                query=query,
                max_results=max_results,
                folder=folder,
                include_spam_trash=include_spam_trash,
                only_recent=only_recent
            )

            stats["fetched"] = len(emails)
            logger.info(f"Fetched {len(emails)} emails")

            if not emails or len(emails) == 0:
                logger.info("No emails to process")
                return []
            
            # # Categorize emails using the filter
            # categorized_emails = self.mail_filter.filter_emails(emails)
            
            # # Update statistics
            # for category, emails_in_category in categorized_emails.items():
            #     stats["categories"][category] = len(emails_in_category)
            #     stats["processed"] += len(emails_in_category)
            
            # Mark emails as read
            for email in emails:
                self.mail_service.mark_as_read(email.email_id)
            
            # # Apply category labels - convert async to sync with run_async
            # self._apply_category_labels_sync(categorized_emails)
            
            # logger.info(f"Processed {stats['processed']} emails: "
            #           f"{stats['categories']['spam']} spam, "
            #           f"{stats['categories']['proposal_requests']} requests, "
            #           f"{stats['categories']['inquiries']} inquiries, "
            #           f"{stats['categories']['other']} other")
            
            # # Save emails to the database
            print(f"Saving {len(emails)} emails to the database")
            results = []
            for email in emails:
                results.append(self.email_repository.create(email))
            
            # Return the list of emails instead of the stats
            return results
        except Exception as e:
            error_msg = f"Error processing emails: {str(e)}"
            logger.error(error_msg)
            stats["errors"].append(error_msg)
            return []
    
    def _apply_category_labels_sync(self, categorized_emails: Dict[str, List[Email]]) -> None:
        """Synchronous wrapper for applying labels to emails based on their category."""
        try:
            # Run the async function in a synchronous context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._apply_category_labels(categorized_emails))
            loop.close()
        except Exception as e:
            logger.error(f"Error applying category labels: {str(e)}")
    
    async def _apply_category_labels(self, categorized_emails: Dict[str, List[Email]]) -> None:
        """Apply labels to emails based on their category."""
        # Map categories to labels
        label_map = {
            "spam": "Processed/Spam",
            "proposal_requests": "Processed/Proposal Requests",
            "inquiries": "Processed/Inquiries",
            "other": "Processed/Other"
        }
        
        for category, emails in categorized_emails.items():
            label = label_map.get(category)
            if not label:
                continue
                
            for email in emails:
                try:
                    self.mail_service.apply_label(email.email_id, label)
                except Exception as e:
                    logger.error(f"Error applying label {label} to email {email.email_id}: {str(e)}")
    
    def _complete_stats(self, stats: Dict[str, Any], start_time: datetime) -> Dict[str, Any]:
        """Complete the statistics with timing information."""
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        stats.update({
            "started_at": start_time.isoformat(),
            "finished_at": end_time.isoformat(),
            "processing_time_seconds": processing_time
        })
        
        return stats
    
    def process_single_email(self, email_id: str) -> Dict[str, Any]:
        """
        Process a single email by ID.
        
        Args:
            email_id: The email ID to process
            
        Returns:
            Processing results including category and details
        """
        try:
            # Get the email details
            email_details = self.mail_processor.get_email_details(email_id)
            if 'email_id' not in email_details or email_details.get('subject') == 'Email not found':
                return {
                    "success": False,
                    "error": "Email not found"
                }
            
            # Create an Email object for classification
            email = Email(
                id=email_details.get('email_id'),
                email_id=email_details.get('email_id'),
                subject=email_details.get('subject', ''),
                sender=email_details.get('sender', ''),
                body=email_details.get('body', ''),
                received_at=datetime.fromisoformat(email_details.get('date')) if email_details.get('date') else datetime.utcnow(),
                processing_status="pending",
                attachments=email_details.get('attachments', [])
            )
            
            # Analyze the email
            is_spam, spam_details = self.mail_filter.is_spam(email)
            intent = self.mail_filter.detect_email_intent(email)
            
            # Extract metadata
            metadata = self.mail_processor.extract_metadata(email)
            
            return {
                "success": True,
                "email_id": email_id,
                "subject": email.subject,
                "is_spam": is_spam,
                "spam_details": spam_details,
                "intent": intent,
                "metadata": metadata
            }
        except Exception as e:
            error_msg = f"Error processing email: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get the health status of all mail services."""
        return {
            "mail_service": self.mail_service.get_health_status(),
            "timestamp": datetime.utcnow().isoformat()
        } 