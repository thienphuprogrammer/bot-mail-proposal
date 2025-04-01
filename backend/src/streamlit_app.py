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
        
        # Create mail service using factory
        mail_facade = MailServiceFactory.create_default_gmail_facade()
        
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

# App title and configuration
st.set_page_config(page_title="Automated Proposal Generator", layout="wide")
st.title("Automated Proposal Generation System")

if settings.USE_AZURE_AI:
    st.caption("Using Azure Model")
else:
    st.caption("Using LangChain Model")

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
                    max_results=10,
                    include_spam_trash=False,
                    query=""
                )
                
                # Check if we have processed any emails
                if result and result.get("processed", 0) > 0:
                    fetched_count = result.get("fetched", 0)
                    processed_count = result.get("processed", 0)
                    
                    # Get stats for different categories
                    categories = result.get("categories", {})
                    spam_count = categories.get("spam", 0)
                    proposal_requests = categories.get("proposal_requests", 0)
                    inquiries = categories.get("inquiries", 0)
                    
                    st.success(
                        f"Fetched {fetched_count} emails, processed {processed_count}: "
                        f"{proposal_requests} proposal requests, {inquiries} inquiries, {spam_count} spam"
                    )
                    
                    # Refresh the page to show new emails
                    st.rerun()
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
        emails = services["email_repository"].find_all(filter_dict=filter_dict, skip=0, limit=20)
        
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
                    "Project": proposal.extracted_data.project_name,
                    "Deadline": proposal.extracted_data.deadline.strftime("%Y-%m-%d") if proposal.extracted_data.deadline else "Not specified",
                    "Priority": proposal.extracted_data.priority,
                    "Proposal Status": "Processing" if len(proposal.proposal_versions) == 0 or proposal.proposal_versions is None else "Completed",
                    "Context": json.dumps(proposal.extracted_data[-1].context)
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
                        (f"{p['Project']} ({p['Status']})" for p in proposal_data if p["ID"] == x),
                        x
                    )
                )
                
                if selected_proposal_id:
                    proposal = services["proposal_repository"].find_by_id(selected_proposal_id)
                    if proposal:
                        # Get email
                        email = services["email_repository"].find_by_id(str(proposal.email_id))
                        
                        # Display proposal details
                        st.subheader(f"Proposal: {proposal.extracted_data.project_name}")
                        st.text(f"Status: {proposal.status.capitalize()}")
                        st.text(f"Created: {proposal.created_at.strftime('%Y-%m-%d %H:%M')}")
                        if email:
                            st.text(f"Email From: {email.sender}")
                        
                        # Extracted data
                        with st.expander("Extracted Requirements", expanded=True):
                            st.write(f"**Project Name:** {proposal.extracted_data.project_name}")
                            st.write(f"**Description:** {proposal.extracted_data.description}")
                            st.write(f"**Features:**")
                            if proposal.extracted_data.key_features:
                                for feature in proposal.extracted_data.key_features:
                                    st.write(f"- {feature}")
                            else:
                                st.write("- General project requirements")
                            deadline_str = proposal.extracted_data.deadline.strftime("%Y-%m-%d") if proposal.extracted_data.deadline else "Not specified"
                            st.write(f"**Deadline:** {deadline_str}")
                            st.write(f"**Budget:** {f'${proposal.extracted_data.budget}' if proposal.extracted_data.budget else 'Not specified'}")
                        
                        # Generated proposal
                        with st.expander("Generated Proposal", expanded=True):
                            st.markdown(proposal.proposal_html, unsafe_allow_html=True)
                        
                        # Approval and sending
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Approve button
                            if proposal.status == "pending":
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
                            # Generate PDF and send
                            if proposal.status == "approved":
                                if st.button("Send Proposal to Customer"):
                                    with st.spinner("Generating PDF and sending proposal..."):
                                        try:
                                            # First generate PDF
                                            pdf_path = services["proposal_service"].generate_pdf(selected_proposal_id)
                                            
                                            if pdf_path:
                                                # Then send email
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
                                            else:
                                                st.error("Failed to generate PDF")
                                        except Exception as e:
                                            st.error(f"Error sending proposal: {str(e)}")
                            
                            # Download PDF
                            if proposal.pdf_path and os.path.exists(proposal.pdf_path):
                                st.markdown(get_download_link(proposal.pdf_path), unsafe_allow_html=True)
                            else:
                                if st.button("Generate PDF"):
                                    with st.spinner("Generating PDF..."):
                                        try:
                                            pdf_path = services["proposal_service"].generate_pdf(selected_proposal_id)
                                            if pdf_path:
                                                st.success("PDF generated successfully!")
                                                st.markdown(get_download_link(pdf_path), unsafe_allow_html=True)
                                            else:
                                                st.error("Failed to generate PDF")
                                        except Exception as e:
                                            st.error(f"Error generating PDF: {str(e)}")
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
                # Get proposal
                proposal = services["proposal_repository"].find_by_id(str(sent.proposal_id))
                project_name = proposal.extracted_data.project_name if proposal else "Unknown"
                
                sent_dict = {
                    "ID": str(sent.id),
                    "Recipient": sent.recipients[0] if sent.recipients else "Unknown",
                    "Project": project_name,
                    "Subject": sent.subject,
                    "Sent": sent.sent_at.strftime("%Y-%m-%d %H:%M")
                }
                sent_data.append(sent_dict)
            
            df = pd.DataFrame(sent_data)
            st.dataframe(df)
            
            # View sent email details
            if sent_data:
                selected_sent_id = st.selectbox(
                    "Select sent email to view",
                    options=[s["ID"] for s in sent_data],
                    format_func=lambda x: next(
                        (f"{s['Project']} to {s['Recipient']}" for s in sent_data if s["ID"] == x),
                        x
                    )
                )
                
                if selected_sent_id:
                    sent = services["sent_email_repository"].find_by_id(selected_sent_id)
                    if sent:
                        # Get proposal
                        proposal = services["proposal_repository"].find_by_id(str(sent.proposal_id))
                        
                        st.subheader(f"Sent Proposal: {sent.subject}")
                        st.text(f"To: {sent.recipients[0] if sent.recipients else 'Unknown'}")
                        st.text(f"Sent: {sent.sent_at.strftime('%Y-%m-%d %H:%M')}")
                        
                        # Email body
                        with st.expander("Email Body", expanded=True):
                            st.markdown(sent.content, unsafe_allow_html=True)
                        
                        # Attachment
                        if sent.attachments and len(sent.attachments) > 0:
                            for attachment in sent.attachments:
                                if "path" in attachment and os.path.exists(attachment["path"]):
                                    attachment_name = attachment.get("name", os.path.basename(attachment["path"]))
                                    st.markdown(get_download_link(attachment["path"], f"Download {attachment_name}"), unsafe_allow_html=True)
                        
                        # Link to proposal
                        if proposal:
                            proposal_link = f"[View Full Proposal Details](#Proposals)"
                            st.markdown(proposal_link)
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
            
            for email in emails:
                # Get associated proposal
                proposals = services["proposal_repository"].find_all(
                    filter_dict={"email_id": ObjectId(email.id)}
                )
                proposal = proposals[0] if proposals else None
                
                # Get associated sent email
                sent_email = None
                if proposal and proposal.sent_email_id:
                    sent_emails = services["sent_email_repository"].find_all(
                        filter_dict={"_id": proposal.sent_email_id}
                    )
                    sent_email = sent_emails[0] if sent_emails else None
                
                # Calculate time metrics
                received_time = email.received_at
                processing_time = proposal.created_at if proposal else None
                sent_time = sent_email.sent_at if sent_email else None
                
                processing_duration = None
                if received_time and processing_time:
                    processing_duration = (processing_time - received_time).total_seconds() / 3600  # in hours
                
                total_duration = None
                if received_time and sent_time:
                    total_duration = (sent_time - received_time).total_seconds() / 3600  # in hours
                
                workflow_dict = {
                    "Email ID": str(email.id),
                    "Subject": email.subject,
                    "Sender": email.sender,
                    "Received": received_time.strftime("%Y-%m-%d %H:%M") if received_time else None,
                    "Processed": "Yes" if email.processed else "No",
                    "Proposal ID": str(proposal.id) if proposal else None,
                    "Proposal Status": proposal.status if proposal else None,
                    "Sent ID": str(sent_email.id) if sent_email else None,
                    "Sent Time": sent_time.strftime("%Y-%m-%d %H:%M") if sent_time else None,
                    "Processing Time (hrs)": round(processing_duration, 2) if processing_duration else None,
                    "Total Time (hrs)": round(total_duration, 2) if total_duration else None
                }
                
                workflow_data.append(workflow_dict)
            
            # Display workflow data
            st.subheader("Email to Proposal Workflow")
            df = pd.DataFrame(workflow_data)
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
                # Average processing time
                processing_times = [item["Processing Time (hrs)"] for item in workflow_data if item["Processing Time (hrs)"] is not None]
                avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
                st.metric("Avg. Processing Time", f"{avg_processing_time:.2f} hrs")
            
            with col3:
                # Average total time
                total_times = [item["Total Time (hrs)"] for item in workflow_data if item["Total Time (hrs)"] is not None]
                avg_total_time = sum(total_times) / len(total_times) if total_times else 0
                st.metric("Avg. Total Time", f"{avg_total_time:.2f} hrs")
            
            # Email to sent proposal conversion rate
            sent_count = sum(1 for item in workflow_data if item["Sent ID"] is not None)
            conversion_rate = (sent_count / len(workflow_data)) * 100 if workflow_data else 0
            st.metric("Email to Sent Proposal Conversion Rate", f"{conversion_rate:.1f}%")
        else:
            st.info("No emails found for workflow analysis")
            
    except Exception as e:
        st.error(f"Error loading workflow analysis: {str(e)}")

# Templates page
elif page == "Templates":
    st.header("Templates")
    
    try:
        # Template filters
        status_filter = st.selectbox(
            "Filter by Status",
            options=["All", "Active", "Inactive"],
            index=0
        )
        
        # Build filter
        filter_dict = {}
        if status_filter != "All":
            filter_dict["status"] = status_filter.lower()
        
        # Get templates from database
        templates = services["template_repository"].find_all(filter_dict=filter_dict, skip=0, limit=20)
        
        if templates:
            # Convert to DataFrame for display
            template_data = []
            for template in templates:
                template_dict = {
                    "ID": str(template.id),
                    "Name": template.name,
                    "Status": template.status.capitalize(),
                    "Created": template.created_at.strftime("%Y-%m-%d %H:%M")
                }
                template_data.append(template_dict)
            
            df = pd.DataFrame(template_data)
            st.dataframe(df)
            
            # View template details
            if template_data:
                selected_template_id = st.selectbox(
                    "Select template to view",
                    options=[t["ID"] for t in template_data],
                    format_func=lambda x: next(
                        (f"{t['Name']} ({t['Status']})" for t in template_data if t["ID"] == x),
                        x
                    )
                )
                
                if selected_template_id:
                    template = services["template_repository"].find_by_id(selected_template_id)
                    if template:
                        # Display template details
                        st.subheader(f"Template: {template.name}")
                        st.text(f"Status: {template.status.capitalize()}")
                        st.text(f"Created: {template.created_at.strftime('%Y-%m-%d %H:%M')}")
                        
                        # Template content
                        with st.expander("Template Content", expanded=True):
                            st.write(template.content)
                        
                        # Approval and status
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Approve button
                            if template.status == "pending":
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
                            # Deactivate button
                            if template.status == "approved":
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
        else:
            st.info(f"No templates found with status: {status_filter}")
            
    except Exception as e:
        st.error(f"Error loading templates: {str(e)}")

# Start the app
if __name__ == "__main__":
    # This part is automatically handled by Streamlit when you run streamlit run src/streamlit_app.py
    pass 
