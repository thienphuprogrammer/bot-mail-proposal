from typing import Dict, Any, List, Optional
import json
import os
from datetime import datetime
from bson import ObjectId

from models.user import PyObjectId
from repositories.base_repository import BaseRepository

class TemplateModel:
    """Model for template."""
    id: str
    name: str
    description: str
    html_content: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    def __init__(self, **kwargs):
        """Initialize template model."""
        self.id = str(kwargs.get("_id", ""))
        self.name = kwargs.get("name", "")
        self.description = kwargs.get("description", "")
        self.html_content = kwargs.get("html_content", "")
        self.created_by = str(kwargs.get("created_by", ""))
        self.created_at = kwargs.get("created_at", datetime.utcnow())
        self.updated_at = kwargs.get("updated_at", datetime.utcnow())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dict."""
        return {
            "name": self.name,
            "description": self.description,
            "html_content": self.html_content,
            "created_by": ObjectId(self.created_by) if self.created_by else None,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class TemplateService:
    """Service for managing proposal templates."""
    
    def __init__(self, template_repository: BaseRepository):
        """Initialize template service."""
        self.template_repository = template_repository
        
        # Create templates directory if it doesn't exist
        self.templates_dir = os.path.join("templates")
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Create default templates if they don't exist
        self._create_default_templates()
    
    def _create_default_templates(self) -> None:
        """Create default templates if they don't exist."""
        default_templates = [
            {
                "name": "Basic Proposal",
                "description": "A simple proposal template for general purposes",
                "html_content": self._get_default_template_content("basic")
            },
            {
                "name": "Detailed Proposal",
                "description": "A comprehensive proposal template with detailed sections",
                "html_content": self._get_default_template_content("detailed")
            },
            {
                "name": "Technical Proposal",
                "description": "A proposal template focused on technical specifications",
                "html_content": self._get_default_template_content("technical")
            }
        ]
        
        for template in default_templates:
            # Check if template already exists
            existing = self.template_repository.find_all({"name": template["name"]})
            if not existing:
                # Create template
                self.template_repository.create(template)
    
    def _get_default_template_content(self, template_type: str) -> str:
        """Get default template content."""
        template_file = os.path.join(self.templates_dir, f"{template_type}_template.html")
        
        # Create template file if it doesn't exist
        if not os.path.exists(template_file):
            with open(template_file, "w") as f:
                f.write(self._get_template_html(template_type))
        
        # Read template file
        with open(template_file, "r") as f:
            return f.read()
    
    def _get_template_html(self, template_type: str) -> str:
        """Get template HTML."""
        if template_type == "basic":
            return """
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .header { text-align: center; margin-bottom: 30px; }
                    .section { margin-bottom: 20px; }
                    .section-title { font-weight: bold; margin-bottom: 10px; }
                    .footer { text-align: center; margin-top: 30px; font-size: 0.8em; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>{{project_name}}</h1>
                    <p>Proposal for {{client_name}}</p>
                </div>
                
                <div class="section">
                    <div class="section-title">Project Overview</div>
                    <p>{{description}}</p>
                </div>
                
                <div class="section">
                    <div class="section-title">Key Features</div>
                    <ul>
                        {{#each features}}
                        <li>{{this}}</li>
                        {{/each}}
                    </ul>
                </div>
                
                <div class="section">
                    <div class="section-title">Timeline</div>
                    <p>The project is expected to be completed by {{deadline}}.</p>
                </div>
                
                <div class="section">
                    <div class="section-title">Budget</div>
                    <p>The estimated cost for this project is {{budget}}.</p>
                </div>
                
                <div class="footer">
                    <p>Contact us at: contact@example.com</p>
                </div>
            </body>
            </html>
            """
        elif template_type == "detailed":
            return """
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .header { text-align: center; margin-bottom: 30px; }
                    .section { margin-bottom: 30px; }
                    .section-title { font-weight: bold; margin-bottom: 15px; font-size: 1.2em; }
                    .subsection { margin-bottom: 15px; }
                    .subsection-title { font-weight: bold; margin-bottom: 10px; }
                    .footer { text-align: center; margin-top: 40px; font-size: 0.8em; }
                    table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
                    th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
                    th { background-color: #f2f2f2; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>{{project_name}}</h1>
                    <p>Comprehensive Proposal for {{client_name}}</p>
                    <p>Priority: {{priority}}</p>
                </div>
                
                <div class="section">
                    <div class="section-title">1. Executive Summary</div>
                    <p>{{description}}</p>
                </div>
                
                <div class="section">
                    <div class="section-title">2. Project Scope</div>
                    <div class="subsection">
                        <div class="subsection-title">2.1 Objectives</div>
                        <p>{{objectives}}</p>
                    </div>
                    <div class="subsection">
                        <div class="subsection-title">2.2 Key Deliverables</div>
                        <ul>
                            {{#each features}}
                            <li>{{this}}</li>
                            {{/each}}
                        </ul>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">3. Methodology</div>
                    <p>{{methodology}}</p>
                </div>
                
                <div class="section">
                    <div class="section-title">4. Timeline</div>
                    <table>
                        <tr>
                            <th>Phase</th>
                            <th>Description</th>
                            <th>Duration</th>
                        </tr>
                        {{#each timeline}}
                        <tr>
                            <td>{{phase}}</td>
                            <td>{{description}}</td>
                            <td>{{duration}}</td>
                        </tr>
                        {{/each}}
                    </table>
                    <p>Project deadline: {{deadline}}</p>
                </div>
                
                <div class="section">
                    <div class="section-title">5. Budget</div>
                    <table>
                        <tr>
                            <th>Item</th>
                            <th>Cost</th>
                        </tr>
                        {{#each budget_items}}
                        <tr>
                            <td>{{item}}</td>
                            <td>{{cost}}</td>
                        </tr>
                        {{/each}}
                    </table>
                    <p>Total budget: {{budget}}</p>
                </div>
                
                <div class="section">
                    <div class="section-title">6. Client Requirements</div>
                    <p>{{client_requirements}}</p>
                </div>
                
                <div class="footer">
                    <p>Contact us at: contact@example.com | Phone: (123) 456-7890</p>
                </div>
            </body>
            </html>
            """
        elif template_type == "technical":
            return """
            <html>
            <head>
                <style>
                    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; }
                    .header { text-align: center; margin-bottom: 30px; }
                    .logo { text-align: center; margin-bottom: 20px; }
                    .section { margin-bottom: 25px; }
                    .section-title { font-weight: bold; margin-bottom: 15px; font-size: 1.2em; color: #2c3e50; }
                    .code { font-family: monospace; background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }
                    .table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
                    .table th, .table td { padding: 12px; text-align: left; border: 1px solid #ddd; }
                    .table th { background-color: #f8f9fa; }
                    .footer { text-align: center; margin-top: 40px; font-size: 0.8em; color: #7f8c8d; border-top: 1px solid #ecf0f1; padding-top: 20px; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>{{project_name}}</h1>
                    <p>Technical Proposal for {{client_name}}</p>
                </div>
                
                <div class="section">
                    <div class="section-title">1. Project Overview</div>
                    <p>{{description}}</p>
                </div>
                
                <div class="section">
                    <div class="section-title">2. Technical Specifications</div>
                    <div class="table-container">
                        <table class="table">
                            <tr>
                                <th>Component</th>
                                <th>Description</th>
                                <th>Technology</th>
                            </tr>
                            {{#each technical_specs}}
                            <tr>
                                <td>{{component}}</td>
                                <td>{{description}}</td>
                                <td>{{technology}}</td>
                            </tr>
                            {{/each}}
                        </table>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">3. Implementation Details</div>
                    <ul>
                        {{#each features}}
                        <li>{{this}}</li>
                        {{/each}}
                    </ul>
                </div>
                
                <div class="section">
                    <div class="section-title">4. System Requirements</div>
                    <div class="code">
                        {{system_requirements}}
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">5. Development Timeline</div>
                    <p>The development is estimated to be completed by {{deadline}}.</p>
                </div>
                
                <div class="section">
                    <div class="section-title">6. Cost Estimation</div>
                    <p>The total cost for implementation is estimated at {{budget}}.</p>
                </div>
                
                <div class="footer">
                    <p>This technical proposal is confidential and proprietary.</p>
                    <p>Contact: tech-team@example.com | Support: (123) 456-7890</p>
                </div>
            </body>
            </html>
            """
        else:
            return "<p>Default template content</p>"
    
    def get_all_templates(self) -> List[TemplateModel]:
        """Get all templates."""
        templates = self.template_repository.find_all({})
        return [TemplateModel(**template) for template in templates]
    
    def get_template(self, template_id: str) -> Optional[TemplateModel]:
        """Get template by ID."""
        template = self.template_repository.find_by_id(template_id)
        return TemplateModel(**template) if template else None
    
    def create_template(self, name: str, description: str, html_content: str, user_id: str) -> TemplateModel:
        """Create a new template."""
        template_data = {
            "name": name,
            "description": description,
            "html_content": html_content,
            "created_by": ObjectId(user_id),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        template = self.template_repository.create(template_data)
        return TemplateModel(**template)
    
    def update_template(self, template_id: str, update_data: Dict[str, Any]) -> Optional[TemplateModel]:
        """Update template."""
        update_data["updated_at"] = datetime.utcnow()
        template = self.template_repository.update(template_id, update_data)
        return TemplateModel(**template) if template else None
    
    def delete_template(self, template_id: str) -> bool:
        """Delete template."""
        return self.template_repository.delete(template_id)
    
    def render_template(self, template_id: str, context: Dict[str, Any]) -> Optional[str]:
        """Render template with context."""
        import pystache
        
        template = self.get_template(template_id)
        if not template:
            return None
        
        return pystache.render(template.html_content, context) 