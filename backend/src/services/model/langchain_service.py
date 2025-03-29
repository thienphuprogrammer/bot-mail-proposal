from typing import Dict, Any, Optional
import json
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent
from langchain.prompts import StringPromptTemplate
from langchain.schema import AgentAction, AgentFinish
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.output_parsers import RegexParser
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from src.core.config import settings
from src.models.proposal import ExtractedData
from src.prompts.base_prompts import PromptRegistry
from src.services.model.base_model import AIService

class LangChainService(AIService):
    """Service for LangChain operations."""
    
    def __init__(self):
        """Initialize the LangChain service."""
        self.llm = ChatOpenAI(
            model=settings.LANGCHAIN_MODEL,
            temperature=settings.LANGCHAIN_TEMPERATURE,
            openai_api_key=settings.OPENAI_API_KEY
        )
    
    def extract_requirements(self, email_body: str) -> Optional[ExtractedData]:
        """Extract requirements from email body."""
        try:
            # Get prompt from registry
            prompt = PromptRegistry.get("openai_requirement_extraction")
            
            # Format user content
            user_content = prompt.format_user_content(email_content=email_body)
            
            # Create prompt for LLM
            full_prompt = f"{prompt.system_content}\n\n{user_content}"
            
            # Get response
            response = self.llm.predict(full_prompt)
            
            # Clean and parse response
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
            print(f"Error extracting requirements: {e}")
            return None
    
    def generate_proposal(self, extracted_data: ExtractedData) -> Optional[str]:
        """Generate a proposal HTML from extracted data."""
        try:
            # Get prompt from registry
            prompt = PromptRegistry.get("openai_proposal_generation")
            
            # Format variables for template
            features_str = ", ".join(extracted_data.features)
            budget_str = f"${extracted_data.budget}" if extracted_data.budget else "Not specified"
            
            # Format user content
            user_content = prompt.format_user_content(
                project_name=extracted_data.project_name,
                description=extracted_data.description,
                features=features_str,
                deadline=extracted_data.deadline,
                budget=budget_str
            )
            
            # Create prompt for LLM
            full_prompt = f"{prompt.system_content}\n\n{user_content}"
            
            # Get response
            response = self.llm.predict(full_prompt)
            
            # Clean response
            response = response.strip()
            if response.startswith("```html"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            return response.strip()
        except Exception as e:
            print(f"Error generating proposal: {e}")
            return None
    
    def generate_pdf(self, html_content: str, output_path: str) -> bool:
        """Generate PDF from HTML content."""
        try:
            # Get prompt from registry  
            prompt = PromptRegistry.get("openai_pdf_generation")
            
            # Format user content (truncate html to reasonable size)
            truncated_html = html_content[:1000] + "..." if len(html_content) > 1000 else html_content
            user_content = prompt.format_user_content(
                html_content=truncated_html,
                output_path=output_path
            )
            
            # Create prompt for LLM
            full_prompt = f"{prompt.system_content}\n\n{user_content}"
            
            # In a real implementation, we would use a PDF generation library here
            # For now, write a placeholder file
            with open(output_path, "w") as f:
                f.write("PDF content would go here - generated via LangChain")
            
            return True
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return False
    
    def create_pdf_agent(self) -> AgentExecutor:
        """Create an agent for PDF generation."""
        # Define tools
        class GeneratePDFInput(BaseModel):
            """Input for GeneratePDF tool."""
            html_content: str = Field(description="HTML content to convert to PDF")
            output_path: str = Field(description="Path to save the PDF file")
            
        class GeneratePDFTool(BaseTool):
            """Tool for generating PDF from HTML."""
            name = "GeneratePDF"
            description = "Generate a PDF file from HTML content"
            args_schema = GeneratePDFInput
            
            def _run(self, html_content: str, output_path: str) -> str:
                # In a real implementation, this would use a PDF generation library
                # For demonstration, just pretending to generate a PDF
                with open(output_path, "w") as f:
                    f.write("PDF content would go here")
                return f"PDF generated and saved to {output_path}"
            
            def _arun(self, html_content: str, output_path: str):
                raise NotImplementedError("This tool does not support async")
        
        # Create tools
        tools = [
            GeneratePDFTool(),
        ]
        
        # Create agent with tools
        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self._create_agent(),
            tools=tools,
            verbose=True
        )
        
        return agent_executor
    
    def _create_agent(self) -> LLMSingleActionAgent:
        """Create an LLM agent."""
        # Get prompt from registry
        prompt = PromptRegistry.get("openai_pdf_generation")
        
        # Create a simplified prompt template
        prompt_template = f"{prompt.system_content}\n\nYou have access to the following tools:\n\nGeneratePDF: Generate a PDF file from HTML content\n\nUse the tools to accomplish the task."
        
        # In a real implementation, this would be more sophisticated
        llm_chain = LLMChain(llm=self.llm, prompt=StringPromptTemplate.from_template(prompt_template))
        
        # Create agent
        agent = LLMSingleActionAgent(
            llm_chain=llm_chain,
            output_parser=RegexParser(
                regex=r"Action: (.*)\nAction Input: (.*)",
                output_keys=["action", "action_input"]
            ),
            stop=["\nObservation:"],
            allowed_tools=["GeneratePDF"]
        )
        
        return agent 