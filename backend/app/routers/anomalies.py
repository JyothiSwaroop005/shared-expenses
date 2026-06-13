from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.import_anomaly import ImportAnomaly
from app.schemas.import_schema import AnomalyOut, AnomalyReviewRequest

router = APIRouter(prefix="/anomalies", tags=["Anomalies"])


@router.get("/session/{session_id}", response_model=List[AnomalyOut])
def get_anomalies_for_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all anomalies detected in a specific import session."""
    return (
        db.query(ImportAnomaly)
        .filter(ImportAnomaly.import_session_id == session_id)
        .all()
    )


@router.get("/pending", response_model=List[AnomalyOut])
def get_pending_anomalies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return all anomalies that have not yet been reviewed.
    This is Meera's view: "Duplicates must be reviewed before deletion."
    """
    return (
        db.query(ImportAnomaly)
        .filter(ImportAnomaly.reviewed == "pending")
        .order_by(ImportAnomaly.created_at.desc())
        .all()
    )


@router.patch("/{anomaly_id}/review", response_model=AnomalyOut)
def review_anomaly(
    anomaly_id: int,
    data: AnomalyReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark an anomaly as reviewed.
    decision = "approved": user confirms the row should be imported despite the anomaly
    decision = "rejected": user confirms the row should be permanently skipped
    
    This satisfies Meera's requirement for human review before action.
    """
    if data.decision not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Decision must be 'approved' or 'rejected'")

    anomaly = db.query(ImportAnomaly).filter(ImportAnomaly.id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")

    anomaly.reviewed = data.decision
    anomaly.action_taken = "imported_with_warning" if data.decision == "approved" else "rejected"
    db.commit()
    db.refresh(anomaly)
    return anomaly
