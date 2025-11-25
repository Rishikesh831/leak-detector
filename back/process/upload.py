from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Any
from sqlalchemy.orm import Session
import pandas as pd
import io

from database import get_db, Upload
from storage import get_storage_service

router = APIRouter()


class UploadResponse(BaseModel):
    """Response model for file upload"""
    upload_id: str = Field(..., description="Unique identifier for the upload")
    filename: str = Field(..., description="Original filename")
    rows: int = Field(..., description="Number of rows in the dataset")
    columns: int = Field(..., description="Number of columns in the dataset")
    preview: List[List[Any]] = Field(..., description="First 10 rows of the dataset")


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a CSV file for leak detection analysis.
    
    Args:
        file: CSV file to upload
        db: Database session (injected)
        
    Returns:
        UploadResponse: Upload metadata and data preview
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400, 
            detail="Only CSV files are supported"
        )
    
    try:
        # Read the file content
        contents = await file.read()
        
        # Parse CSV using pandas
        df = pd.read_csv(io.BytesIO(contents))
        
        # Validate CSV is not empty
        if df.empty:
            raise HTTPException(status_code=400, detail="The uploaded CSV file is empty")
        
        # Get rows and columns count
        rows, columns = df.shape
        
        # Reset file pointer for storage
        file.file.seek(0)
        await file.seek(0)
        
        # Save file using storage service
        storage_service = get_storage_service()
        file_path, file_size = await storage_service.save_file(file)
        
        # Create database record
        upload = Upload(
            filename=file.filename,
            rows_count=rows,
            columns_count=columns,
            file_path=file_path,
            status="uploaded"
        )
        
        db.add(upload)
        db.commit()
        db.refresh(upload)
        
        # Get preview (first 10 rows as list of lists)
        preview_df = df.head(10)
        preview = preview_df.values.tolist()
        
        print(f"✅ Upload successful: {upload.id} - {file.filename} ({rows} rows)")
        
        return UploadResponse(
            upload_id=str(upload.id),
            filename=file.filename,
            rows=rows,
            columns=columns,
            preview=preview
        )
        
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="The uploaded CSV file is empty")
    except pd.errors.ParserError:
        raise HTTPException(status_code=400, detail="Invalid CSV file format")
    except Exception as e:
        db.rollback()
        print(f"❌ Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")