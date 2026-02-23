from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.base import get_db
from app.db.models import Alert, User, Patient, AlertSeverity, UserRole
from app.core.security import decode_access_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/alerts", tags=["alerts"])
security = HTTPBearer()


class AlertCreate(BaseModel):
    patient_id: int
    severity: AlertSeverity
    title: str
    description: str = None
    recommended_actions: List[str] = []


class AlertResponse(BaseModel):
    id: int
    patient_id: int
    severity: AlertSeverity
    title: str
    description: str = None
    recommended_actions: List = []
    is_resolved: bool
    created_at: datetime
    resolved_at: datetime = None
    
    class Config:
        from_attributes = True


class EmergencyAlertRequest(BaseModel):
    patient_id: int
    emergency_type: str  # stroke, heart_attack, cardiac_arrest
    symptoms: List[str]
    vital_signs: dict = None


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current authenticated user"""
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@router.post("/", response_model=AlertResponse)
def create_alert(
    alert: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new alert"""
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == alert.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Create alert
    db_alert = Alert(**alert.dict())
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    
    # TODO: Send notifications based on severity
    
    return db_alert


@router.post("/emergency", response_model=AlertResponse)
async def trigger_emergency_alert(
    request: EmergencyAlertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger an emergency alert for critical health conditions"""
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == request.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Create critical alert
    alert = Alert(
        patient_id=request.patient_id,
        severity=AlertSeverity.CRITICAL,
        title=f"EMERGENCY: {request.emergency_type.replace('_', ' ').title()}",
        description=f"Emergency detected: {', '.join(request.symptoms)}",
        recommended_actions=[
            "Call emergency services immediately (911)",
            "Do not leave patient alone",
            "Follow emergency protocol guidance"
        ]
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    # TODO: Integrate with emergency_detection_agent
    # TODO: Send emergency notifications to all contacts
    # TODO: Auto-book emergency appointment
    
    return alert


@router.get("/", response_model=List[AlertResponse])
def get_alerts(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get alerts based on user role"""
    query = db.query(Alert)
    
    if active_only:
        query = query.filter(Alert.is_resolved == False)
    
    if current_user.role == UserRole.PATIENT:
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient:
            return []
        query = query.filter(Alert.patient_id == patient.id)
    
    alerts = query.offset(skip).limit(limit).all()
    return alerts


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Check permissions
    if current_user.role == UserRole.PATIENT:
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient or alert.patient_id != patient.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    return alert


@router.put("/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resolve an alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Only doctors and admins can resolve alerts
    if current_user.role == UserRole.PATIENT:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    alert.is_resolved = True
    alert.resolved_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Alert resolved successfully"}
