"""
Azure Deepseek model prompts.
"""
from prompts.base_prompts import Prompt, PromptRegistry

# Register requirement extraction prompt
PromptRegistry.register(
    "azure_requirement_extraction",
    Prompt(
        name="azure_requirement_extraction",
        system_content="""
You are an AI assistant specialized in extracting structured project requirements from customer emails.
Your task is to analyze emails and identify key project details, converting them into a structured JSON format.
Be precise and extract only information that is explicitly mentioned or can be reasonably inferred.
""",
        user_template="""
Please analyze the following customer email and extract the key project requirements.

EMAIL:
{email_content}

Extract the following information in a clean JSON format:
1. Project name (a concise title for the project)
2. Description (a brief summary of what the project involves)
3. Features (a list of specific features or requirements)
4. Deadline (when the project needs to be completed, in YYYY-MM-DD format)
5. Budget (the amount mentioned, or null if not specified)

Format your response as valid JSON like:
{{
    "project_name": "...",
    "description": "...",
    "features": ["feature1", "feature2", ...],
    "deadline": "YYYY-MM-DD",
    "budget": number or null
}}

Only return the JSON, nothing else.
"""
    )
)

# Register proposal generation prompt
PromptRegistry.register(
    "azure_proposal_generation",
    Prompt(
        name="azure_proposal_generation",
        system_content="""
You are an expert proposal writer with years of experience creating professional business proposals.
Your proposals are clear, well-structured, convincing, and tailored to the specific requirements.
You create professional HTML documents with clean, modern design elements.
""",
        user_template="""
Based on the following project requirements, create a professional project proposal in HTML format.

PROJECT DETAILS:
- Project Name: {project_name}
- Description: {description}
- Features: {features}
- Deadline: {deadline}
- Budget: {budget}

Generate a complete proposal with the following sections:
1. Executive Summary (brief overview of the proposal)
2. Project Understanding (demonstrate understanding of requirements)
3. Proposed Solution (detailed approach to meeting requirements)
4. Features & Deliverables (detailed breakdown of features)
5. Timeline & Milestones (key phases with dates)
6. Pricing & Payment Terms (cost breakdown if budget is provided)
7. About Us (brief company overview)
8. Terms & Conditions (standard terms)

Use proper HTML formatting with appropriate tags (<div>, <h1>, <p>, <ul>, <table>, etc.) and include some basic CSS for styling.
Make the proposal visually appealing and professional.
"""
    )
)

# Register PDF generation prompt
PromptRegistry.register(
    "azure_pdf_generation",
    Prompt(
        name="azure_pdf_generation",
        system_content="""
You are an AI assistant specialized in generating PDF documents from HTML content.
You have expertise in document formatting, layout design, and content optimization for PDF output.
""",
        user_template="""
Convert the following HTML content into a professional PDF document format.
Ensure proper page breaks, margins, and formatting to create a professional-looking document.

HTML CONTENT:
{html_content}

The PDF should be saved to: {output_path}
"""
    )
) 