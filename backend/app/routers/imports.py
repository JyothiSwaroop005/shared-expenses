from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.import_session import ImportSession
from app.schemas.import_schema import ImportSessionOut
from app.services.csv_importer import run_import

router = APIRouter(prefix="/imports", tags=["CSV Import"])


@router.post("/", response_model=ImportSessionOut)
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload and process a CSV file.
    
    - Reads the file bytes
    - Runs the importer (anomaly detection + row import)
    - Returns the full import session with all anomalies
    
    Will NOT crash on bad data - all problems become anomaly records.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted")

    contents = await file.read()

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        session = run_import(
            file_bytes=contents,
            filename=file.filename,
            uploaded_by_id=current_user.id,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Re-query to get relationships loaded
    session = db.query(ImportSession).filter(ImportSession.id == session.id).first()
    return session


@router.get("/", response_model=List[ImportSessionOut])
def list_import_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all past import sessions, newest first."""
    return (
        db.query(ImportSession)
        .order_by(ImportSession.created_at.desc())
        .all()
    )


@router.get("/{session_id}", response_model=ImportSessionOut)
def get_import_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(ImportSession).filter(ImportSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Import session not found")
    return session
