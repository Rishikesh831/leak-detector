from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import List, Any
import pandas as pd
import uuid
import io

router = APIRouter()


class UploadResponse(BaseModel):
    """Response model for file upload"""
    upload_id: str = Field(..., description="Unique identifier for the upload")
    filename: str = Field(..., description="Original filename")
    rows: int = Field(..., description="Number of rows in the dataset")
    columns: int = Field(..., description="Number of columns in the dataset")
    preview: List[List[Any]] = Field(..., description="First 10 rows of the dataset")


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a CSV file for water leak detection analysis.
    
    Args:
        file: CSV file to upload
        
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
        
        # Generate unique upload ID
        upload_id = str(uuid.uuid4())
        
        # Get rows and columns count
        rows, columns = df.shape
        
        # Get preview (first 10 rows as list of lists)
        preview_df = df.head(10)
        preview = preview_df.values.tolist()
        
        # TODO: Store the file and metadata in database
        # Example:
        # await db.save_upload(upload_id, file.filename, df)
        
        return UploadResponse(
            upload_id=upload_id,
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
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")