"""
File utilities for common file operations.
Provides functions for safe file handling, file type validation, and more.
"""

import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union, BinaryIO, Iterator, Tuple, Dict
import mimetypes
import zipfile
import logging

from utils.hash import hash_file, verify_file_hash

# Setup logger
logger = logging.getLogger(__name__)


def ensure_directory(directory_path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to directory
        
    Returns:
        Path object of the directory
    """
    dir_path = Path(directory_path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def safe_filename(filename: str) -> str:
    """
    Convert a string to a safe filename by removing/replacing unsafe characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename
    """
    # Replace problematic characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # Limit length to avoid filesystem limitations
    if len(filename) > 255:
        base, ext = os.path.splitext(filename)
        filename = f"{base[:255-len(ext)]}{ext}"
        
    return filename


def get_file_extension(file_path: Union[str, Path]) -> str:
    """
    Get the extension of a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        File extension with dot (e.g., '.txt')
    """
    return os.path.splitext(str(file_path))[1].lower()


def get_mime_type(file_path: Union[str, Path]) -> str:
    """
    Get the MIME type of a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        MIME type string
    """
    mime_type, _ = mimetypes.guess_type(str(file_path))
    return mime_type or 'application/octet-stream'


def is_valid_filetype(file_path: Union[str, Path], allowed_extensions: List[str]) -> bool:
    """
    Check if a file has a valid extension.
    
    Args:
        file_path: Path to file
        allowed_extensions: List of allowed extensions (with or without dots)
        
    Returns:
        True if valid, False otherwise
    """
    # Ensure extensions have dots
    allowed = [ext if ext.startswith('.') else f'.{ext}' for ext in allowed_extensions]
    
    # Check extension
    extension = get_file_extension(file_path)
    return extension.lower() in [ext.lower() for ext in allowed]


def create_temp_file(content: Union[str, bytes], suffix: Optional[str] = None) -> Path:
    """
    Create a temporary file with content.
    
    Args:
        content: File content (string or bytes)
        suffix: Optional file extension
        
    Returns:
        Path to temporary file
    """
    fd, temp_path = tempfile.mkstemp(suffix=suffix)
    
    try:
        # Convert string to bytes if needed
        if isinstance(content, str):
            content = content.encode('utf-8')
            
        with os.fdopen(fd, 'wb') as temp_file:
            temp_file.write(content)
            
    except Exception as e:
        # Close and remove file on error
        os.unlink(temp_path)
        raise e
        
    return Path(temp_path)


def backup_file(file_path: Union[str, Path], backup_dir: Optional[Union[str, Path]] = None) -> Path:
    """
    Create a backup of a file.
    
    Args:
        file_path: Path to file
        backup_dir: Optional directory for backups
        
    Returns:
        Path to backup file
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Create backup dir if specified, otherwise use the same directory
    if backup_dir:
        backup_path = Path(backup_dir)
        ensure_directory(backup_path)
    else:
        backup_path = file_path.parent
    
    # Create a backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = file_path.name
    backup_file = backup_path / f"{filename}.{timestamp}.bak"
    
    # Copy the file
    shutil.copy2(file_path, backup_file)
    
    return backup_file


def zip_files(files: List[Union[str, Path]], output_path: Union[str, Path], 
              base_dir: Optional[Union[str, Path]] = None) -> Path:
    """
    Create a zip archive containing specified files.
    
    Args:
        files: List of file paths to include
        output_path: Path for the output zip file
        base_dir: Optional base directory for relative paths in archive
        
    Returns:
        Path to created zip file
    """
    output_path = Path(output_path)
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files:
            file_path = Path(file_path)
            
            if not file_path.exists():
                logger.warning(f"File not found, skipping: {file_path}")
                continue
                
            # Determine archive path
            if base_dir:
                try:
                    # Calculate relative path from base_dir
                    rel_path = file_path.relative_to(base_dir)
                    archive_path = str(rel_path)
                except ValueError:
                    # Use filename if not relative to base_dir
                    archive_path = file_path.name
            else:
                archive_path = file_path.name
                
            zipf.write(file_path, archive_path)
            
    return output_path


def read_in_chunks(file_obj: BinaryIO, chunk_size: int = 4096) -> Iterator[bytes]:
    """
    Generator to read a file in chunks.
    
    Args:
        file_obj: File object opened in binary mode
        chunk_size: Size of chunks to read
        
    Yields:
        Chunks of the file
    """
    while True:
        data = file_obj.read(chunk_size)
        if not data:
            break
        yield data


def get_file_size(file_path: Union[str, Path]) -> int:
    """
    Get the size of a file in bytes.
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in bytes
    """
    return os.path.getsize(file_path)


def remove_files(file_paths: List[Union[str, Path]], ignore_errors: bool = False) -> None:
    """
    Remove multiple files.
    
    Args:
        file_paths: List of file paths to remove
        ignore_errors: Whether to ignore errors
        
    Returns:
        None
    """
    for file_path in file_paths:
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
        except Exception as e:
            if not ignore_errors:
                raise e
            logger.warning(f"Error removing file {file_path}: {e}")


def scan_directory(directory: Union[str, Path], 
                  pattern: str = "*", 
                  recursive: bool = True) -> List[Path]:
    """
    Scan a directory for files matching a pattern.
    
    Args:
        directory: Directory to scan
        pattern: Glob pattern to match
        recursive: Whether to scan recursively
        
    Returns:
        List of matching file paths
    """
    directory = Path(directory)
    
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    if recursive:
        return list(directory.glob(f"**/{pattern}"))
    else:
        return list(directory.glob(pattern))


def verify_file_integrity(file_path: Union[str, Path], 
                         expected_hash: Optional[str] = None, 
                         hash_algorithm: str = 'sha256') -> bool:
    """
    Verify the integrity of a file using hash comparison.
    
    Args:
        file_path: Path to the file to verify
        expected_hash: Expected hash value, if None saves the current hash
        hash_algorithm: Hash algorithm to use
        
    Returns:
        True if integrity check passes, False otherwise
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return False
    
    if expected_hash is None:
        # If no expected hash provided, assume we're saving the hash
        hash_file(file_path, algorithm=hash_algorithm)
        return True
    else:
        # Verify the file against the expected hash
        return verify_file_hash(file_path, expected_hash, algorithm=hash_algorithm)
        

def save_file_with_integrity(file_path: Union[str, Path],
                           content: bytes,
                           hash_algorithm: str = 'sha256') -> Tuple[bool, str]:
    """
    Save a file and compute its hash for integrity verification.
    
    Args:
        file_path: Path where to save the file
        content: Binary content to save
        hash_algorithm: Hash algorithm to use
        
    Returns:
        Tuple of (success, file_hash)
    """
    file_path = Path(file_path)
    
    # Create parent directories if they don't exist
    os.makedirs(file_path.parent, exist_ok=True)
    
    try:
        # Write the file
        with open(file_path, 'wb') as f:
            f.write(content)
            
        # Compute the file hash
        file_hash = hash_file(file_path, algorithm=hash_algorithm)
        
        return True, file_hash
    except Exception as e:
        print(f"Error saving file with integrity check: {e}")
        return False, "" 