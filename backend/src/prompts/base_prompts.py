"""
Base prompt management system for all AI models.
"""
from typing import Dict, Any, Optional
import json

class Prompt:
    """Base class for managing prompts."""
    
    def __init__(self, name: str, system_content: str, user_template: str):
        """Initialize a prompt with system content and user template.
        
        Args:
            name: The name of the prompt
            system_content: The system content to set context for the model
            user_template: The user template with {placeholders} for formatting
        """
        self.name = name
        self.system_content = system_content
        self.user_template = user_template
    
    def format_user_content(self, **kwargs) -> str:
        """Format the user template with provided variables.
        
        Args:
            **kwargs: The variables to format the template with
            
        Returns:
            The formatted user content
        """
        try:
            return self.user_template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required variable for prompt template: {e}")
        except Exception as e:
            raise ValueError(f"Error formatting prompt template: {e}")


class PromptRegistry:
    """Registry for managing and retrieving prompts."""
    
    _prompts: Dict[str, Prompt] = {}
    
    @classmethod
    def register(cls, name: str, prompt: Optional[Prompt] = None, system_content: str = None, user_template: str = None) -> Prompt:
        """Register a new prompt.
        
        Args:
            name: The name of the prompt
            prompt: A Prompt object to register
            system_content: The system content to set context for the model (if prompt not provided)
            user_template: The user template with {placeholders} for formatting (if prompt not provided)
            
        Returns:
            The registered prompt
        """
        if prompt is not None:
            # Register an existing Prompt object
            cls._prompts[name] = prompt
            return prompt
        elif system_content is not None and user_template is not None:
            # Create and register a new Prompt
            prompt = Prompt(name, system_content, user_template)
            cls._prompts[name] = prompt
            return prompt
        else:
            raise ValueError("Either prompt object or both system_content and user_template must be provided")
    
    @classmethod
    def get(cls, name: str) -> Prompt:
        """Get a prompt by name.
        
        Args:
            name: The name of the prompt
            
        Returns:
            The prompt
            
        Raises:
            ValueError: If the prompt is not found
        """
        if name not in cls._prompts:
            raise ValueError(f"Prompt not found: {name}")
        
        return cls._prompts[name]
    
    @classmethod
    def list_prompts(cls) -> Dict[str, str]:
        """List all registered prompts.
        
        Returns:
            A dictionary of prompt names and descriptions
        """
        return {name: prompt.system_content.split('\n')[0] for name, prompt in cls._prompts.items()} 