"""
Prompt manager for loading, validating, and providing prompts.
Allows for centralized management of prompts for different AI providers.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import logging
from jinja2 import Template

from src.core.config import settings
from src.core.const import TEMPLATES_DIR

# Setup logger
logger = logging.getLogger(__name__)


class PromptManager:
    """
    Manager for AI prompts that handles loading, validation and rendering.
    Supports different model providers and prompt formats.
    """
    
    def __init__(self):
        self.prompts = {}
        self.prompt_configs = {}
        self.load_all_prompts()
        
    def load_all_prompts(self) -> None:
        """Load all prompt configurations."""
        # Determine which provider to use
        use_azure = settings.USE_AZURE_AI
        
        # Load base prompts
        base_prompts = self._load_prompts_module("base_prompts")
        
        # Load provider-specific prompts
        provider_module = "azure_prompts" if use_azure else "openai_prompts"
        provider_prompts = self._load_prompts_module(provider_module)
        
        # Merge prompts (provider-specific override base)
        self.prompts = {**base_prompts, **provider_prompts}
        
        # Load custom prompts from files if available
        custom_prompts_dir = Path(TEMPLATES_DIR) / "prompts"
        if custom_prompts_dir.exists():
            custom_prompts = self._load_prompts_from_directory(custom_prompts_dir)
            # Custom prompts override default ones
            self.prompts.update(custom_prompts)
            
        logger.info(f"Loaded {len(self.prompts)} prompts")
        
    def _load_prompts_module(self, module_name: str) -> Dict[str, Any]:
        """
        Load prompts from a Python module.
        
        Args:
            module_name: Name of the module to import
            
        Returns:
            Dictionary of prompts
        """
        try:
            # Dynamic import
            module = __import__(f"src.prompts.{module_name}", fromlist=["PROMPTS"])
            return getattr(module, "PROMPTS", {})
        except (ImportError, AttributeError) as e:
            logger.warning(f"Failed to load prompts from module {module_name}: {e}")
            return {}
            
    def _load_prompts_from_directory(self, directory: Path) -> Dict[str, Any]:
        """
        Load prompts from JSON files in a directory.
        
        Args:
            directory: Path to directory containing prompt files
            
        Returns:
            Dictionary of prompts
        """
        prompts = {}
        
        if not directory.exists():
            return prompts
            
        for file_path in directory.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    prompt_data = json.load(f)
                    
                # Use filename (without extension) as key if not specified
                prompt_name = file_path.stem
                if isinstance(prompt_data, dict) and "name" in prompt_data:
                    prompt_name = prompt_data.pop("name")
                    
                prompts[prompt_name] = prompt_data
                logger.debug(f"Loaded prompt '{prompt_name}' from {file_path}")
                
            except Exception as e:
                logger.warning(f"Failed to load prompt file {file_path}: {e}")
                
        return prompts
    
    def get_prompt(self, prompt_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a prompt by name.
        
        Args:
            prompt_name: Name of the prompt
            
        Returns:
            Prompt configuration or None if not found
        """
        return self.prompts.get(prompt_name)
    
    def render_prompt(self, prompt_name: str, **kwargs) -> Optional[Union[str, Dict[str, Any]]]:
        """
        Render a prompt with given variables.
        
        Args:
            prompt_name: Name of the prompt
            **kwargs: Variables to render the prompt with
            
        Returns:
            Rendered prompt (string or dict depending on prompt type)
        """
        prompt_template = self.get_prompt(prompt_name)
        if not prompt_template:
            logger.warning(f"Prompt '{prompt_name}' not found")
            return None
            
        # For string prompts, use Jinja2 template rendering
        if isinstance(prompt_template, str):
            template = Template(prompt_template)
            return template.render(**kwargs)
            
        # For structured prompts (dict), render any string values
        elif isinstance(prompt_template, dict):
            return self._render_structured_prompt(prompt_template, kwargs)
            
        # For list prompts (like few-shot examples)
        elif isinstance(prompt_template, list):
            return [
                self._render_structured_prompt(item, kwargs) 
                if isinstance(item, dict) else item 
                for item in prompt_template
            ]
            
        return prompt_template
        
    def _render_structured_prompt(self, template: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively render a structured (dict) prompt.
        
        Args:
            template: Prompt template dictionary
            variables: Variables to render with
            
        Returns:
            Rendered prompt dictionary
        """
        result = {}
        
        for key, value in template.items():
            if isinstance(value, str):
                # Render string values with Jinja2
                template_obj = Template(value)
                result[key] = template_obj.render(**variables)
            elif isinstance(value, dict):
                # Recursively render nested dictionaries
                result[key] = self._render_structured_prompt(value, variables)
            elif isinstance(value, list):
                # Render lists, processing dict items
                result[key] = [
                    self._render_structured_prompt(item, variables) 
                    if isinstance(item, dict) 
                    else item
                    for item in value
                ]
            else:
                # Keep other values as is
                result[key] = value
                
        return result
    
    def list_available_prompts(self) -> List[str]:
        """
        List all available prompt names.
        
        Returns:
            List of prompt names
        """
        return list(self.prompts.keys())
    
    def add_prompt(self, name: str, prompt: Any) -> None:
        """
        Add or update a prompt.
        
        Args:
            name: Prompt name
            prompt: Prompt content
        """
        self.prompts[name] = prompt
        
    def save_prompt(self, name: str, directory: Optional[Path] = None) -> bool:
        """
        Save a prompt to a JSON file.
        
        Args:
            name: Prompt name
            directory: Directory to save to (defaults to templates/prompts)
            
        Returns:
            True if saved successfully, False otherwise
        """
        if name not in self.prompts:
            logger.warning(f"Cannot save: prompt '{name}' not found")
            return False
            
        if directory is None:
            directory = Path(TEMPLATES_DIR) / "prompts"
            
        os.makedirs(directory, exist_ok=True)
        
        try:
            prompt_data = self.prompts[name]
            file_path = directory / f"{name}.json"
            
            # If not a dict already, wrap in a dict with name
            if not isinstance(prompt_data, dict):
                prompt_data = {"content": prompt_data}
                
            # Add name to the data
            save_data = {"name": name, **prompt_data}
            
            with open(file_path, "w") as f:
                json.dump(save_data, f, indent=2)
                
            logger.info(f"Saved prompt '{name}' to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save prompt '{name}': {e}")
            return False


# Singleton instance
prompt_manager = PromptManager() 