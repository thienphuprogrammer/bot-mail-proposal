"""
PDF rendering for proposals.
"""

import os
import logging
import tempfile
from typing import Optional, Dict, Any
from datetime import datetime

import pdfkit
from bs4 import BeautifulSoup

from services.proposal.core.interfaces import ProposalRenderer
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)

class PDFProposalRenderer(ProposalRenderer):
    """Renders proposals as PDF documents using wkhtmltopdf."""
    
    def __init__(self, proposal_repository: BaseRepository):
        """
        Initialize the PDF proposal renderer.
        
        Args:
            proposal_repository: Repository for retrieving proposals
        """
        self.proposal_repository = proposal_repository
        
        # Configure PDF generation options
        self.pdf_options = {
            'page-size': 'A4',
            'margin-top': '20mm',
            'margin-right': '20mm',
            'margin-bottom': '20mm',
            'margin-left': '20mm',
            'encoding': 'UTF-8',
            'no-outline': None,
            'enable-local-file-access': None,
        }
        
        # Create temp directories
        os.makedirs("temp", exist_ok=True)
        os.makedirs(os.path.join("temp", "proposals"), exist_ok=True)
        
        logger.info("Initialized PDF proposal renderer")
    
    def render_html(self, proposal_id: str) -> str:
        """
        Render a proposal as HTML.
        
        Args:
            proposal_id: ID of the proposal to render
            
        Returns:
            HTML representation of the proposal
        """
        try:
            # Get the proposal
            proposal = self.proposal_repository.find_by_id(proposal_id)
            if not proposal:
                logger.error(f"Proposal not found: {proposal_id}")
                return ""
                
            # Get the latest version
            if not proposal.versions or len(proposal.versions) == 0:
                logger.error(f"Proposal has no versions: {proposal_id}")
                return ""
                
            latest_version = max(proposal.versions, key=lambda v: v.version)
            html_content = latest_version.html_content
            
            # Add CSS for better printing if not already included
            if "<style>" not in html_content:
                html_content = self._add_print_styles(html_content)
                
            return html_content
            
        except Exception as e:
            logger.error(f"Error rendering HTML: {str(e)}")
            return ""
    
    def generate_pdf(self, proposal_id: str, output_dir: str = "temp") -> Optional[str]:
        """
        Generate a PDF version of a proposal.
        
        Args:
            proposal_id: ID of the proposal to convert
            output_dir: Directory to save the PDF
            
        Returns:
            Path to the generated PDF file or None if failed
        """
        try:
            # Ensure the output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Get the proposal HTML
            html_content = self.render_html(proposal_id)
            if not html_content:
                logger.error(f"Failed to get HTML content for proposal: {proposal_id}")
                return None
                
            # Get the proposal for metadata
            proposal = self.proposal_repository.find_by_id(proposal_id)
            if not proposal:
                logger.error(f"Proposal not found: {proposal_id}")
                return None
                
            # Create a filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c if c.isalnum() else "_" for c in proposal.project_title)
            filename = f"{safe_title}_{timestamp}.pdf"
            output_path = os.path.join(output_dir, filename)
            
            # Create a temporary HTML file
            with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode='w', encoding='utf-8') as temp_html:
                temp_html.write(html_content)
                temp_html_path = temp_html.name
            
            try:
                # Convert HTML to PDF
                logger.info(f"Generating PDF for proposal {proposal_id} to {output_path}")
                pdfkit.from_file(temp_html_path, output_path, options=self.pdf_options)
                
                # Update the proposal with the PDF path
                self.proposal_repository.update(
                    proposal_id,
                    {"pdf_path": output_path}
                )
                
                logger.info(f"PDF generated successfully: {output_path}")
                return output_path
                
            finally:
                # Clean up the temporary HTML file
                if os.path.exists(temp_html_path):
                    os.unlink(temp_html_path)
                    
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            return None
    
    def generate_docx(self, proposal_id: str, output_dir: str = "temp") -> Optional[str]:
        """
        Generate a DOCX version of a proposal.
        
        Args:
            proposal_id: ID of the proposal to convert
            output_dir: Directory to save the DOCX
            
        Returns:
            Path to the generated DOCX file or None if failed
        """
        try:
            # Use a third-party library like python-docx or htmldocx to convert
            # This is a placeholder implementation - in a real system you would
            # implement the actual DOCX conversion logic
            
            # For now, just log a warning
            logger.warning("DOCX generation not fully implemented")
            
            # Create a dummy file to indicate the feature is not complete
            os.makedirs(output_dir, exist_ok=True)
            dummy_file = os.path.join(output_dir, f"proposal_{proposal_id}_docx_not_implemented.txt")
            
            with open(dummy_file, 'w') as f:
                f.write("DOCX generation not fully implemented")
                
            return dummy_file
            
        except Exception as e:
            logger.error(f"Error generating DOCX: {str(e)}")
            return None
    
    def apply_template(self, proposal_html: str, template_id: str) -> str:
        """
        Apply a template to a proposal's content.
        
        Args:
            proposal_html: HTML content of the proposal
            template_id: ID of the template to apply
            
        Returns:
            HTML with the template applied
        """
        try:
            # In a real implementation, you would fetch the template from a database
            # and merge it with the proposal content
            
            # This is a simple placeholder implementation
            soup = BeautifulSoup(proposal_html, 'html.parser')
            
            # Create a basic template structure
            template = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Project Proposal</title>
                <style>
                    @page {{
                        size: A4;
                        margin: 2cm;
                    }}
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 30px;
                        border-bottom: 1px solid #ddd;
                        padding-bottom: 10px;
                    }}
                    .logo {{
                        max-width: 200px;
                        height: auto;
                    }}
                    .footer {{
                        text-align: center;
                        margin-top: 30px;
                        border-top: 1px solid #ddd;
                        padding-top: 10px;
                        font-size: 0.8em;
                        color: #666;
                    }}
                    h1, h2, h3, h4 {{
                        color: #0066cc;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 20px 0;
                    }}
                    th, td {{
                        border: 1px solid #ddd;
                        padding: 8px;
                    }}
                    th {{
                        background-color: #f2f2f2;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <img src="logo.png" alt="Company Logo" class="logo">
                    <h1>Project Proposal</h1>
                    <p>Template ID: {template_id}</p>
                </div>
                
                <div class="content">
                    {proposal_html}
                </div>
                
                <div class="footer">
                    <p>Generated on {datetime.now().strftime("%Y-%m-%d")} | Contact: info@company.com</p>
                </div>
            </body>
            </html>
            """
            
            return template
            
        except Exception as e:
            logger.error(f"Error applying template: {str(e)}")
            return proposal_html
    
    def _add_print_styles(self, html_content: str) -> str:
        """Add CSS styles for better printing."""
        css = """
        <style>
            @page {
                size: A4;
                margin: 2cm;
            }
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }
            h1 {
                color: #0066cc;
                font-size: 24px;
            }
            h2 {
                color: #0066cc;
                font-size: 20px;
            }
            h3 {
                color: #0066cc;
                font-size: 16px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
            }
            th {
                background-color: #f2f2f2;
            }
            .section {
                margin-bottom: 20px;
            }
            .page-break {
                page-break-after: always;
            }
        </style>
        """
        
        # Add the CSS to the head or create a head if it doesn't exist
        if "<head>" in html_content:
            html_content = html_content.replace("<head>", f"<head>\n{css}")
        elif "<html>" in html_content:
            html_content = html_content.replace("<html>", f"<html>\n<head>{css}</head>")
        else:
            html_content = f"<html><head>{css}</head><body>{html_content}</body></html>"
            
        return html_content 