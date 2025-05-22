from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
# from src.api.v1.auth.routes import get_current_user
from src.core.config import settings
import logging
from bson import ObjectId

from src.repositories.template_repository import TemplateRepository
from src.services.template.template_service import TemplateService

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize repositories and services
template_repository = TemplateRepository()
template_service = TemplateService(template_repository=template_repository)

# Template models
class TemplateBase(BaseModel):
    name: str
    content: str
    description: Optional[str] = None
    
class TemplateResponse(BaseModel):
    id: str
    name: str
    content: str
    description: Optional[str] = None
    status: str
    created_at: datetime
    
    class Config:
        orm_mode = True

@router.get("/", response_model=List[Dict[str, Any]])
async def get_templates(
    skip: int = 0, 
    limit: int = 20, 
    status: Optional[str] = None,
    # current_user = Depends(get_current_user)
):
    """
    Get all templates, with optional filtering by status.
    """
    try:
        filter_dict = {}
        if status and status.lower() != "all":
            status_map = {
                "active": "approved", 
                "inactive": "inactive",
                "pending": "pending"
            }
            filter_dict["status"] = status_map.get(status.lower(), status.lower())
            
        templates = template_repository.find_all(
            filter_dict=filter_dict,
            skip=skip,
            limit=limit
        )
        
        # Convert to response format
        result = []
        for template in templates:
            template_dict = {
                "id": str(template.id),
                "name": template.name if hasattr(template, 'name') else "Unnamed",
                "description": template.description if hasattr(template, 'description') else "",
                "status": template.status if hasattr(template, 'status') else "unknown",
                "created_at": template.created_at if hasattr(template, 'created_at') else datetime.utcnow(),
                "content_preview": template.content[:100] + "..." if hasattr(template, 'content') and template.content and len(template.content) > 100 else template.content if hasattr(template, 'content') else ""
            }
            result.append(template_dict)
        
        return result
    except Exception as e:
        logger.error(f"Error retrieving templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving templates: {str(e)}"
        )

@router.get("/{template_id}", response_model=Dict[str, Any])
async def get_template(
    template_id: str,
    # current_user = Depends(get_current_user)
):
    """
    Get a specific template by ID.
    """
    try:
        template = template_repository.find_by_id(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with ID {template_id} not found"
            )
            
        # Convert to response dictionary with safe attribute access
        template_dict = {
            "id": str(template.id),
            "name": template.name if hasattr(template, 'name') else "Unnamed",
            "description": template.description if hasattr(template, 'description') else "",
            "status": template.status if hasattr(template, 'status') else "unknown",
            "created_at": template.created_at if hasattr(template, 'created_at') else datetime.utcnow(),
            "content": template.content if hasattr(template, 'content') else ""
        }
        
        return template_dict
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving template {template_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving template: {str(e)}"
        )

@router.post("/", response_model=Dict[str, Any])
async def create_template(
    template: TemplateBase,
    # current_user = Depends(get_current_user)
):
    """
    Create a new template.
    """
    try:
        # Check if template with same name exists
        existing_templates = template_repository.find_all(
            filter_dict={"name": template.name},
            skip=0,
            limit=1
        )
        
        if existing_templates and len(existing_templates) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template with name '{template.name}' already exists"
            )
            
        # Create new template
        template_data = {
            "name": template.name,
            "content": template.content,
            "description": template.description,
            "status": "pending",  # New templates start as pending
            "created_at": datetime.utcnow()
        }
        
        template_id = template_repository.create(template_data)
        
        if template_id:
            return {
                "status": "success",
                "message": "Template created successfully",
                "template_id": str(template_id)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create template"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating template: {str(e)}"
        )

@router.put("/{template_id}", response_model=Dict[str, Any])
async def update_template(
    template_id: str,
    template_update: TemplateBase,
    # current_user = Depends(get_current_user)
):
    """
    Update an existing template.
    """
    try:
        # Check if template exists
        template = template_repository.find_by_id(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with ID {template_id} not found"
            )
            
        # Update template
        template_data = {
            "name": template_update.name,
            "content": template_update.content,
            "description": template_update.description,
            "status": "pending",  # Updates reset status to pending for review
        }
        
        success = template_repository.update(template_id, template_data)
        
        if success:
            return {
                "status": "success",
                "message": "Template updated successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update template"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template {template_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating template: {str(e)}"
        )

@router.post("/{template_id}/approve", response_model=Dict[str, Any])
async def approve_template(
    template_id: str,
    # current_user = Depends(get_current_user)
):
    """
    Approve a template.
    """
    try:
        # Check if template exists
        template = template_repository.find_by_id(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with ID {template_id} not found"
            )
            
        if template.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template is not pending approval"
            )
            
        # Approve template
        success = template_repository.approve_template(template_id)
        
        if success:
            return {
                "status": "success",
                "message": "Template approved successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to approve template"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving template {template_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error approving template: {str(e)}"
        )

@router.post("/{template_id}/deactivate", response_model=Dict[str, Any])
async def deactivate_template(
    template_id: str,
    # current_user = Depends(get_current_user)
):
    """
    Deactivate a template.
    """
    try:
        # Check if template exists
        template = template_repository.find_by_id(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with ID {template_id} not found"
            )
            
        if template.status != "approved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template is not currently active/approved"
            )
            
        # Deactivate template
        success = template_repository.deactivate_template(template_id)
        
        if success:
            return {
                "status": "success",
                "message": "Template deactivated successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deactivate template"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating template {template_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deactivating template: {str(e)}"
        )

@router.delete("/{template_id}", response_model=Dict[str, Any])
async def delete_template(
    template_id: str,
    # current_user = Depends(get_current_user)
):
    """
    Delete a template.
    """
    try:
        # Check if template exists
        template = template_repository.find_by_id(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with ID {template_id} not found"
            )
            
        # Delete template
        success = template_repository.delete(template_id)
        
        if success:
            return {
                "status": "success",
                "message": "Template deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete template"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template {template_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting template: {str(e)}"
        ) 