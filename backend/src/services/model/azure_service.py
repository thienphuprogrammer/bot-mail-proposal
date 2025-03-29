import os
import json
from typing import Dict, Any, Optional, List

from azure.ai.inference import ChatCompletionsClient

from src.core.config import settings
from src.models.proposal import ExtractedData
from src.prompts.base_prompts import PromptRegistry
from src.services.model.base_model import AIService

class AzureDeepseekService(AIService):
    """Service for Azure OpenAI with deepseek model operations."""
    
    def __init__(self):
        """Initialize the Azure Deepseek service."""
        self.client = ChatCompletionsClient(
            endpoint=settings.AZURE_OPENAI_ENDPOINT,
            credential=settings.AZURE_OPENAI_API_KEY
        )
        self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT
    
    def _call_azure_api(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> Optional[str]:
        """Call Azure OpenAI API with the deepseek model."""
        try:
            # Create message list
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Call API
            response = self.client.complete(
                self.deployment_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling Azure API: {str(e)}")
            return None
    
    def extract_requirements(self, email_body: str) -> Optional[ExtractedData]:
        """Extract requirements from email body using Azure Deepseek model."""
        try:
            # Get prompt from registry
            prompt = PromptRegistry.get("azure_requirement_extraction")
            
            # Format user content
            user_prompt = prompt.format_user_content(email_content=email_body)
            
            # Call API
            response = self._call_azure_api(
                system_prompt=prompt.system_content,
                user_prompt=user_prompt,
                temperature=0.1
            )
            
            if not response:
                return None
                
            # Clean response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            # Parse JSON
            data = json.loads(response.strip())
            
            # Create ExtractedData instance
            return ExtractedData(
                project_name=data["project_name"],
                description=data["description"],
                features=data["features"],
                deadline=data["deadline"],
                budget=data.get("budget")
            )
        except Exception as e:
            print(f"Error extracting requirements with Azure: {e}")
            return None
    
    def generate_proposal(self, extracted_data: ExtractedData) -> Optional[str]:
        """Generate a proposal HTML from extracted data using Azure Deepseek model."""
        try:
            # Get prompt from registry
            prompt = PromptRegistry.get("azure_proposal_generation")
            
            # Format variables for template
            features_str = ", ".join(extracted_data.features)
            budget_str = f"${extracted_data.budget}" if extracted_data.budget else "Not specified"
            
            # Format user content
            user_prompt = prompt.format_user_content(
                project_name=extracted_data.project_name,
                description=extracted_data.description,
                features=features_str,
                deadline=extracted_data.deadline,
                budget=budget_str
            )
            
            # Call API
            response = self._call_azure_api(
                system_prompt=prompt.system_content,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=4000
            )
            
            if not response:
                return None
            
            # Clean response
            response = response.strip()
            if response.startswith("```html"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            return response.strip()
        except Exception as e:
            print(f"Error generating proposal with Azure: {e}")
            return None
    
    def generate_pdf(self, html_content: str, output_path: str) -> bool:
        """Generate PDF from HTML content using Azure Deepseek model."""
        try:
            # Get prompt from registry
            prompt = PromptRegistry.get("azure_pdf_generation")
            
            # Format user content (truncate html to reasonable size)
            truncated_html = html_content[:1000] + "..." if len(html_content) > 1000 else html_content
            user_prompt = prompt.format_user_content(
                html_content=truncated_html,
                output_path=output_path
            )
            
            # Call API
            response = self._call_azure_api(
                system_prompt=prompt.system_content,
                user_prompt=user_prompt,
                temperature=0.3,
                max_tokens=500
            )
            
            # In a real implementation, we would use a PDF generation library here
            # For now, write a placeholder file
            with open(output_path, "w") as f:
                f.write("PDF content would go here - generated via Azure Deepseek model")
            
            return True
        except Exception as e:
            print(f"Error generating PDF with Azure: {e}")
            return False 