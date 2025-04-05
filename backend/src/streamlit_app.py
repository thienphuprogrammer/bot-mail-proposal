import streamlit as st
import os
import json
import base64
from datetime import datetime
from bson import ObjectId
import pandas as pd

# Initialize MongoDB connection
from database.mongodb import init_db
from repositories.email_repository import EmailRepository
from repositories.proposal_repository import ProposalRepository
from repositories.sent_email_repository import SentEmailRepository
from repositories.user_repository import UserRepository
from repositories.template_repository import TemplateRepository

# Import models
from models.email import Email, SentEmail
from models.proposal import Proposal, ProposalStatus, ApprovalDecision
from models.user import User, UserCreate

# Import services
from services.authentication import create_auth_service
from services.model import create_model_service
from services.mail.core.mail_factory import MailServiceFactory
from services.proposal.core.proposal_factory import ProposalServiceFactory
from services.template.template_service import TemplateService

from core.config import settings

# Custom JSON encoder for MongoDB ObjectId and datetime
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Initialize services
@st.cache_resource
def initialize_services():
    """Initialize all required services with proper dependency injection."""
    try:
        # Initialize database
        init_db()
        
        # Create repositories
        email_repository = EmailRepository()
        proposal_repository = ProposalRepository()
        sent_email_repository = SentEmailRepository()
        user_repository = UserRepository()
        template_repository = TemplateRepository()
        
        # Create authentication service
        auth_service = create_auth_service(user_repository=user_repository)
        
        # Create model service
        model_service = create_model_service(
            provider="langchain" if not settings.USE_AZURE_AI else "azure"
        )
        
        # Create mail service using factory - use Outlook instead of Gmail
        mail_facade = MailServiceFactory.create_default_outlook_facade()
        
        # Create proposal service using factory
        proposal_facade = ProposalServiceFactory.create_proposal_facade(
            proposal_repository=proposal_repository,
            email_repository=email_repository,
            sent_email_repository=sent_email_repository,
            mail_service=mail_facade
        )
        
        # Create template service
        template_service = TemplateService(
            template_repository=template_repository
        )
        
        return {
            "email_repository": email_repository,
            "proposal_repository": proposal_repository,
            "sent_email_repository": sent_email_repository,
            "user_repository": user_repository,
            "template_repository": template_repository,
            "mail_service": mail_facade,
            "model_service": model_service,
            "proposal_service": proposal_facade,
            "auth_service": auth_service,
            "template_service": template_service
        }
    except Exception as e:
        st.error(f"Failed to initialize services: {str(e)}")
        return None

# Function to get a download link for a file
def get_download_link(file_path: str, link_text: str = "Download PDF") -> str:
    """Generate a download link for a file."""
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="{os.path.basename(file_path)}">{link_text}</a>'
        return href
    except Exception as e:
        st.error(f"Failed to generate download link: {str(e)}")
        return ""

# Function to display PDF viewer
def display_pdf(file_path: str):
    """Display a PDF in the Streamlit app."""
    try:
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        
        # Embed PDF viewer using HTML
        pdf_display = f"""
        <iframe 
            src="data:application/pdf;base64,{base64_pdf}" 
            width="100%" 
            height="600" 
            type="application/pdf"
            frameborder="0">
        </iframe>
        """
        st.markdown(pdf_display, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Failed to display PDF: {str(e)}")

# App title and configuration
st.set_page_config(page_title="Automated Proposal Generator", layout="wide")
st.title("Automated Proposal Generation System")

if settings.USE_AZURE_AI:
    st.caption("Using Azure Model")
else:
    st.caption("Using LangChain Model")

# Email service info
st.caption("Using Outlook for email services")

# Initialize services
services = initialize_services()
if not services:
    st.error("Failed to initialize services. Please check your configuration.")
    st.stop()

# Sidebar for navigation
st.sidebar.title("Navigation")

# User authentication
if "user" not in st.session_state:
    st.session_state["user"] = {
        "id": None,
        "email": None,
        "role": None
    }

# Login/logout in sidebar
if st.session_state["user"] is None:
    # Only show login option
    page = "Login"
    st.sidebar.info("Please login to access the system")
else:
    # Show user info and logout button
    st.sidebar.success(f"Logged in as {st.session_state['user']['email']}")
    if st.sidebar.button("Logout"):
        st.session_state["user"] = None
        st.rerun()
    
    # Show navigation options
    page = st.sidebar.radio("Go to", ["Dashboard", "Emails", "Proposals", "Sent Proposals", "Workflow Analysis", "Templates"])

# Login page
if page == "Login":
    st.header("Login")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if email and password:
                try:
                    user = services["auth_service"].authenticate_user(email, password)
                    if user:
                        st.session_state["user"] = {
                            "id": str(user.id),
                            "email": user.email,
                            "role": user.role
                        }
                        st.success(f"Successfully logged in as {email}")
                        st.rerun()
                    else:
                        st.error("Invalid email or password")
                except Exception as e:
                    st.error(f"Login failed: {str(e)}")
            else:
                st.error("Please fill in all fields")
    
    with col2:
        st.subheader("Register")
        
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_name = st.text_input("Full Name")
        
        if st.button("Register"):
            if reg_email and reg_password and reg_name:
                try:
                    user_create = UserCreate(
                        email=reg_email,
                        password=reg_password,
                        full_name=reg_name,
                        role="staff"  # Default role
                    )
                    
                    user = services["auth_service"].register_user(user_create)
                    if user:
                        st.success(f"Successfully registered {reg_email}. You can now login.")
                    else:
                        st.error("Email is already registered")
                except Exception as e:
                    st.error(f"Registration failed: {str(e)}")
            else:
                st.error("Please fill in all fields")

# Check if user is logged in for other pages
elif st.session_state["user"] is None:
    st.warning("Please login first")
    st.stop()

# Dashboard page
elif page == "Dashboard":
    st.header("Dashboard")
    
    try:
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        
        # Email stats
        total_emails = len(services["email_repository"].find_all(filter_dict={}, skip=0, limit=1000))
        unprocessed_emails = len(services["email_repository"].find_all(
            filter_dict={"processing_status": "pending"}, 
            skip=0, 
            limit=1000
        ))
        
        # Proposal stats
        total_proposals = len(services["proposal_repository"].find_all(filter_dict={}, skip=0, limit=1000))
        proposals_by_status = {
            "draft": len(services["proposal_repository"].find_all(
                filter_dict={"current_status": "draft"}, 
                skip=0, 
                limit=1000
            )),
            "under_review": len(services["proposal_repository"].find_all(
                filter_dict={"current_status": "under_review"}, 
                skip=0, 
                limit=1000
            )),
            "approved": len(services["proposal_repository"].find_all(
                filter_dict={"current_status": "approved"}, 
                skip=0, 
                limit=1000
            )),
            "sent": len(services["proposal_repository"].find_all(
                filter_dict={"current_status": "sent"}, 
                skip=0, 
                limit=1000
            ))
        }
        
        with col1:
            st.metric("Total Emails", total_emails)
        
        with col2:
            st.metric("Pending Emails", unprocessed_emails)
        
        with col3:
            st.metric("Total Proposals", total_proposals)
        
        with col4:
            st.metric("Sent Proposals", proposals_by_status["sent"])
        
        # Recent activity
        st.subheader("Recent Activity")
        
        # Recent emails
        st.write("Recent Emails")
        recent_emails = services["email_repository"].find_all(skip=0, limit=5)
        if recent_emails:
            email_data = []
            for email in recent_emails:
                email_data.append({
                    "ID": str(email.id),
                    "Sender": email.sender,
                    "Subject": email.subject,
                    "Received": email.received_at.strftime("%Y-%m-%d %H:%M"),
                    "Processed": "Yes" if email.processed else "No"
                })
            
            st.dataframe(pd.DataFrame(email_data))
        else:
            st.info("No recent emails")
        
        # Recent proposals
        st.write("Recent Proposals")
        recent_proposals = services["proposal_repository"].find_all(skip=0, limit=5)
        if recent_proposals:
            proposal_data = []
            for proposal in recent_proposals:
                proposal_data.append({
                    "ID": str(proposal.id),
                    "Project": proposal.extracted_data.project_name,
                    "Deadline": proposal.extracted_data.deadline.strftime("%Y-%m-%d") if proposal.extracted_data.deadline else "Not specified",
                    "Priority": proposal.extracted_data.priority,
                    "Proposal Status": "Processing" if len(proposal.proposal_versions) == 0 or proposal.proposal_versions is None else "Completed"
                })
            
            st.dataframe(pd.DataFrame(proposal_data))
        else:
            st.info("No recent proposals")
            
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")

# Email page
elif page == "Emails":
    st.header("Email Processing")
    
    if st.button("Fetch New Emails", key="fetch_emails_button"):
        with st.spinner("Fetching and processing emails..."):
            try:
                # Use mail service to fetch emails
                result = services["mail_service"].fetch_and_process_emails(
                    query="isRead eq false",
                    max_results=20,
                    folder="inbox",
                    include_spam_trash=True,
                    only_recent=True
                )
                
                # Check if we have processed any emails
                if result:
                    # Handle both dictionary and list result formats
                    if isinstance(result, dict):
                        # Original dictionary format
                        fetched_count = result.get("fetched", 0) if result else 0
                        processed_count = result.get("processed", 0) if result else 0
                        
                        # Get stats for different categories
                        categories = result.get("categories", {}) if result else {}
                        spam_count = categories.get("spam", 0) if categories else 0
                        proposal_requests = categories.get("proposal_requests", 0) if categories else 0
                        inquiries = categories.get("inquiries", 0) if categories else 0
                        
                        success_message = (
                            f"Fetched {fetched_count} emails, processed {processed_count}: "
                            f"{proposal_requests} proposal requests, {inquiries} inquiries, {spam_count} spam"
                        )
                    elif isinstance(result, list):
                        # List format - just show the count
                        processed_count = len(result)
                        success_message = f"Processed {processed_count} emails"
                    else:
                        # Unknown result format
                        processed_count = 0
                        success_message = "Emails processed successfully, but count unknown"
                    
                    # Show success message if any emails were processed
                    if processed_count > 0:
                        st.success(success_message)
                        # Refresh the page to show new emails
                        st.rerun()
                    else:
                        st.info("No new emails found")
                else:
                    st.info("No new emails found")
            except Exception as e:
                st.error(f"Error fetching emails: {str(e)}")
    
    # Email filters
    st.subheader("Email List")
    filter_col1, filter_col2 = st.columns(2)
    
    with filter_col1:
        show_processed = st.checkbox("Show Processed Emails", value=True)
    
    with filter_col2:
        show_unprocessed = st.checkbox("Show Unprocessed Emails", value=True)
    
    # Build filter
    filter_dict = {}
    if show_processed and not show_unprocessed:
        filter_dict["processed"] = True
    elif not show_processed and show_unprocessed:
        filter_dict["processed"] = False
    
    try:
        # Get emails from database
        emails = services["email_repository"].find_all(filter_dict=filter_dict, skip=0, limit=1000)
        
        if emails:
            # Convert to DataFrame for display
            email_data = []
            for email in emails:
                email_dict = {
                    "ID": str(email.id),
                    "Sender": email.sender,
                    "Subject": email.subject,
                    "Received": email.received_at.strftime("%Y-%m-%d %H:%M"),
                    "Processed": "Yes" if email.processed else "No"
                }
                email_data.append(email_dict)
            
            df = pd.DataFrame(email_data)
            st.dataframe(df)
            
            # View email details
            if email_data:
                selected_email_id = st.selectbox(
                    "Select email to view",
                    options=[e["ID"] for e in email_data],
                    format_func=lambda x: next((e["Subject"] for e in email_data if e["ID"] == x), x)
                )
                
                if selected_email_id:
                    email = services["email_repository"].find_by_id(selected_email_id)
                    if email:
                        st.subheader(f"Email: {email.subject}")
                        st.text(f"From: {email.sender}")
                        st.text(f"Received: {email.received_at.strftime('%Y-%m-%d %H:%M')}")
                        
                        # Email body with scrollable area
                        st.text_area("Email Body", email.body, height=300)
                        
                        # Get proposal if it exists
                        proposals = services["proposal_repository"].find_all(
                            filter_dict={"email_id": ObjectId(selected_email_id)}
                        )
                        
                        # Process button
                        if not email.processed and not proposals:
                            if st.button("Generate Proposal from Email"):
                                with st.spinner("Analyzing email and generating proposal..."):
                                    try:
                                        proposal_id = services["proposal_service"].analyze_email(selected_email_id)
                                        if proposal_id:
                                            st.success("Proposal generated successfully!")
                                            st.rerun()
                                        else:
                                            st.error("Failed to generate proposal")
                                    except Exception as e:
                                        st.error(f"Error generating proposal: {str(e)}")
                        # Show existing proposal
                        if proposals:
                            st.success(f"This email has been processed")
                            proposal_link = f"[View Proposal #{str(proposals[0].id)}](#Proposals)"
                            st.markdown(proposal_link)
        else:
            st.info("No emails found with the selected filters")
            
    except Exception as e:
        st.error(f"Error loading emails: {str(e)}")

# Proposals page
elif page == "Proposals":
    st.header("Proposals")
    
    try:
        # Proposal filters
        status_filter = st.selectbox(
            "Filter by Status",
            options=["All", "Pending", "Approved", "Sent"],
            index=0
        )
        
        # Build filter
        filter_dict = {}
        if status_filter != "All":
            filter_dict["status"] = status_filter.lower()
        
        # Get proposals from database
        proposals = services["proposal_repository"].find_all(filter_dict=filter_dict, skip=0, limit=20)
        
        if proposals:
            # Convert to DataFrame for display
            proposal_data = []
            for proposal in proposals:
                # Get related email subject
                email = services["email_repository"].find_by_id(str(proposal.email_id))
                email_subject = email.subject if email else "Unknown"
                
                proposal_dict = {
                    "ID": str(proposal.id),
                    "Email Subject": email_subject,
                    "Project": proposal.extracted_data.project_name if hasattr(proposal, 'extracted_data') and hasattr(proposal.extracted_data, 'project_name') else "Unknown",
                    "Deadline": proposal.extracted_data.deadline.strftime("%Y-%m-%d") if hasattr(proposal, 'extracted_data') and hasattr(proposal.extracted_data, 'deadline') and proposal.extracted_data.deadline else "Not specified",
                    "Priority": proposal.extracted_data.priority if hasattr(proposal, 'extracted_data') and hasattr(proposal.extracted_data, 'priority') else "Medium",
                    "Proposal Status": "Processing" if not hasattr(proposal, 'proposal_versions') or proposal.proposal_versions is None or len(proposal.proposal_versions) == 0 else "Completed",
                    "Context": proposal.proposal_versions[-1].content if hasattr(proposal, 'proposal_versions') and proposal.proposal_versions and len(proposal.proposal_versions) > 0 and hasattr(proposal.proposal_versions[-1], 'content') else "",
                    "Mail context": proposal.extracted_data.description if hasattr(proposal, 'extracted_data') and hasattr(proposal.extracted_data, 'description') else ""
                }
                proposal_data.append(proposal_dict)
            
            df = pd.DataFrame(proposal_data)
            st.dataframe(df)
            
            # View proposal details
            if proposal_data:
                selected_proposal_id = st.selectbox(
                    "Select proposal to view",
                    options=[p["ID"] for p in proposal_data],
                    format_func=lambda x: next(
                        (f"{p['Project']}" for p in proposal_data if p["ID"] == x),
                        x
                    )
                )
                
                if selected_proposal_id:
                    proposal = services["proposal_repository"].find_by_id(selected_proposal_id)
                    if proposal:
                        # Get email
                        email = services["email_repository"].find_by_id(str(proposal.email_id))
                        
                        # Display proposal details
                        st.subheader(f"Proposal: {proposal.extracted_data.project_name if hasattr(proposal, 'extracted_data') and hasattr(proposal.extracted_data, 'project_name') else 'Unnamed Project'}")
                        st.text(f"Created: {proposal.proposal_versions[-1].created_at.strftime('%Y-%m-%d %H:%M') if hasattr(proposal, 'proposal_versions') and proposal.proposal_versions and len(proposal.proposal_versions) > 0 and hasattr(proposal.proposal_versions[-1], 'created_at') else 'Unknown'}")
                        if email:
                            st.text(f"Email From: {email.sender}")
                        
                        # Extracted data
                        with st.expander("Extracted Requirements", expanded=True):
                            st.write(f"**Project Name:** {proposal.extracted_data.project_name if hasattr(proposal, 'extracted_data') and hasattr(proposal.extracted_data, 'project_name') else 'Unknown'}")
                            st.write(f"**Description:** {proposal.extracted_data.description if hasattr(proposal, 'extracted_data') and hasattr(proposal.extracted_data, 'description') else 'Not available'}")
                            st.write(f"**Features:**")
                            if hasattr(proposal, 'extracted_data') and hasattr(proposal.extracted_data, 'key_features') and proposal.extracted_data.key_features:
                                for feature in proposal.extracted_data.key_features:
                                    st.write(f"- {feature}")
                            else:
                                st.write("- General project requirements")
                            deadline_str = proposal.extracted_data.deadline.strftime("%Y-%m-%d") if hasattr(proposal, 'extracted_data') and hasattr(proposal.extracted_data, 'deadline') and proposal.extracted_data.deadline else "Not specified"
                            st.write(f"**Deadline:** {deadline_str}")
                            st.write(f"**Budget:** {f'${proposal.extracted_data.budget}' if hasattr(proposal, 'extracted_data') and hasattr(proposal.extracted_data, 'budget') and proposal.extracted_data.budget else 'Not specified'}")
                        
                        # Generated proposal
                        with st.expander("Generated Proposal", expanded=True):
                            st.markdown(proposal.proposal_versions[-1].content if hasattr(proposal, 'proposal_versions') and proposal.proposal_versions and len(proposal.proposal_versions) > 0 and hasattr(proposal.proposal_versions[-1], 'content') else "No proposal content available", unsafe_allow_html=True)
                        
                        # Check for PDF and display
                        pdf_path = None
                        if hasattr(proposal, 'proposal_versions') and proposal.proposal_versions and hasattr(proposal.proposal_versions[-1], 'pdf_path'):
                            pdf_path = proposal.proposal_versions[-1].pdf_path
                            
                        if pdf_path and os.path.exists(pdf_path):
                            with st.expander("PDF Preview", expanded=True):
                                st.markdown(get_download_link(pdf_path), unsafe_allow_html=True)
                                display_pdf(pdf_path)
                        
                        # Approval and sending
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            # Approve button
                            if proposal.current_status == "under_review":
                                if st.button("Approve Proposal"):
                                    with st.spinner("Approving proposal..."):
                                        try:
                                            success = services["proposal_service"].approve_proposal(
                                                selected_proposal_id,
                                                st.session_state["user"]["id"],
                                                ApprovalDecision.APPROVED
                                            )
                                            if success:
                                                st.success("Proposal approved successfully!")
                                                st.rerun()
                                            else:
                                                st.error("Failed to approve proposal")
                                        except Exception as e:
                                            st.error(f"Error approving proposal: {str(e)}")
                        
                        with col2:
                            # Generate PDF
                            if not pdf_path or not os.path.exists(pdf_path):
                                if st.button("Generate PDF"):
                                    with st.spinner("Generating PDF..."):
                                        try:
                                            # Use the generate_pdf_from_proposal method if available, otherwise fallback to generate_pdf
                                            if hasattr(services["proposal_service"].proposal_renderer, 'generate_pdf_from_proposal'):
                                                pdf_path = services["proposal_service"].proposal_renderer.generate_pdf_from_proposal(selected_proposal_id)
                                            else:
                                                pdf_path = services["proposal_service"].generate_pdf(selected_proposal_id)
                                                
                                            if pdf_path and os.path.exists(pdf_path):
                                                st.success("PDF generated successfully!")
                                                st.markdown(get_download_link(pdf_path), unsafe_allow_html=True)
                                                with st.expander("PDF Preview", expanded=True):
                                                    display_pdf(pdf_path)
                                                st.rerun()  # Refresh to show updated UI
                                            else:
                                                st.error("Failed to generate PDF")
                                                # Check for wkhtmltopdf
                                                renderer = services["proposal_service"].proposal_renderer
                                                if hasattr(renderer, 'wkhtmltopdf_path'):
                                                    if not os.path.exists(renderer.wkhtmltopdf_path):
                                                        st.error(f"wkhtmltopdf not found at configured path: {renderer.wkhtmltopdf_path}")
                                                        st.info("Please install wkhtmltopdf: [Download Here](https://wkhtmltopdf.org/downloads.html)")
                                        except Exception as e:
                                            st.error(f"Error generating PDF: {str(e)}")
                        
                        with col3:
                            # Send proposal
                            if proposal.current_status == "approved" and pdf_path and os.path.exists(pdf_path):
                                if st.button("Send Proposal to Customer"):
                                    with st.spinner("Sending proposal..."):
                                        try:
                                            if email:
                                                result = services["proposal_service"].send_proposal(
                                                    selected_proposal_id,
                                                    recipient=email.sender
                                                )
                                                
                                                if result["success"]:
                                                    st.success("Proposal sent successfully!")
                                                    st.rerun()
                                                else:
                                                    st.error(f"Failed to send proposal: {result.get('error', 'Unknown error')}")
                                            else:
                                                st.error("Could not find original email")
                                        except Exception as e:
                                            st.error(f"Error sending proposal: {str(e)}")
        else:
            st.info(f"No proposals found with status: {status_filter}")
            
    except Exception as e:
        st.error(f"Error loading proposals: {str(e)}")

# Sent Proposals page
elif page == "Sent Proposals":
    st.header("Sent Proposals")
    
    try:
        # Get sent emails from database
        sent_emails = services["sent_email_repository"].find_all(skip=0, limit=20)
        
        if sent_emails:
            # Convert to DataFrame for display
            sent_data = []
            for sent in sent_emails:
                try:
                    # Get proposal
                    proposal = None
                    project_name = "Unknown"
                    if hasattr(sent, 'proposal_id') and sent.proposal_id:
                        try:
                            proposal = services["proposal_repository"].find_by_id(str(sent.proposal_id))
                            if proposal and hasattr(proposal, 'extracted_data') and hasattr(proposal.extracted_data, 'project_name'):
                                project_name = proposal.extracted_data.project_name
                        except Exception:
                            # Keep default project_name if error occurs
                            pass
                    
                    recipients = []
                    if hasattr(sent, 'recipients') and sent.recipients:
                        recipients = sent.recipients
                    
                    sent_at = None
                    if hasattr(sent, 'sent_at') and sent.sent_at:
                        sent_at = sent.sent_at
                    
                    sent_dict = {
                        "ID": str(sent.id) if hasattr(sent, 'id') else "Unknown",
                        "Recipient": recipients[0] if recipients else "Unknown",
                        "Project": project_name,
                        "Subject": sent.subject if hasattr(sent, 'subject') else "Unknown",
                        "Sent": sent_at.strftime("%Y-%m-%d %H:%M") if sent_at else "Unknown"
                    }
                    sent_data.append(sent_dict)
                except Exception as e:
                    st.warning(f"Error processing sent email: {str(e)}")
                    continue
            
            if sent_data:
                df = pd.DataFrame(sent_data)
                st.dataframe(df)
                
                # View sent email details
                selected_sent_id = st.selectbox(
                    "Select sent email to view",
                    options=[s["ID"] for s in sent_data],
                    format_func=lambda x: next(
                        (f"{s['Project']} to {s['Recipient']}" for s in sent_data if s["ID"] == x),
                        x
                    )
                )
                
                if selected_sent_id:
                    try:
                        sent = services["sent_email_repository"].find_by_id(selected_sent_id)
                        if sent:
                            # Get proposal
                            proposal = None
                            if hasattr(sent, 'proposal_id') and sent.proposal_id:
                                try:
                                    proposal = services["proposal_repository"].find_by_id(str(sent.proposal_id))
                                except Exception:
                                    pass
                            
                            # Safely get subject
                            subject = "Sent Proposal"
                            if hasattr(sent, 'subject') and sent.subject:
                                subject = sent.subject
                            
                            # Safely get recipients
                            recipient = "Unknown"
                            if hasattr(sent, 'recipients') and sent.recipients and len(sent.recipients) > 0:
                                recipient = sent.recipients[0]
                            
                            # Safely get sent time
                            sent_time_str = "Unknown time"
                            if hasattr(sent, 'sent_at') and sent.sent_at:
                                sent_time_str = sent.sent_at.strftime("%Y-%m-%d %H:%M")
                            
                            st.subheader(f"Sent Proposal: {subject}")
                            st.text(f"To: {recipient}")
                            st.text(f"Sent: {sent_time_str}")
                            
                            # Email body
                            with st.expander("Email Body", expanded=True):
                                if hasattr(sent, 'content') and sent.content:
                                    st.markdown(sent.content, unsafe_allow_html=True)
                                else:
                                    st.info("No email content available")
                            
                            # Attachment handling and PDF preview
                            has_attachments = False
                            if hasattr(sent, 'attachments') and sent.attachments and len(sent.attachments) > 0:
                                for attachment in sent.attachments:
                                    if isinstance(attachment, dict) and "path" in attachment and os.path.exists(attachment["path"]):
                                        has_attachments = True
                                        attachment_name = os.path.basename(attachment["path"])
                                        if "name" in attachment and attachment["name"]:
                                            attachment_name = attachment["name"]
                                        st.markdown(get_download_link(attachment["path"], f"Download {attachment_name}"), unsafe_allow_html=True)
                                        
                                        # If it's a PDF, show preview
                                        if attachment["path"].lower().endswith('.pdf'):
                                            with st.expander("PDF Preview", expanded=True):
                                                display_pdf(attachment["path"])
                            
                            if not has_attachments:
                                st.warning("Attachments are not available or have been moved")
                            
                            # Link to proposal
                            if proposal:
                                proposal_link = f"[View Full Proposal Details](#Proposals)"
                                st.markdown(proposal_link)
                    except Exception as e:
                        st.error(f"Error displaying sent email: {str(e)}")
            else:
                st.info("No valid sent proposal data available")
        else:
            st.info("No sent proposals found")
            
    except Exception as e:
        st.error(f"Error loading sent proposals: {str(e)}")

# Workflow Analysis page
elif page == "Workflow Analysis":
    st.header("Workflow Analysis")
    
    try:
        # Get all emails with their proposals
        emails = services["email_repository"].find_all(skip=0, limit=50)
        
        if emails:
            workflow_data = []
            error_count = 0
            
            for email in emails:
                try:
                    # Get associated proposal
                    proposals = None
                    try:
                        proposals = services["proposal_repository"].find_all(
                            filter_dict={"email_id": ObjectId(str(email.id))}
                        )
                    except Exception as e:
                        # Continue without logging debug info
                        pass

                    proposal = proposals[0] if proposals and len(proposals) > 0 else None
                    
                    # Get associated sent email
                    sent_email = None
                    if proposal and hasattr(proposal, 'sent_email_id') and proposal.sent_email_id:
                        try:
                            sent_emails = services["sent_email_repository"].find_all(
                                filter_dict={"_id": ObjectId(str(proposal.sent_email_id))}
                            )
                            sent_email = sent_emails[0] if sent_emails and len(sent_emails) > 0 else None
                        except Exception:
                            # Continue without error
                            pass
                    
                    # Calculate time metrics with safe defaults
                    received_time = None
                    if hasattr(email, 'received_at') and email.received_at:
                        received_time = email.received_at
                    
                    processing_time = None  
                    if proposal and hasattr(proposal, 'created_at') and proposal.created_at:
                        processing_time = proposal.created_at
                    
                    sent_time = None
                    if sent_email and hasattr(sent_email, 'sent_at') and sent_email.sent_at:
                        sent_time = sent_email.sent_at
                    
                    processing_duration = None
                    if received_time and processing_time:
                        try:
                            processing_duration = (processing_time - received_time).total_seconds() / 3600  # in hours
                        except Exception:
                            processing_duration = None
                    
                    total_duration = None
                    if received_time and sent_time:
                        try:
                            total_duration = (sent_time - received_time).total_seconds() / 3600  # in hours
                        except Exception:
                            total_duration = None
                    
                    # Ensure all dictionary values have fallbacks
                    email_id = str(email.id) if hasattr(email, 'id') else "Unknown"
                    subject = email.subject if hasattr(email, 'subject') else "Unknown"
                    sender = email.sender if hasattr(email, 'sender') else "Unknown"
                    received_str = received_time.strftime("%Y-%m-%d %H:%M") if received_time else "Unknown"
                    processed = "Yes" if hasattr(email, 'processed') and email.processed else "No"
                    proposal_id = str(proposal.id) if proposal and hasattr(proposal, 'id') else None
                    proposal_status = proposal.current_status if proposal and hasattr(proposal, 'current_status') else None
                    sent_id = str(sent_email.id) if sent_email and hasattr(sent_email, 'id') else None
                    sent_str = sent_time.strftime("%Y-%m-%d %H:%M") if sent_time else None
                    
                    # Build workflow entry with safe attribute access and stringified values
                    workflow_dict = {
                        "Email ID": email_id,
                        "Subject": subject,
                        "Sender": sender,
                        "Received": received_str,
                        "Processed": processed,
                        "Proposal ID": proposal_id,
                        "Proposal Status": proposal_status,
                        "Sent ID": sent_id,
                        "Sent Time": sent_str,
                        "Processing Time (hrs)": round(processing_duration, 2) if processing_duration is not None else None,
                        "Total Time (hrs)": round(total_duration, 2) if total_duration is not None else None
                    }
                    
                    workflow_data.append(workflow_dict)
                except Exception as item_e:
                    # Skip this item and count errors
                    error_count += 1
                    continue
            
            # Display workflow data
            if workflow_data:
                st.subheader("Email to Proposal Workflow")
                
                # Show error count if any
                if error_count > 0:
                    st.warning(f"{error_count} items were skipped due to errors")
                
                # Convert all None values to empty strings for display safety
                safe_data = []
                for item in workflow_data:
                    safe_item = {k: (v if v is not None else "") for k, v in item.items()}
                    safe_data.append(safe_item)
                    
                df = pd.DataFrame(safe_data)
                st.dataframe(df)
                
                # Statistics
                st.subheader("Workflow Statistics")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Processing rate
                    processed_count = sum(1 for item in workflow_data if item["Processed"] == "Yes")
                    processing_rate = (processed_count / len(workflow_data)) * 100 if workflow_data else 0
                    st.metric("Email Processing Rate", f"{processing_rate:.1f}%")
                
                with col2:
                    # Average processing time - handle empty lists
                    processing_times = [item["Processing Time (hrs)"] for item in workflow_data if item["Processing Time (hrs)"] is not None]
                    avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
                    st.metric("Avg. Processing Time", f"{avg_processing_time:.2f} hrs")
                
                with col3:
                    # Average total time - handle empty lists
                    total_times = [item["Total Time (hrs)"] for item in workflow_data if item["Total Time (hrs)"] is not None]
                    avg_total_time = sum(total_times) / len(total_times) if total_times else 0
                    st.metric("Avg. Total Time", f"{avg_total_time:.2f} hrs")
                
                # Email to sent proposal conversion rate
                sent_count = sum(1 for item in workflow_data if item["Sent ID"] is not None and item["Sent ID"] != "")
                conversion_rate = (sent_count / len(workflow_data)) * 100 if workflow_data else 0
                st.metric("Email to Sent Proposal Conversion Rate", f"{conversion_rate:.1f}%")
            else:
                st.info("No workflow data available for analysis")
        else:
            st.info("No emails found for workflow analysis")
            
    except Exception as e:
        st.error(f"Error loading workflow analysis: {str(e)}")

# Templates page
elif page == "Templates":
    st.header("Templates")
    
    try:
        # Template filters with improved status options
        status_options = ["All", "Active", "Inactive", "Pending"]
        status_filter = st.selectbox(
            "Filter by Status",
            options=status_options,
            index=0
        )
        
        # Build filter with proper status mapping
        filter_dict = {}
        if status_filter != "All":
            status_map = {
                "Active": "approved", 
                "Inactive": "inactive",
                "Pending": "pending"
            }
            filter_dict["status"] = status_map.get(status_filter, status_filter.lower())
        
        # Get templates from database
        templates = services["template_repository"].find_all(filter_dict=filter_dict, skip=0, limit=20)
        
        if templates and len(templates) > 0:
            # Convert to DataFrame for display
            template_data = []
            error_count = 0
            
            for template in templates:
                try:
                    # Safe extraction of template properties with explicit checks
                    template_id = "Unknown"
                    if hasattr(template, 'id') and template.id is not None:
                        template_id = str(template.id)
                    
                    template_name = "Unnamed"
                    if hasattr(template, 'name') and template.name is not None:
                        template_name = str(template.name)
                        
                    template_status = "Unknown"
                    if hasattr(template, 'status') and template.status is not None:
                        template_status = str(template.status).capitalize()
                        
                    created_at_str = "Unknown"
                    if hasattr(template, 'created_at') and template.created_at is not None:
                        try:
                            created_at_str = template.created_at.strftime("%Y-%m-%d %H:%M")
                        except Exception:
                            pass
                    
                    template_dict = {
                        "ID": template_id,
                        "Name": template_name,
                        "Status": template_status,
                        "Created": created_at_str
                    }
                    template_data.append(template_dict)
                except Exception as e:
                    error_count += 1
                    continue
            
            if template_data and len(template_data) > 0:
                if error_count > 0:
                    st.warning(f"{error_count} templates were skipped due to data errors")
                    
                # Create DataFrame with all string values to prevent JavaScript errors
                df = pd.DataFrame(template_data)
                st.dataframe(df)
                
                # Create a simplified dictionary for the dropdown to avoid issues
                template_options = []
                template_display_names = {}
                
                for t in template_data:
                    tid = t["ID"]
                    if tid != "Unknown" and tid.strip() != "":
                        template_options.append(tid)
                        template_display_names[tid] = f"{t['Name']} ({t['Status']})"
                
                # View template details
                if template_options and len(template_options) > 0:
                    try:
                        selected_template_id = st.selectbox(
                            "Select template to view",
                            options=template_options,
                            format_func=lambda x: template_display_names.get(x, x) if template_display_names and x in template_display_names else x
                        )
                        
                        if selected_template_id and selected_template_id != "Unknown":
                            try:
                                template = services["template_repository"].find_by_id(selected_template_id)
                                if template:
                                    # Display template details with safe access
                                    name = "Unnamed Template"
                                    if hasattr(template, 'name') and template.name is not None:
                                        name = str(template.name)
                                        
                                    status = "Unknown"
                                    if hasattr(template, 'status') and template.status is not None:
                                        status = str(template.status).capitalize()
                                        
                                    created_at = "Unknown date"
                                    if hasattr(template, 'created_at') and template.created_at is not None:
                                        try:
                                            created_at = template.created_at.strftime("%Y-%m-%d %H:%M")
                                        except Exception:
                                            pass
                                    
                                    st.subheader(f"Template: {name}")
                                    st.text(f"Status: {status}")
                                    st.text(f"Created: {created_at}")
                                    
                                    # Safely check for content existence
                                    content = ""
                                    has_content = False
                                    if hasattr(template, 'content') and template.content is not None:
                                        content = str(template.content)
                                        has_content = content.strip() != ""
                                    
                                    # Template content
                                    with st.expander("Template Content", expanded=True):
                                        if has_content:
                                            # Try to determine if it's HTML or markdown
                                            if content.strip().startswith('<'):
                                                st.markdown(content, unsafe_allow_html=True)
                                            else:
                                                st.write(content)
                                        else:
                                            st.info("No content available for this template")
                                    
                                    # Testing template preview
                                    with st.expander("Template Preview", expanded=False):
                                        st.info("This is how the template would look when applied to a proposal")
                                        if has_content:
                                            sample_data = {
                                                "project_name": "Sample Project",
                                                "client_name": "Sample Client",
                                                "deadline": "2023-12-31",
                                                "budget": "$5,000",
                                                "features": ["Feature 1", "Feature 2", "Feature 3"]
                                            }
                                            
                                            # Try to render with sample data (basic implementation)
                                            try:
                                                preview = content
                                                for key, value in sample_data.items():
                                                    if key and value is not None:
                                                        placeholder = "{{" + key + "}}"
                                                        replacement = ""
                                                        if isinstance(value, list):
                                                            replacement = "<ul>" + "".join([f"<li>{item}</li>" for item in value]) + "</ul>"
                                                        else:
                                                            replacement = str(value)
                                                        preview = preview.replace(placeholder, replacement)
                                                
                                                st.markdown(preview, unsafe_allow_html=True)
                                            except Exception as preview_e:
                                                st.error(f"Error rendering preview: {str(preview_e)}")
                                    
                                    # Approval and status
                                    col1, col2, col3 = st.columns(3)
                                    
                                    current_status = ""
                                    if hasattr(template, 'status') and template.status is not None:
                                        current_status = str(template.status).lower()
                                    
                                    with col1:
                                        # Approve button - only show if status is actually pending
                                        if current_status == "pending":
                                            if st.button("Approve Template"):
                                                with st.spinner("Approving template..."):
                                                    try:
                                                        success = services["template_repository"].approve_template(selected_template_id)
                                                        if success:
                                                            st.success("Template approved successfully!")
                                                            st.rerun()
                                                        else:
                                                            st.error("Failed to approve template")
                                                    except Exception as e:
                                                        st.error(f"Error approving template: {str(e)}")
                                    
                                    with col2:
                                        # Deactivate button - only show if status is approved
                                        if current_status == "approved":
                                            if st.button("Deactivate Template"):
                                                with st.spinner("Deactivating template..."):
                                                    try:
                                                        success = services["template_repository"].deactivate_template(selected_template_id)
                                                        if success:
                                                            st.success("Template deactivated successfully!")
                                                            st.rerun()
                                                        else:
                                                            st.error("Failed to deactivate template")
                                                    except Exception as e:
                                                        st.error(f"Error deactivating template: {str(e)}")
                                    
                                    with col3:
                                        # Test apply button - only show for active templates
                                        if current_status in ["approved", "active"]:
                                            if st.button("Test Apply to Proposal"):
                                                st.info("This functionality is not yet implemented")
                                else:
                                    st.error("Template not found. It may have been deleted.")
                            except Exception as template_e:
                                st.error(f"Error loading template details: {str(template_e)}")
                    except Exception as select_e:
                        st.error(f"Error with template selection: {str(select_e)}")
                else:
                    st.warning("No valid templates found to select")
            else:
                st.warning("Templates were found but could not be processed properly")
        else:
            st.info(f"No templates found with status: {status_filter}")
            
    except Exception as e:
        st.error(f"Error loading templates: {str(e)}")

# Start the app
if __name__ == "__main__":
    # This part is automatically handled by Streamlit when you run streamlit run src/streamlit_app.py
    pass 
