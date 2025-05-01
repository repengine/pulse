"""
Training Review Storage Module

This module manages the storage and retrieval of data submitted for training review.
It handles both forecast and retrodiction data submissions to help improve model quality.
"""

import json
import os
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define storage paths
STORAGE_BASE_DIR = Path("./data/training_review")
FORECAST_REVIEWS_DIR = STORAGE_BASE_DIR / "forecasts"
RETRODICTION_REVIEWS_DIR = STORAGE_BASE_DIR / "retrodictions"

# Ensure directories exist
FORECAST_REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
RETRODICTION_REVIEWS_DIR.mkdir(parents=True, exist_ok=True)

# Track submissions in memory for quick access
_submissions_index = {
    "forecast": {},
    "retrodiction": {}
}


def store_training_submission(submission_type, submission_id, data, metadata=None):
    """
    Store a training review submission.
    
    Args:
        submission_type (str): Type of submission ('forecast' or 'retrodiction')
        submission_id (str): Unique identifier for the submission
        data (dict): The data to be reviewed (forecast or retrodiction data)
        metadata (dict, optional): Additional metadata about the submission
        
    Returns:
        bool: True if storage was successful, False otherwise
    """
    if submission_type not in ('forecast', 'retrodiction'):
        logger.error(f"Invalid submission type: {submission_type}")
        return False
        
    if metadata is None:
        metadata = {}
    
    # Add timestamp if not present
    if 'submission_date' not in metadata:
        metadata['submission_date'] = datetime.now().isoformat()
    
    # Create the submission package
    submission = {
        'id': submission_id,
        'data': data,
        'metadata': metadata,
        'status': 'pending_review',  # Initial status
        'created_at': metadata.get('submission_date')
    }
    
    try:
        # Determine the storage directory
        storage_dir = FORECAST_REVIEWS_DIR if submission_type == 'forecast' else RETRODICTION_REVIEWS_DIR
        
        # Save the submission to a JSON file
        file_path = storage_dir / f"{submission_id}.json"
        with open(file_path, 'w') as f:
            json.dump(submission, f, indent=2)
            
        # Update the index
        _submissions_index[submission_type][submission_id] = {
            'id': submission_id,
            'created_at': submission['created_at'],
            'status': submission['status'],
            'file_path': str(file_path)
        }
        
        logger.info(f"Stored {submission_type} submission {submission_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error storing {submission_type} submission: {str(e)}")
        return False


def get_training_submission(submission_type, submission_id):
    """
    Retrieve a training submission by ID.
    
    Args:
        submission_type (str): Type of submission ('forecast' or 'retrodiction')
        submission_id (str): The ID of the submission to retrieve
        
    Returns:
        dict: The submission data if found, None otherwise
    """
    if submission_type not in ('forecast', 'retrodiction'):
        logger.error(f"Invalid submission type: {submission_type}")
        return None
    
    try:
        # Check if in index
        if submission_id not in _submissions_index[submission_type]:
            # Try to find the file
            storage_dir = FORECAST_REVIEWS_DIR if submission_type == 'forecast' else RETRODICTION_REVIEWS_DIR
            file_path = storage_dir / f"{submission_id}.json"
            
            if not file_path.exists():
                logger.warning(f"{submission_type.capitalize()} submission {submission_id} not found")
                return None
                
            # Update the index
            with open(file_path, 'r') as f:
                submission = json.load(f)
                
            _submissions_index[submission_type][submission_id] = {
                'id': submission_id,
                'created_at': submission['created_at'],
                'status': submission['status'],
                'file_path': str(file_path)
            }
        else:
            # Load from the file path in the index
            file_path = _submissions_index[submission_type][submission_id]['file_path']
            with open(file_path, 'r') as f:
                submission = json.load(f)
        
        return submission
        
    except Exception as e:
        logger.error(f"Error retrieving {submission_type} submission {submission_id}: {str(e)}")
        return None


def list_training_submissions(submission_type, limit=50, status=None, sort_by='created_at', reverse=True):
    """
    List training submissions of a specific type.
    
    Args:
        submission_type (str): Type of submission ('forecast' or 'retrodiction')
        limit (int, optional): Maximum number of submissions to return
        status (str, optional): Filter by status (e.g., 'pending_review', 'reviewed')
        sort_by (str, optional): Field to sort by
        reverse (bool, optional): Whether to reverse the sort order
        
    Returns:
        list: List of submission summaries (without full data)
    """
    if submission_type not in ('forecast', 'retrodiction'):
        logger.error(f"Invalid submission type: {submission_type}")
        return []
    
    try:
        # Ensure the index is updated
        _refresh_index(submission_type)
        
        # Get submissions from the index
        submissions = list(_submissions_index[submission_type].values())
        
        # Apply status filter if provided
        if status is not None:
            submissions = [s for s in submissions if s['status'] == status]
        
        # Sort submissions
        submissions.sort(key=lambda s: s.get(sort_by, ''), reverse=reverse)
        
        # Apply limit
        return submissions[:limit]
        
    except Exception as e:
        logger.error(f"Error listing {submission_type} submissions: {str(e)}")
        return []


def update_training_submission_status(submission_type, submission_id, status, reviewer=None, notes=None):
    """
    Update the status of a training submission.
    
    Args:
        submission_type (str): Type of submission ('forecast' or 'retrodiction')
        submission_id (str): The ID of the submission to update
        status (str): New status (e.g., 'reviewed', 'approved', 'rejected')
        reviewer (str, optional): Name or ID of the reviewer
        notes (str, optional): Review notes
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    if submission_type not in ('forecast', 'retrodiction'):
        logger.error(f"Invalid submission type: {submission_type}")
        return False
    
    try:
        # Get the submission
        submission = get_training_submission(submission_type, submission_id)
        if not submission:
            logger.warning(f"{submission_type.capitalize()} submission {submission_id} not found")
            return False
        
        # Update the status
        submission['status'] = status
        
        # Add review info
        if 'review' not in submission:
            submission['review'] = {}
            
        submission['review']['updated_at'] = datetime.now().isoformat()
        
        if reviewer:
            submission['review']['reviewer'] = reviewer
            
        if notes:
            submission['review']['notes'] = notes
        
        # Save the updated submission
        storage_dir = FORECAST_REVIEWS_DIR if submission_type == 'forecast' else RETRODICTION_REVIEWS_DIR
        file_path = storage_dir / f"{submission_id}.json"
        
        with open(file_path, 'w') as f:
            json.dump(submission, f, indent=2)
        
        # Update the index
        _submissions_index[submission_type][submission_id]['status'] = status
        
        logger.info(f"Updated {submission_type} submission {submission_id} status to {status}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating {submission_type} submission {submission_id}: {str(e)}")
        return False


def _refresh_index(submission_type):
    """
    Refresh the index of submissions from disk.
    
    Args:
        submission_type (str): Type of submission ('forecast' or 'retrodiction')
    """
    try:
        # Determine the storage directory
        storage_dir = FORECAST_REVIEWS_DIR if submission_type == 'forecast' else RETRODICTION_REVIEWS_DIR
        
        # Scan for JSON files
        for file_path in storage_dir.glob('*.json'):
            submission_id = file_path.stem
            
            # Skip if already in index
            if submission_id in _submissions_index[submission_type]:
                continue
                
            try:
                # Read basic info without loading the full data
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                _submissions_index[submission_type][submission_id] = {
                    'id': submission_id,
                    'created_at': data.get('created_at', ''),
                    'status': data.get('status', 'unknown'),
                    'file_path': str(file_path)
                }
            except Exception as e:
                logger.warning(f"Error indexing {submission_id}: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error refreshing {submission_type} index: {str(e)}")


# Initialize indices on module load
def _init():
    """Initialize the storage system and indices."""
    _refresh_index('forecast')
    _refresh_index('retrodiction')
    logger.info("Training review store initialized")

# Call initialization
_init()