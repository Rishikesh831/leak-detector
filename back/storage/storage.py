"""
File storage service
Handles file uploads and retrieval for the Leak Detector application
"""
import os
import uuid
import aiofiles
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
from datetime import datetime

# Storage configuration
STORAGE_BASE_DIR = Path(__file__).parent.parent.parent / "data" / "uploads"
MAX_FILE_SIZE_MB = 100  # Maximum upload size in MB


class StorageService:
    """Handles file upload and storage operations"""
    
    def __init__(self, base_dir: Path = STORAGE_BASE_DIR):
        self.base_dir = base_dir
        self._ensure_directory_exists()
    
    def _ensure_directory_exists(self):
        """Create storage directory if it doesn't exist"""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Storage directory: {self.base_dir}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent directory traversal
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove any path components
        filename = os.path.basename(filename)
        
        # Replace spaces and special characters
        filename = filename.replace(" ", "_")
        
        # Keep only alphanumeric, dots, hyphens, and underscores
        allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
        filename = "".join(c for c in filename if c in allowed_chars)
        
        return filename
    
    def _generate_unique_filename(self, original_filename: str) -> str:
        """
        Generate unique filename with timestamp and UUID
        
        Args:
            original_filename: Original filename with extension
            
        Returns:
            Unique filename
        """
        # Split filename and extension
        name_parts = original_filename.rsplit(".", 1)
        if len(name_parts) == 2:
            name, ext = name_parts
        else:
            name = original_filename
            ext = ""
        
        # Sanitize name
        name = self._sanitize_filename(name)
        
        # Create unique filename: name_timestamp_uuid.ext
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        if ext:
            unique_filename = f"{name}_{timestamp}_{unique_id}.{ext}"
        else:
            unique_filename = f"{name}_{timestamp}_{unique_id}"
        
        return unique_filename
    
    async def save_file(self, file: UploadFile) -> tuple[str, int]:
        """
        Save uploaded file to storage
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            Tuple of (file_path, file_size_bytes)
            
        Raises:
            ValueError: If file is too large or invalid
        """
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        max_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_size_bytes:
            raise ValueError(f"File too large. Maximum size: {MAX_FILE_SIZE_MB}MB")
        
        # Generate unique filename
        unique_filename = self._generate_unique_filename(file.filename)
        file_path = self.base_dir / unique_filename
        
        # Save file asynchronously
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                contents = await file.read()
                await f.write(contents)
            
            print(f"✅ File saved: {file_path}")
            return str(file_path), file_size
            
        except Exception as e:
            print(f"❌ Error saving file: {e}")
            # Clean up partial file if it exists
            if file_path.exists():
                file_path.unlink()
            raise e
    
    def get_file_path(self, upload_id: str, filename: str) -> Optional[Path]:
        """
        Get file path for a given upload_id
        
        Args:
            upload_id: UUID of the upload
            filename: Stored filename
            
        Returns:
            Path object if file exists, None otherwise
        """
        file_path = Path(filename)
        
        if file_path.exists():
            return file_path
        
        return None
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage
        
        Args:
            file_path: Path to file
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                print(f"🗑️ File deleted: {file_path}")
                return True
            return False
        except Exception as e:
            print(f"❌ Error deleting file: {e}")
            return False
    
    def get_storage_stats(self) -> dict:
        """
        Get storage statistics
        
        Returns:
            Dictionary with storage info
        """
        if not self.base_dir.exists():
            return {
                "total_files": 0,
                "total_size_mb": 0,
                "storage_path": str(self.base_dir)
            }
        
        files = list(self.base_dir.iterdir())
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        
        return {
            "total_files": len(files),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "storage_path": str(self.base_dir)
        }


# Singleton instance
storage_service = StorageService()


def get_storage_service() -> StorageService:
    """Get the storage service singleton instance"""
    return storage_service
