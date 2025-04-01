"""
Azure DeepSeek AI service implementation.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from services.model.core.interfaces import AIService
from models.proposal import ExtractedData, ProposalStatus
from core.config import settings

logger = logging.getLogger(__name__)

# Import Azure AI Inference SDK
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

class AzureModelService(AIService):
    """Azure DeepSeek AI service."""
    
    def __init__(self, api_key: str = None, endpoint: str = None):
        """
        Initialize Azure AI service.
        
        Args:
            api_key: Azure API key, defaults to settings.AZURE_API_KEY
            endpoint: Azure endpoint, defaults to settings.AZURE_ENDPOINT
        """
        self.api_key = api_key or settings.AZURE_OPENAI_API_KEY
        self.endpoint = endpoint or settings.AZURE_OPENAI_ENDPOINT
        self.model_name = "DeepSeek-R1"
        self.client = None
        
        # Initialize Azure clients
        try:
            self._setup_clients()
            logger.info("Azure AI service initialized")
        except Exception as e:
            logger.error(f"Error initializing Azure AI service: {e}")
    
    def _setup_clients(self):
        """Set up Azure clients."""
        self.client = ChatCompletionsClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.api_key),
            model=self.model_name
        )
    
    def generate_text(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> Optional[str]:
        """
        Generate text using Azure's DeepSeek model.
        
        Args:
            prompt: Text prompt to generate from
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated text or None if generation failed
        """
        try:
            logger.info(f"Generating text with Azure DeepSeek, max_tokens={max_tokens}, temp={temperature}")
            
            response = self.client.complete(
                messages=[UserMessage(content=prompt)],
                model_extras={
                    "safe_mode": True,
                    "max_tokens": max_tokens
                },
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return None
    
    def extract_requirements(self, email_body: str) -> Optional[str]:
        """
        Extract project requirements from an email using Azure AI.
        
        Args:
            email_body: Body of the email to analyze
            
        Returns:
            JSON string with extracted requirements or None if extraction failed
        """
        try:
            logger.info("Extracting requirements with Azure DeepSeek")
            
            # Construct a prompt for the extraction
            extraction_prompt = f"""
            Extract key project requirements and metadata from the following email.
            Format the output as a structured JSON with the following fields:
            - project_title: A concise title for the project (required)
            - client_name: Name of the client or company (required)
            - timeline: Expected timeline for the project (ISO format)
            - budget: Budget information if mentioned (numeric value)
            - project_type: Type of project (web, mobile, etc.)
            - requirements: Detailed project requirements (required)
            - tech_stack: List of technologies mentioned or required (must be a list)
            - additional_notes: Any other important information
            
            Email:
            {email_body}
            
            Return ONLY the JSON object, no additional text or explanation.
            Ensure tech_stack is always a list, even if empty.
            """
            
            # Generate the structured extraction using system message for instructions
            response = self.client.complete(
                messages=[
                    SystemMessage(content="You are an AI assistant that extracts structured information from emails. Return only valid JSON."),
                    UserMessage(content=extraction_prompt)
                ],
                model_extras={
                    "safe_mode": True
                },
                temperature=0.2
            )
            
            if not response or not response.choices:
                logger.error("No response received from Azure AI")
                return None
            
            content = response.choices[0].message.content.strip()
            
            # Try to find JSON in the response if there's additional text
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            
            # Validate JSON output
            try:
                extracted_data = json.loads(content)
                
                # Validate required fields
                required_fields = ["project_title", "requirements"]
                missing_fields = [field for field in required_fields if field not in extracted_data]
                if missing_fields:
                    logger.error(f"Extracted data missing required fields: {missing_fields}")
                    return None
                
                # Ensure project_title is not empty
                if not str(extracted_data["project_title"]).strip():
                    logger.error("Project title is empty")
                    return None
                
                # Ensure requirements is not empty
                if not str(extracted_data["requirements"]).strip():
                    logger.error("Requirements are empty")
                    return None
                
                # Validate timeline format if present
                if "timeline" in extracted_data:
                    try:
                        datetime.fromisoformat(extracted_data["timeline"])
                    except ValueError:
                        logger.error("Invalid timeline format")
                        return None
                
                # Validate budget if present
                if "budget" in extracted_data and extracted_data["budget"] is not None:
                    try:
                        float(extracted_data["budget"])
                    except (ValueError, TypeError):
                        logger.error("Invalid budget format")
                        return None
                
                # Ensure tech_stack is a list
                if "tech_stack" not in extracted_data:
                    extracted_data["tech_stack"] = []
                elif not isinstance(extracted_data["tech_stack"], list):
                    # Convert to list if it's a string
                    if isinstance(extracted_data["tech_stack"], str):
                        extracted_data["tech_stack"] = [tech.strip() for tech in extracted_data["tech_stack"].split(",") if tech.strip()]
                    else:
                        extracted_data["tech_stack"] = []
                
                return json.dumps(extracted_data)
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse extracted data as JSON: {e}")
                return None
            
        except Exception as e:
            logger.error(f"Error extracting requirements: {e}")
            return None
    
    def generate_proposal(self, extracted_data: str) -> Optional[str]:
        """
        Generate a proposal from extracted requirements using Azure AI.
        
        Args:
            extracted_data: JSON string with requirements and metadata
            
        Returns:
            HTML content for the proposal or None if generation failed
        """
        try:
            logger.info("Generating proposal with Azure DeepSeek")
            
            # Parse extracted data
            try:
                data = json.loads(extracted_data)
            except json.JSONDecodeError:
                logger.error("Failed to parse extracted data")
                return None
            
            # Construct a prompt for the proposal generation
            proposal_prompt = f"""
            Create a professional project proposal based on the following data:
            {json.dumps(data, indent=2)}
            
            Format the proposal as clean markdown with the following sections:
            1. Executive Summary
            2. Client Overview
            3. Project Scope
            4. Approach & Methodology
            5. Timeline & Milestones
            6. Budget & Pricing
            7. Team & Resources
            8. Next Steps
            
            Use a clean, professional style with proper markdown formatting.
            Include all the requirements mentioned.
            """
            
            # Generate the proposal HTML
            response = self.client.complete(
                messages=[
                    SystemMessage(content="You are an AI assistant that creates professional project proposals in HTML format."),
                    UserMessage(content=proposal_prompt)
                ],
                model_extras={
                    "safe_mode": True
                },
                temperature=0.4
            )
            
            if not response:
                logger.error("Failed to generate proposal")
                return None
                
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating proposal: {e}")
            return None
    
    def improve_proposal(self, feedback: str, current_html: str) -> Optional[str]:
        """
        Improve a proposal based on feedback using Azure AI.
        
        Args:
            feedback: Feedback on what to improve
            current_html: Current HTML content of the proposal
            
        Returns:
            Improved HTML content or None if improvement failed
        """
        try:
            logger.info("Improving proposal with Azure DeepSeek")
            
            # Construct a prompt for the improvement
            improvement_prompt = f"""
            Improve the following proposal HTML based on this feedback:
            
            FEEDBACK:
            {feedback}
            
            CURRENT HTML:
            {current_html}
            
            Make the requested changes while preserving the overall structure.
            Return the complete improved HTML.
            """
            
            # Generate the improved HTML
            response = self.client.complete(
                messages=[
                    SystemMessage(content="You are an AI assistant that improves project proposals based on feedback."),
                    UserMessage(content=improvement_prompt)
                ],
                model_extras={
                    "safe_mode": True
                },
                temperature=0.2
            )
            
            if not response:
                logger.error("Failed to improve proposal")
                return None
                
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error improving proposal: {e}")
            return None
    
    def review_document(self, document_content: str) -> Dict[str, Any]:
        """
        Review a document for quality, completeness, and issues using Azure AI.
        
        Args:
            document_content: Content of the document to review
            
        Returns:
            Dictionary with review results
        """
        try:
            logger.info("Reviewing document with Azure DeepSeek")
            
            # Construct a prompt for the document review
            review_prompt = f"""
            Review the following document content for quality, completeness, and issues.
            Provide a structured analysis in JSON format with these fields:
            - score: Overall quality score (0.0 to 1.0)
            - strengths: List of document strengths
            - weaknesses: List of document weaknesses
            - suggestions: List of specific improvement suggestions
            - missing_elements: List of important elements that might be missing
            
            DOCUMENT:
            {document_content[:2000]}... (truncated for brevity)
            """
            
            # Generate the review
            response = self.client.complete(
                messages=[
                    SystemMessage(content="You are an AI assistant that reviews documents and provides structured feedback in JSON format."),
                    UserMessage(content=review_prompt)
                ],
                model_extras={
                    "safe_mode": True
                },
                temperature=0.3
            )
            
            if not response:
                logger.error("Failed to review document")
                return {
                    "status": "error",
                    "message": "Failed to generate review",
                    "score": 0,
                    "suggestions": []
                }
            
            # Parse review results
            try:
                review_data = json.loads(response.choices[0].message.content)
                return {
                    "status": "success",
                    "score": review_data.get("score", 0),
                    "strengths": review_data.get("strengths", []),
                    "weaknesses": review_data.get("weaknesses", []),
                    "suggestions": review_data.get("suggestions", []),
                    "missing_elements": review_data.get("missing_elements", [])
                }
            except json.JSONDecodeError:
                logger.error("Failed to parse review results as JSON")
                return {
                    "status": "error",
                    "message": "Invalid review format",
                    "score": 0,
                    "suggestions": []
                }
                
        except Exception as e:
            logger.error(f"Error reviewing document: {e}")
            return {
                "status": "error",
                "message": str(e),
                "score": 0,
                "suggestions": []
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Check the health status of the Azure AI service.
        
        Returns:
            Dictionary with status information
        """
        status = {
            "service": "azure_model_service",
            "status": "unknown",
            "details": {}
        }
        
        try:
            # Simple check - try to generate a short text
            response = self.client.complete(
                messages=[UserMessage(content="Hello, this is a test.")],
                model_extras={"safe_mode": True},
                temperature=0
            )
            
            if response and response.choices:
                status["status"] = "healthy"
                status["details"]["test_response"] = response.choices[0].message.content
            else:
                status["status"] = "error"
                status["details"]["error"] = "Failed to generate test response"
                
        except Exception as e:
            status["status"] = "error"
            status["details"]["error"] = str(e)
            
        return status 
