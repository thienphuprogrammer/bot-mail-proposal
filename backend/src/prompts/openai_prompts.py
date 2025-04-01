"""
OpenAI model prompts.
"""
from prompts.base_prompts import Prompt, PromptRegistry

# Register requirement extraction prompt for OpenAI
PromptRegistry.register(
    "openai_requirement_extraction",
    Prompt(
        system_content="""
You are an AI assistant specialized in extracting structured project requirements from customer emails.
You have excellent analytical skills and can identify key project details even when they are not explicitly stated.
""",
        user_template="""
I need you to analyze this customer email and extract the requirements into a structured format.

EMAIL:
{email_content}

Please extract the following information and return it as a valid JSON object:
- project_name: A concise title for the project
- description: A brief summary of the project scope
- features: An array of specific features or requirements requested
- deadline: When the project needs to be completed (in YYYY-MM-DD format)
- budget: The budget mentioned in the email (as a number), or null if not specified

Format it as:
{{
    "project_name": "...",
    "description": "...",
    "features": ["feature1", "feature2", ...],
    "deadline": "YYYY-MM-DD",
    "budget": number or null
}}

Only return the JSON, no additional text.
"""
    )
)

# Register proposal generation prompt for OpenAI
PromptRegistry.register(
    "openai_proposal_generation",
    Prompt(
        system_content="""
You are an experienced business proposal writer working for a professional services company.
Your proposals are known for being clear, well-organized, and persuasive.
You strike the perfect balance between technical details and business value.
""",
        user_template="""
Create a professional proposal based on the following project requirements:

PROJECT INFORMATION:
- Project Name: {project_name}
- Description: {description}
- Features Requested: {features}
- Deadline: {deadline}
- Budget: {budget}

The proposal should be formatted in HTML and include:
1. A professional header with project title
2. Executive summary
3. Detailed understanding of requirements
4. Proposed solution
5. Feature implementation details
6. Project timeline
7. Cost breakdown
8. Terms and conditions
9. Next steps

Use appropriate HTML tags (<h1>, <p>, <ul>, <table>, etc.) and include basic CSS styling to make it visually appealing.
"""
    )
)

# Register PDF generation prompt for OpenAI
PromptRegistry.register(
    "openai_pdf_generation",
    Prompt(
        system_content="""
You are a document formatting specialist who helps convert HTML content into professional PDFs.
You excel at ensuring proper layout, formatting, and design principles in document generation.
""",
        user_template="""
Convert the following HTML content into a professional PDF document.
Pay special attention to layout, typography, and overall presentation.

HTML CONTENT:
{html_content}

Save the final PDF to this location: {output_path}

Ensure the document follows standard business formatting with appropriate margins, headers, and page breaks.
"""
    )
) 