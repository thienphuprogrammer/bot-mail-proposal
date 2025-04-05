"""
PDF rendering for proposals.
"""

import os
import logging
import tempfile
from typing import Optional
from datetime import datetime
import markdown
from services.proposal.core.interfaces import ProposalRenderer
from repositories.base_repository import BaseRepository
import re

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
        self.wkhtmltopdf_path = "D:/wkhtmltopdf/bin/wkhtmltopdf.exe"
        self.pdf_options = {
            'page-size': 'A4',
            'margin-top': '25mm',
            'margin-right': '20mm',
            'margin-bottom': '25mm',
            'margin-left': '20mm',
            'encoding': 'UTF-8',
            'no-outline': None,
            'enable-local-file-access': None,
            'footer-right': '[page] of [topage]',
            'footer-font-size': '9',
            'footer-line': True,
            'header-right': '[date]',
            'header-font-size': '9',
            'print-media-type': None,
            'dpi': 300,
            'image-quality': 100,
            'zoom': 1.0
        }
        os.makedirs("temp/proposals", exist_ok=True)

    def _get_proposal_content(self, proposal_id: str) -> Optional[str]:
        """
        Get the markdown content from the latest proposal version.

        Args:
            proposal_id: ID of the proposal

        Returns:
            Markdown content or None if not found
        """
        proposal = self.proposal_repository.find_by_id(proposal_id)
        if not proposal or not proposal.proposal_versions:
            logger.error(f"Proposal not found or has no versions: {proposal_id}")
            return None
        latest_version = max(proposal.proposal_versions, key=lambda v: v.version)
        return latest_version.content

    def _remove_think_tags(self, content: str) -> str:
        """
        Remove content inside <think> tags.

        Args:
            content: The markdown text with potential <think> tags

        Returns:
            Content with <think> sections removed
        """
        pattern = r'<think>.*?</think>'
        return re.sub(pattern, '', content, flags=re.DOTALL)

    def _get_css(self) -> str:
        """
        Get the CSS for the proposal.

        Returns:
            CSS string for styling the HTML
        """
        return """
        <style>
            @page { size: A4; margin: 2.54cm; }
            body { font-family: 'Calibri', 'Arial', sans-serif; font-size: 11pt; line-height: 1.15; color: #333333; margin: 0; padding: 0; }
            h1 { font-size: 16pt; color: #2E74B5; border-bottom: 1px solid #DEDEDE; padding-bottom: 3pt; }
            h2 { font-size: 14pt; color: #2E74B5; }
            h3 { font-size: 12pt; color: #2E74B5; }
            h4 { font-size: 11pt; color: #2E74B5; }
            h1, h2, h3, h4 { font-family: 'Calibri', 'Arial', sans-serif; margin-top: 12pt; margin-bottom: 6pt; line-height: 1.1; font-weight: bold; page-break-after: avoid; }
            p { margin-top: 0; margin-bottom: 10pt; }
            ul, ol { margin-top: 0; margin-bottom: 10pt; padding-left: 24pt; }
            li { margin-bottom: 4pt; }
            a { color: #0563C1; text-decoration: underline; }
            table { width: 100%; border-collapse: collapse; margin: 12pt 0; font-size: 10pt; table-layout: fixed; }
            table, th, td { border: 1px solid #D0D0D0; }
            th { background-color: #F2F2F2; font-weight: bold; text-align: left; padding: 6pt; }
            td { padding: 6pt; vertical-align: top; word-wrap: break-word; }
            tr:nth-child(even) { background-color: #F9F9F9; }
            blockquote { margin: 10pt 20pt; padding: 10pt; background-color: #F6F6F6; border-left: 3pt solid #CCCCCC; font-style: italic; }
            code { font-family: 'Consolas', 'Courier New', monospace; background-color: #F8F8F8; padding: 2pt 4pt; border: 1px solid #E0E0E0; border-radius: 3pt; font-size: 10pt; }
            pre { font-family: 'Consolas', 'Courier New', monospace; background-color: #F8F8F8; padding: 10pt; border: 1px solid #E0E0E0; border-radius: 3pt; overflow-x: auto; margin: 10pt 0; font-size: 10pt; white-space: pre-wrap; }
            img { max-width: 100%; height: auto; }
            .header { text-align: right; margin-bottom: 20pt; color: #666666; font-size: 9pt; }
            .footer { text-align: center; margin-top: 20pt; color: #666666; font-size: 9pt; border-top: 1pt solid #DEDEDE; padding-top: 5pt; }
            .main-heading { font-size: 18pt; color: #1F4E79; text-transform: uppercase; border-bottom: 2px solid #1F4E79; padding-bottom: 5pt; margin-top: 16pt; }
            .sub-heading { font-size: 16pt; color: #2E74B5; border-bottom: 1px solid #DEDEDE; }
            strong, b { font-weight: bold; color: #1F4E79; }
            em, i { font-style: italic; color: #444444; }
            .important-text { font-weight: bold; color: #C00000; text-transform: uppercase; margin-right: 5pt; }
            .note-text { font-weight: bold; color: #1F4E79; text-transform: uppercase; margin-right: 5pt; }
            .highlight { background-color: #F8F8F8; padding: 10pt; border: 1px solid #E0E0E0; border-radius: 3pt; margin: 10pt 0; }
            .highlight pre { margin: 0; padding: 0; border: none; }
            .toc { background-color: #F6F6F6; padding: 15pt; margin: 15pt 0; border: 1px solid #E0E0E0; border-radius: 3pt; }
            .toc ul { padding-left: 20pt; }
            .toc li { margin-bottom: 5pt; }
            .toc a { text-decoration: none; color: #2E74B5; }
        </style>
        """

    def _convert_to_styled_html(self, content: str) -> str:
        """
        Convert markdown to HTML with styling.

        Args:
            content: The markdown text to convert

        Returns:
            HTML with styling
        """
        cleaned_content = self._remove_think_tags(content)
        
        # Ensure tables have proper formatting by normalizing table syntax
        # Fix issue with tables not rendering properly
        table_pattern = r'(\n\s*\|[^\n]+\|\s*\n\s*\|[\-\|]+\|\s*\n)'
        
        def fix_table(match):
            table_header = match.group(0)
            # Ensure there's a blank line before the table
            if not table_header.startswith('\n\n'):
                table_header = '\n\n' + table_header
            return table_header
            
        cleaned_content = re.sub(table_pattern, fix_table, cleaned_content)
        
        html_content = markdown.markdown(
            cleaned_content,
            extensions=['tables', 'fenced_code', 'nl2br', 'codehilite', 'sane_lists', 'smarty', 'toc'],
            extension_configs={'codehilite': {'linenums': False, 'use_pygments': True, 'css_class': 'highlight'}, 'toc': {'permalink': False}}
        )
        css = self._get_css()
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Project Proposal</title>
            {css}
        </head>
        <body>
            <div class="header">{datetime.now().strftime("%Y-%m-%d")}</div>
            {html_content}
            <div class="footer"><span>Page </span><span class="pageNumber"></span><span> of </span><span class="totalPages"></span></div>
        </body>
        </html>
        """

    def _save_html_to_file(self, html_content: str, output_path: str) -> bool:
        """
        Save HTML content to a file as a fallback for PDF generation.

        Args:
            html_content: HTML content to save
            output_path: Path where to save the HTML file

        Returns:
            True if successful, False otherwise
        """
        html_path = output_path.replace('.pdf', '.html')
        try:
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"HTML saved as fallback: {html_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving HTML fallback: {str(e)}")
            return False

    def generate_pdf(self, content: str, output_path: str = None) -> Optional[str]:
        """
        Generate a PDF from content (markdown or text).

        Args:
            content: The markdown/text content to convert to PDF
            output_path: Optional path to save the PDF. If not provided, a temp path will be used.

        Returns:
            Path to the generated PDF file or None if failed
        """
        try:
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join("temp/proposals", f"proposal_{timestamp}.pdf")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            html_content = self._convert_to_styled_html(content)
            with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode='w', encoding='utf-8') as temp_html:
                temp_html.write(html_content)
                temp_html_path = temp_html.name

            try:
                import pdfkit
                config = pdfkit.configuration(wkhtmltopdf=self.wkhtmltopdf_path) if self.wkhtmltopdf_path else None
                pdfkit.from_file(temp_html_path, output_path, options=self.pdf_options, configuration=config)
                if os.path.exists(output_path):
                    logger.info(f"PDF generated successfully: {output_path}")
                    return output_path
                logger.error(f"PDF generation failed: {output_path}")
                self._save_html_to_file(html_content, output_path)
                return None
            except ImportError:
                logger.error("pdfkit not installed. Install with: pip install pdfkit")
                self._save_html_to_file(html_content, output_path)
                return None
            except Exception as e:
                logger.error(f"Error using pdfkit: {str(e)}")
                self._save_html_to_file(html_content, output_path)
                return None
            finally:
                if os.path.exists(temp_html_path):
                    os.unlink(temp_html_path)
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            if "No wkhtmltopdf executable found" in str(e):
                logger.error("Please install wkhtmltopdf: https://wkhtmltopdf.org/downloads.html")
            return None

    def render_html(self, proposal_id: str) -> str:
        """
        Render a proposal as HTML.

        Args:
            proposal_id: ID of the proposal to render

        Returns:
            HTML representation of the proposal
        """
        content = self._get_proposal_content(proposal_id)
        return self._convert_to_styled_html(content) if content else ""

    def generate_pdf_from_proposal(self, proposal_id: str) -> Optional[str]:
        """
        Generate PDF for a specific proposal.

        Args:
            proposal_id: ID of the proposal to generate PDF for

        Returns:
            Path to the generated PDF or None if failed
        """
        try:
            content = self._get_proposal_content(proposal_id)
            if not content:
                logger.error(f"Could not get content for proposal: {proposal_id}")
                return None
            proposal = self.proposal_repository.find_by_id(proposal_id)
            if not proposal:
                logger.error(f"Proposal not found: {proposal_id}")
                return None

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = (
                "".join(c if c.isalnum() else "_" for c in proposal.extracted_data.project_name)
                if hasattr(proposal, 'extracted_data') and hasattr(proposal.extracted_data, 'project_name')
                else f"proposal_{proposal_id}"
            )
            output_path = os.path.join("temp/proposals", f"{safe_title}_{timestamp}.pdf")
            pdf_path = self.generate_pdf(content, output_path)

            if pdf_path and hasattr(proposal, 'proposal_versions') and proposal.proposal_versions:
                latest_version_index = len(proposal.proposal_versions) - 1
                update_data = {f"proposal_versions.{latest_version_index}.pdf_path": pdf_path}
                self.proposal_repository.update(proposal_id, update_data)
            return pdf_path
        except Exception as e:
            logger.error(f"Error generating PDF from proposal: {str(e)}")
            return None

    def generate_docx(self, proposal_id: str, output_dir: str = "temp/proposals") -> Optional[str]:
        """
        Generate a DOCX version of a proposal.

        Args:
            proposal_id: ID of the proposal to convert
            output_dir: Directory to save the DOCX

        Returns:
            Path to the generated DOCX file or None if failed
        """
        logger.warning("DOCX generation not implemented")
        return None