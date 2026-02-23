from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from app.db.base import get_db
from app.db.models import HealthReport, User, Patient, UserRole, MedicalRecord
from app.core.security import decode_access_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime
import json

router = APIRouter(prefix="/reports", tags=["reports"])
security = HTTPBearer()


class HealthReportCreate(BaseModel):
    patient_id: int
    report_type: str = "summary"  # summary, detailed, etc.


class HealthReportResponse(BaseModel):
    id: int
    patient_id: int
    report_type: str
    report_data: dict
    pdf_path: str = None
    created_at: datetime
    
    class Config:
        from_attributes = True


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


@router.post("/", response_model=HealthReportResponse)
def generate_health_report(
    report_request: HealthReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a health status report for a patient"""
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == report_request.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Check permissions
    if current_user.role == UserRole.PATIENT:
        if patient.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get patient medical records
    medical_records = db.query(MedicalRecord).filter(
        MedicalRecord.patient_id == report_request.patient_id
    ).order_by(MedicalRecord.visit_date.desc()).limit(10).all()
    
    # Generate report data
    report_data = {
        "patient_info": {
            "id": patient.id,
            "name": patient.user.full_name if patient.user else "Unknown",
            "date_of_birth": str(patient.date_of_birth) if patient.date_of_birth else None,
            "blood_type": patient.blood_type,
            "gender": patient.gender
        },
        "medical_history": patient.medical_history or [],
        "allergies": patient.allergies or [],
        "current_medications": patient.current_medications or [],
        "recent_visits": [
            {
                "date": str(record.visit_date),
                "diagnosis": record.diagnosis,
                "treatment": record.treatment_plan
            }
            for record in medical_records
        ],
        "generated_at": datetime.utcnow().isoformat()
    }
    
    # Create health report record
    health_report = HealthReport(
        patient_id=report_request.patient_id,
        report_type=report_request.report_type,
        report_data=report_data
    )
    db.add(health_report)
    db.commit()
    db.refresh(health_report)
    
    # TODO: Generate PDF using report_service
    
    return health_report


@router.get("/patient/{patient_id}", response_model=List[HealthReportResponse])
def get_patient_reports(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all health reports for a patient"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Check permissions
    if current_user.role == UserRole.PATIENT:
        if patient.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    reports = db.query(HealthReport).filter(
        HealthReport.patient_id == patient_id
    ).order_by(HealthReport.created_at.desc()).all()
    
    return reports


@router.get("/{report_id}", response_model=HealthReportResponse)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific health report"""
    report = db.query(HealthReport).filter(HealthReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Check permissions
    patient = db.query(Patient).filter(Patient.id == report.patient_id).first()
    if current_user.role == UserRole.PATIENT:
        if patient.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    return report


@router.get("/{report_id}/pdf")
def download_report_pdf(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download health report as PDF"""
    report = db.query(HealthReport).filter(HealthReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Check permissions
    patient = db.query(Patient).filter(Patient.id == report.patient_id).first()
    if current_user.role == UserRole.PATIENT:
        if patient.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    # TODO: Generate PDF if not exists
    if not report.pdf_path:
        raise HTTPException(status_code=404, detail="PDF not generated yet")
    
    return FileResponse(report.pdf_path, media_type="application/pdf", filename=f"health_report_{report_id}.pdf")
