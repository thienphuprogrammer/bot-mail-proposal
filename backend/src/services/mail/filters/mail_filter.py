"""
Mail filter service for spam detection and email categorization using Azure AI.
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
import json
from datetime import datetime

from models.email import EmailCreate
from services.mail.core.interfaces import MailFilter
from services.model.providers.azure_service import AzureModelService
from core.config import settings
from azure.ai.inference.models import SystemMessage, UserMessage

logger = logging.getLogger(__name__)

class MailFilterService(MailFilter):
    """Service for filtering emails and categorizing them using Azure AI."""
    
    # Common spam keywords and patterns (kept for fallback)
    SPAM_KEYWORDS = [
        'buy now', 'click here', 'free offer', 'limited time', 'discount',
        'congrats', 'congratulations', 'winner', 'won', 'prize', 'lottery',
        'nigeria', 'inheritance', 'million dollars', 'urgent', 'attention',
        'account suspended', 'verify your account', 'banking details',
        'cryptocurrency', 'investment opportunity', 'make money fast',
        'work from home', 'earn extra income', 'get rich'
    ]
    
    # Legitimate business email domains
    TRUSTED_DOMAINS = [
        'gmail.com', 'outlook.com', 'hotmail.com', 'yahoo.com', 
        'office365.com', 'microsoft.com', 'apple.com', 'icloud.com'
    ]
    
    # Business request keywords (kept for fallback)
    BUSINESS_REQUEST_KEYWORDS = [
        'proposal', 'project', 'quote', 'quotation', 'estimate',
        'service', 'consultation', 'collaborate', 'partnership',
        'business opportunity', 'contract', 'hire', 'outsource',
        'development', 'software', 'application', 'web', 'mobile',
        'deadline', 'budget', 'requirements', 'specification'
    ]
    
    def __init__(self):
        """Initialize the email filter service with Azure AI integration."""
        # Cache for previously classified emails
        self._classification_cache = {}
        
        # Initialize Azure AI service
        try:
            self.azure_service = AzureModelService(
                api_key=settings.AZURE_OPENAI_API_KEY,
                endpoint=settings.AZURE_OPENAI_ENDPOINT
            )
            logger.info("Azure AI service initialized for email filtering")
        except Exception as e:
            logger.error(f"Failed to initialize Azure AI service: {e}. Falling back to rule-based filtering.")
    
    def is_spam(self, email: EmailCreate) -> Tuple[bool, Dict[str, Any]]:
        """
        Determine if an email is spam using Azure AI or fallback to rules.
        
        Args:
            email: The email to check
            
        Returns:
            Tuple of (is_spam, details) where details contains the reasons
        """
        # Check cache first
        if email.gmail_id in self._classification_cache:
            return self._classification_cache[email.gmail_id]
            
        # Initialize result details
        details = {
            "spam_score": 0.0,
            "reasons": [],
            "checks": {}
        }

        is_spam_flag = False
        
        # Use Azure AI for spam detection
        try:
            result = self._analyze_with_azure_ai(email, "spam_detection")  
            if result:
                details["spam_score"] = result.get("spam_score", 0.0)
                details["reasons"] = result.get("reasons", [])
                details["checks"]["ai_check"] = {
                    "is_spam": details["spam_score"] >= 0.5,
                    "score": details["spam_score"]
                }
                is_spam_flag = details["spam_score"] >= 0.5
                self._classification_cache[email.gmail_id] = (is_spam_flag, details)
            return (is_spam_flag, details)
                
        except Exception as e:
            logger.error(f"Error using Azure AI for spam detection: {e}. Falling back to rules.")
        
        # Fallback to rule-based checks if AI is unavailable or failed
        return self._rule_based_spam_check(email)
    
    def _rule_based_spam_check(self, email: EmailCreate) -> Tuple[bool, Dict[str, Any]]:
        """Fallback method using rule-based checks for spam detection."""
        details = {
            "spam_score": 0.0,
            "reasons": [],
            "checks": {}
        }
        
        # Check 1: Keyword check
        keyword_check = self._check_spam_keywords(email.subject, email.body)
        details["checks"]["keyword_check"] = keyword_check
        if keyword_check["is_spam"]:
            details["reasons"].append(f"Contains spam keywords: {', '.join(keyword_check['matched_keywords'])}")
            details["spam_score"] += 0.3 * min(1, len(keyword_check["matched_keywords"]) / 3)
        
        # Check 2: Sender domain check
        domain_check = self._check_sender_domain(email.sender)
        details["checks"]["domain_check"] = domain_check
        if domain_check["is_spam"]:
            details["reasons"].append(f"Suspicious sender domain: {domain_check['domain']}")
            details["spam_score"] += 0.2
        
        # Check 3: Suspicious patterns check
        pattern_check = self._check_suspicious_patterns(email.subject, email.body)
        details["checks"]["pattern_check"] = pattern_check
        if pattern_check["is_spam"]:
            details["reasons"].extend(pattern_check["reasons"])
            details["spam_score"] += 0.2 * min(1, len(pattern_check["reasons"]) / 2)
        
        # Normalize spam score to 0-1 range
        details["spam_score"] = min(1.0, details["spam_score"])
        
        # Final decision based on spam score
        is_spam = details["spam_score"] >= 0.5
        
        # Cache the result
        self._classification_cache[email.gmail_id] = (is_spam, details)
        
        return (is_spam, details)
    
    def _analyze_with_azure_ai(self, email: EmailCreate, analysis_type: str) -> Optional[Dict[str, Any]]:
        """
        Analyze an email using the Azure AI service.
        
        Args:
            email: The email to analyze
            analysis_type: Type of analysis to perform
            
        Returns:
            Dictionary with analysis results or None if failed
        """
        try:
            # Create a combined message with important email metadata
            email_content = f"""
            Subject: {email.subject}
            From: {email.sender}
            Date: {email.received_at or datetime.now().isoformat()}
            
            {email.body}
            """
            
            if analysis_type == "spam_detection":
                prompt = f"""
                Analyze the following email and determine if it's spam or legitimate.
                Provide your analysis as a JSON with these fields:
                - spam_score: A number between 0 and 1 where 0 is definitely not spam and 1 is definitely spam
                - reasons: A list of reasons why this might be spam, if applicable
                - category: The likely category of this email (spam, marketing, business_request, personal, etc.)
                
                Email:
                {email_content}
                """
                
                system_message = "You are an AI assistant that specializes in email spam detection and classification. Analyze emails objectively and provide a structured JSON response."
                
            elif analysis_type == "intent_detection":
                prompt = f"""
                Analyze the following email and determine the sender's intent and the email category.
                Provide your analysis as a JSON with these fields:
                - category: The most likely category (proposal_requests, inquiries, spam, marketing, other)
                - confidence: A number between 0 and 1 indicating your confidence in this classification
                - details: Additional details about the intent, including:
                  - project_type: If this is a project request, what type of project
                  - deadline_mentioned: Boolean indicating if a deadline is mentioned
                  - budget_mentioned: Boolean indicating if a budget is mentioned
                  - urgent: Boolean indicating if the request is urgent
                  - key_points: List of key points extracted from the email
                
                Email:
                {email_content}
                """
                
                system_message = "You are an AI assistant that specializes in analyzing business emails to detect intent and extract key information. Provide structured JSON responses."
                
            else:
                logger.error(f"Unknown analysis type: {analysis_type}")
                return None
            
            # Call Azure AI service
            response = self.azure_service.client.complete(
                messages=[
                    SystemMessage(content=system_message),
                    UserMessage(content=prompt)
                ],
                model_extras={"safe_mode": True},
                temperature=0.1
            )
            
            if not response:
                logger.error(f"No response from Azure AI for {analysis_type}")
                return None
                
            result_text = response.choices[0].message.content
                
            # Extract the JSON part from the response
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.error(f"No valid JSON found in Azure AI response for {analysis_type}")
                return None
                
            json_str = result_text[json_start:json_end]
            
            # Parse the JSON
            analysis_data = json.loads(json_str)
            
            logger.info(f"Successfully analyzed email using Azure AI: {analysis_type}")
            return analysis_data
            
        except Exception as e:
            logger.error(f"Error analyzing email with Azure AI ({analysis_type}): {e}")
            return None
    
    def _check_spam_keywords(self, subject: str, body: str) -> Dict[str, Any]:
        """Check if the email contains common spam keywords."""
        result = {
            "is_spam": False,
            "matched_keywords": []
        }
        
        # Combine subject and body for checking
        text = (subject + " " + body).lower()
        
        # Check for spam keywords
        for keyword in self.SPAM_KEYWORDS:
            if keyword.lower() in text:
                result["matched_keywords"].append(keyword)
        
        # If we found 3 or more spam keywords, consider it spam
        if len(result["matched_keywords"]) >= 3:
            result["is_spam"] = True
            
        return result
    
    def _check_sender_domain(self, sender: str) -> Dict[str, Any]:
        """Check if the sender's domain is suspicious."""
        result = {
            "is_spam": False,
            "domain": ""
        }
        
        # Extract domain from sender
        domain_match = re.search(r'@([^@\s]+)$', sender)
        if domain_match:
            domain = domain_match.group(1).lower()
            result["domain"] = domain
            
            # Check if domain is in our trusted list
            if domain not in self.TRUSTED_DOMAINS:
                # Additional checks for suspicious domains
                if len(domain) > 25:  # Unusually long domain
                    result["is_spam"] = True
                elif domain.count('.') > 3:  # Too many subdomains
                    result["is_spam"] = True
                elif re.match(r'.*\d{4,}.*', domain):  # Domain with many numbers
                    result["is_spam"] = True
        
        return result
    
    def _check_suspicious_patterns(self, subject: str, body: str) -> Dict[str, Any]:
        """Check for suspicious patterns in the email."""
        result = {
            "is_spam": False,
            "reasons": []
        }
        
        # Check 1: Excessive capitalization in subject
        if sum(1 for c in subject if c.isupper()) > 0.5 * len(subject) and len(subject) > 10:
            result["reasons"].append("Excessive capitalization in subject")
        
        # Check 2: Lots of exclamation points
        if subject.count('!') >= 2 or body.count('!') >= 5:
            result["reasons"].append("Excessive exclamation points")
        
        # Check 3: Suspicious URLs
        urls = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', body)
        suspicious_urls = [url for url in urls if any(suspicious in url.lower() for suspicious in 
                          ['crypto', 'prize', 'lottery', 'payment', 'verify', 'click'])]
        
        if suspicious_urls:
            result["reasons"].append(f"Contains {len(suspicious_urls)} suspicious URLs")
        
        # Check 4: Excessive HTML content
        html_tags_count = len(re.findall(r'<[^>]+>', body))
        if html_tags_count > 50:
            result["reasons"].append(f"Excessive HTML content ({html_tags_count} tags)")
        
        if result["reasons"]:
            result["is_spam"] = True
            
        return result
    
    def detect_email_intent(self, email: EmailCreate) -> Dict[str, Any]:
        """
        Detect the intent and category of an email using Azure AI.
        
        Args:
            email: The email to analyze
            
        Returns:
            Dictionary with intent details including category and confidence
        """
        default_intent = {
            "category": "other",
            "confidence": 0.0,
            "details": {}
        }
        
        # Check if it's spam first
        is_spam, spam_details = self.is_spam(email)
        if is_spam:
            default_intent["category"] = "spam"
            default_intent["confidence"] = spam_details["spam_score"]
            default_intent["details"]["spam_score"] = spam_details["spam_score"]
            default_intent["details"]["spam_reasons"] = spam_details["reasons"]
            return default_intent
        
        try:
            # Use Azure AI for intent detection
            result = self._analyze_with_azure_ai(email, "intent_detection")
                
            if result:
                intent = {
                    "category": result.get("category", "other"),
                    "confidence": result.get("confidence", 0.5),
                    "details": result.get("details", {})
                }
                return intent
                
        except Exception as e:
            logger.error(f"Error using Azure AI for intent detection: {e}. Falling back to rules.")
        
        # Fallback to rule-based intent detection
        return self._rule_based_intent_detection(email)
    
    def _rule_based_intent_detection(self, email: EmailCreate) -> Dict[str, Any]:
        """Fallback method using rule-based checks for intent detection."""
        intent = {
            "category": "other",
            "confidence": 0.0,
            "details": {}
        }
        
        # Check for business request keywords in subject and body
        text = f"{email.subject} {email.body}".lower()
        business_keywords = [keyword for keyword in self.BUSINESS_REQUEST_KEYWORDS if keyword.lower() in text]
        
        if business_keywords:
            # If we found business keywords, this is likely a proposal request
            proposal_score = min(1.0, len(business_keywords) / 5)
            intent["category"] = "proposal_requests"
            intent["confidence"] = proposal_score
            intent["details"]["matched_keywords"] = business_keywords
            
            # Extract specific request details
            request_details = self._extract_request_details(email)
            intent["details"]["request_info"] = request_details
        else:
            # Check for inquiry patterns
            if '?' in email.subject or email.subject.lower().startswith(('how', 'what', 'when', 'where', 'who', 'can you')):
                intent["category"] = "inquiries"
                intent["confidence"] = 0.8
            elif '?' in email.body:
                # Count questions in body
                question_count = email.body.count('?')
                if question_count >= 2:
                    intent["category"] = "inquiries"
                    intent["confidence"] = min(1.0, question_count / 5)
        
        return intent
    
    def _extract_request_details(self, email: EmailCreate) -> Dict[str, Any]:
        """Extract structured details from a proposal request email."""
        details = {
            "project_type": "",
            "deadline_mentioned": False,
            "budget_mentioned": False,
            "urgent": False
        }
        
        # Check for project type
        project_types = [
            'website', 'app', 'application', 'mobile app', 'web app',
            'e-commerce', 'ecommerce', 'software', 'system', 'integration',
            'api', 'automation', 'chatbot', 'dashboard', 'analytics'
        ]
        
        text = f"{email.subject} {email.body}".lower()
        
        # Check each project type
        for project in project_types:
            if project in text:
                details["project_type"] = project
                break
        
        # Check for deadline mentions
        deadline_keywords = ['deadline', 'due date', 'due by', 'complete by', 'delivery date', 'timeframe']
        details["deadline_mentioned"] = any(keyword in text for keyword in deadline_keywords)
        
        # Check for budget mentions
        budget_keywords = ['budget', 'cost', 'price', 'quote', 'estimate', '$', 'usd', 'eur', 'dollars', 'euros']
        details["budget_mentioned"] = any(keyword in text for keyword in budget_keywords)
        
        # Check for urgency
        urgency_keywords = ['asap', 'urgent', 'quickly', 'immediately', 'as soon as possible', 'rush']
        details["urgent"] = any(keyword in text for keyword in urgency_keywords)
        
        return details
    
    def filter_emails(self, emails: List[EmailCreate]) -> Dict[str, List[EmailCreate]]:
        """
        Filter a list of emails into different categories using Azure AI.
        
        Args:
            emails: List of emails to filter
            
        Returns:
            Dictionary with categories as keys and lists of emails as values
        """
        categories = {
            "spam": [],
            "proposal_requests": [],
            "inquiries": [],
            "other": []
        }
        
        for email in emails:
            try:
                # Detect intent for each email
                intent = self.detect_email_intent(email)
                category = intent.get("category", "other")
                
                # Add to appropriate category
                if category in categories:
                    categories[category].append(email)
                else:
                    categories["other"].append(email)
            except Exception as e:
                logger.error(f"Error filtering email {email.gmail_id}: {e}")
                categories["other"].append(email)
        
        return categories 