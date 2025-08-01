"""
File monitoring utilities for detecting when files are completely written
"""
import os
import time
import logging
import sys
from typing import Optional

# Configure logging to write to stderr to avoid interference with tqdm
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.propagate = False


class FileStabilityMonitor:
    """
    Monitors file stability to detect when a file has finished being written
    """
    
    def __init__(self, stability_time: int=5, max_wait_time: int=300, check_interval: float=1.0):
        """
        Initialize the file stability monitor
        
        Args:
            stability_time: Number of consecutive stable checks required
            max_wait_time: Maximum time to wait for stability (seconds)
            check_interval: Time between checks (seconds)
        """
        self.stability_time = stability_time
        self.max_wait_time = max_wait_time
        self.check_interval = check_interval
    
    def wait_for_stability(self, file_path: str) -> bool:
        """
        Wait for a file to become stable (not changing)
        
        Args:
            file_path: Path to the file to monitor
            
        Returns:
            True if file became stable, False if timeout or error
        """
        if not os.path.exists(file_path):
            logger.error(f"File {file_path} does not exist")
            return False
        
        logger.info(f"Starting stability check for {file_path}")
        
        previous_size = -1
        previous_mtime = -1
        stable_count = 0
        start_time = time.time()
        
        while stable_count < self.stability_time:
            try:
                # Check timeout
                if time.time() - start_time > self.max_wait_time:
                    logger.warning(f"File {file_path} stability check timed out after {self.max_wait_time} seconds")
                    return False
                
                # Get current file stats
                current_size = os.path.getsize(file_path)
                current_mtime = os.path.getmtime(file_path)
                
                # Check if file is stable (size and modification time unchanged)
                if current_size == previous_size and current_mtime == previous_mtime:
                    stable_count += 1
                    logger.debug(f"File {file_path} stable for {stable_count}/{self.stability_time} checks "
                               f"(size: {current_size}, mtime: {current_mtime})")
                else:
                    stable_count = 0
                    previous_size = current_size
                    previous_mtime = current_mtime
                    logger.debug(f"File {file_path} changed - size: {current_size}, mtime: {current_mtime}")
                
                time.sleep(self.check_interval)
                
            except FileNotFoundError:
                logger.error(f"File {file_path} not found during stability check")
                return False
            except Exception as e:
                logger.error(f"Error checking file stability for {file_path}: {e}")
                return False
        
        logger.info(f"File {file_path} is stable and ready for processing")
        return True
    
    def is_file_accessible(self, file_path: str) -> bool:
        """
        Check if a file is accessible and not locked by another process
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if file is accessible, False otherwise
        """
        try:
            # Try to open the file in read mode
            with open(file_path, 'rb') as f:
                # Try to read a small amount to ensure file is not locked
                f.read(1)
                f.seek(0)  # Reset position
            return True
        except (IOError, OSError) as e:
            logger.debug(f"File {file_path} is not accessible: {e}")
            return False
    
    def wait_for_accessibility(self, file_path: str, timeout: int=60) -> bool:
        """
        Wait for a file to become accessible
        
        Args:
            file_path: Path to the file to check
            timeout: Maximum time to wait (seconds)
            
        Returns:
            True if file became accessible, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_file_accessible(file_path):
                logger.info(f"File {file_path} is now accessible")
                return True
            time.sleep(1)
        
        logger.warning(f"File {file_path} did not become accessible within {timeout} seconds")
        return False


def get_file_info(file_path: str) -> Optional[dict]:
    """
    Get detailed information about a file
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with file information or None if error
    """
    try:
        stat = os.stat(file_path)
        return {
            'size': stat.st_size,
            'mtime': stat.st_mtime,
            'ctime': stat.st_ctime,
            'atime': stat.st_atime,
            'mode': stat.st_mode,
            'uid': stat.st_uid,
            'gid': stat.st_gid
        }
    except Exception as e:
        logger.error(f"Error getting file info for {file_path}: {e}")
        return None


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB" 
