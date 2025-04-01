from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from bson import ObjectId
from pymongo.errors import PyMongoError

from repositories.base_repository import MongoRepository
from models.proposal import Proposal, ProposalCreate, ProposalUpdate, ProposalStatus
from database.mongodb import MongoDB

class ProposalRepository(MongoRepository[Proposal, ProposalCreate]):
    """Repository for Proposal operations."""
    
    def __init__(self):
        """Initialize repository with proposal collection."""
        super().__init__(MongoDB.get_collection("proposals"))
    
    def _map_to_model(self, db_item: Dict[str, Any]) -> Optional[Proposal]:
        """Map database item to Proposal model."""
        if not db_item:
            return None
        try:
            return Proposal(**db_item)
        except Exception as e:
            raise ValueError(f"Error mapping proposal data: {str(e)}")
    
    def _convert_to_dict(self, item: ProposalCreate) -> Dict[str, Any]:
        """Convert ProposalCreate to dictionary for database operations."""
        try:
            return item.model_dump(by_alias=True, exclude_unset=True)
        except Exception as e:
            raise ValueError(f"Error converting proposal to dict: {str(e)}")
    
    def _convert_update_to_dict(self, item: ProposalUpdate) -> Dict[str, Any]:
        """Convert ProposalUpdate to dictionary for database operations."""
        try:
            return item.model_dump(by_alias=True, exclude_unset=True)
        except Exception as e:
            raise ValueError(f"Error converting proposal update to dict: {str(e)}")
    
    def find_by_email_id(self, email_id: Union[str, ObjectId]) -> Optional[Proposal]:
        """
        Find proposal by email ID.
        
        Args:
            email_id: Email ID to search for
            
        Returns:
            Optional[Proposal]: Found proposal or None
            
        Raises:
             If database operation fails
        """
        try:
            email_id = ObjectId(email_id) if isinstance(email_id, str) else email_id
            result = self.collection.find_one({"email_id": email_id})
            return self._map_to_model(result)
        except PyMongoError as e:
            raise f"Error finding proposal by email ID: {str(e)}"
    
    def find_by_status(self, status: Union[str, ProposalStatus], limit: int = 10) -> List[Proposal]:
        """
        Find proposals by status.
        
        Args:
            status: Status to search for
            limit: Maximum number of results to return
            
        Returns:
            List[Proposal]: List of matching proposals
            
        Raises:
             If database operation fails
        """
        try:
            status_str = status.value if isinstance(status, ProposalStatus) else status
            cursor = self.collection.find({"current_status": status_str}).limit(limit)
            return [self._map_to_model(doc) for doc in cursor]
        except PyMongoError as e:
            raise ValueError(f"Error finding proposals by status: {str(e)}")
    
    def add_version(self, proposal_id: Union[str, ObjectId], version_data: Dict[str, Any]) -> Optional[Proposal]:
        """
        Add a new version to a proposal.
        
        Args:
            proposal_id: ID of the proposal
            version_data: Version data to add
            
        Returns:
            Optional[Proposal]: Updated proposal or None
            
        Raises:
             If database operation fails
        """
        try:
            proposal_id = ObjectId(proposal_id) if isinstance(proposal_id, str) else proposal_id
            
            # First get the current proposal to validate
            proposal = self.find_by_id(proposal_id)
            if not proposal:
                return None
            
            # Calculate the next version number
            next_version = len(proposal.proposal_versions) + 1
            
            # Ensure version data has required fields
            version_data.update({
                'version': next_version,
                'created_at': datetime.utcnow()
            })
            
            # Add the new version
            result = self.collection.update_one(
                {"_id": proposal_id},
                {
                    "$push": {"proposal_versions": version_data},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            if result.modified_count == 0:
                return None
                
            # Fetch and validate the updated proposal
            updated_proposal = self.find_by_id(proposal_id)
            if not updated_proposal:
                return None
                
            return updated_proposal
        except PyMongoError as e:
            raise ValueError(f"Error adding proposal version: {str(e)}")
        except Exception as e:
            raise ValueError(f"Unexpected error adding proposal version: {str(e)}")
    
    def update_status(self, proposal_id: Union[str, ObjectId], status: Union[str, ProposalStatus]) -> Optional[Proposal]:
        """
        Update proposal status.
        
        Args:
            proposal_id: ID of the proposal
            status: New status to set
            
        Returns:
            Optional[Proposal]: Updated proposal or None
            
        Raises:
             If database operation fails
        """
        try:
            proposal_id = ObjectId(proposal_id) if isinstance(proposal_id, str) else proposal_id
            status_str = status.value if isinstance(status, ProposalStatus) else status
            
            update_data = {
                "current_status": status_str,
                "updated_at": datetime.utcnow()
            }
            
            if status_str == ProposalStatus.SENT.value:
                update_data["timestamps.sent_at"] = datetime.utcnow()
            
            return self.update(proposal_id, update_data)
        except PyMongoError as e:
            raise ValueError(f"Error updating proposal status: {str(e)}")
    
    def find_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Proposal]:
        """
        Find proposals created within a date range.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            List[Proposal]: List of matching proposals
            
        Raises:
             If database operation fails
        """
        try:
            cursor = self.collection.find({
                "timestamps.created_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            })
            return [self._map_to_model(doc) for doc in cursor]
        except PyMongoError as e:
            raise ValueError(f"Error finding proposals by date range: {str(e)}")
    
    def find_by_user(self, user_id: Union[str, ObjectId], limit: int = 10) -> List[Proposal]:
        """
        Find proposals created or modified by a specific user.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of results to return
            
        Returns:
            List[Proposal]: List of matching proposals
            
        Raises:
             If database operation fails
        """
        try:
            user_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
            cursor = self.collection.find({
                "$or": [
                    {"proposal_versions.modified_by": user_id},
                    {"approval_history.user_id": user_id}
                ]
            }).limit(limit)
            return [self._map_to_model(doc) for doc in cursor]
        except PyMongoError as e:
            raise ValueError(f"Error finding proposals by user: {str(e)}")
    
    def update(self, id: str, update_dict: Union[Dict[str, Any], ProposalUpdate]) -> Optional[Proposal]:
        """Update a document by ID."""
        try:
            # Convert ProposalUpdate to dict if needed
            if isinstance(update_dict, ProposalUpdate):
                update_dict = self._convert_update_to_dict(update_dict)
                
            self.collection.update_one(
                {"_id": ObjectId(id)},
                {"$set": update_dict}
            )
            return self.find_by_id(id)
        except Exception as e:
            raise ValueError(f"Error updating document: {str(e)}")