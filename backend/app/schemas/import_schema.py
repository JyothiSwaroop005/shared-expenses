from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Any


class AnomalyOut(BaseModel):
    id: int
    import_session_id: int
    row_number: int
    anomaly_type: str
    description: str
    raw_data: Optional[Any] = None
    action_taken: str
    reviewed: str
    created_at: datetime

    class Config:
        from_attributes = True


class AnomalyReviewRequest(BaseModel):
    # "approved" = import this row anyway | "rejected" = confirm skip
    decision: str


class ImportSessionOut(BaseModel):
    id: int
    filename: str
    uploaded_by_id: int
    total_rows: int
    imported_rows: int
    skipped_rows: int
    anomaly_count: int
    status: str
    created_at: datetime
    anomalies: List[AnomalyOut] = []

    class Config:
        from_attributes = True
