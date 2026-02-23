from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.base import get_db
from app.db.models import Patient, User, UserRole, HealthMetric
from app.schemas import PatientCreate, PatientUpdate, PatientResponse, UserCreate, HealthMetricCreate, HealthMetricResponse
from app.api.routes.auth import get_current_user
from app.core.security import get_password_hash
import random
import string

router = APIRouter(prefix="/patients", tags=["Patients"])


def generate_medical_id(db: Session) -> str:
    """Generate a unique medical ID in the format AH-XXXXX"""
    while True:
        digits = ''.join(random.choices(string.digits, k=5))
        medical_id = f"AH-{digits}"
        # Check if exists
        exists = db.query(Patient).filter(Patient.medical_id == medical_id).first()
        if not exists:
            return medical_id


@router.get("/search", response_model=List[PatientResponse])
async def search_patients(
    query: Optional[str] = Query(None, description="Search by name, email, or ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search patients by name, email, or ID (Admin/Doctor only)"""
    if current_user.role not in [UserRole.ADMIN, UserRole.DOCTOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to search patients"
        )
    
    if not query:
        return []
    
    # Search in patient and user tables
    patients = db.query(Patient).join(User, Patient.user_id == User.id).filter(
        (User.full_name.ilike(f"%{query}%")) |
        (User.email.ilike(f"%{query}%")) |
        (Patient.medical_id.ilike(f"%{query}%"))
    ).all()
    
    return patients


@router.get("/me", response_model=PatientResponse)
async def get_my_patient_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's patient profile"""
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can access this endpoint"
        )
    
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found"
        )
    
    return patient



@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new patient profile"""
    # Check if patient profile already exists
    existing = db.query(Patient).filter(Patient.user_id == patient_data.user_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient profile already exists for this user"
        )
    
    patient = Patient(**patient_data.dict())
    patient.medical_id = generate_medical_id(db)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    
    return patient


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get patient by ID"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    return patient


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    patient_data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update patient information"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Update fields
    for key, value in patient_data.dict(exclude_unset=True).items():
        setattr(patient, key, value)
    
    db.commit()
    db.refresh(patient)
    
    return patient


@router.get("/", response_model=List[PatientResponse])
async def list_patients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all patients (admin/doctor only)"""
    if current_user.role not in [UserRole.ADMIN, UserRole.DOCTOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view all patients"
        )
    
    patients = db.query(Patient).offset(skip).limit(limit).all()
    return patients


@router.post("/register", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def doctor_create_patient(
    user_data: UserCreate,
    patient_data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Doctor-initiated patient account creation"""
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can create patient accounts"
        )
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user account
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        role=UserRole.PATIENT,
        hashed_password=hashed_password,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create patient profile
    patient = Patient(
        user_id=new_user.id,
        primary_doctor_id=current_user.id,
        medical_id=generate_medical_id(db),
        **patient_data.dict(exclude={"user_id", "primary_doctor_id"})
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    
    return patient


@router.put("/{patient_id}/assign-doctor/{doctor_id}", response_model=PatientResponse)
async def assign_doctor(
    patient_id: int,
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign a primary doctor to a patient (Admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can assign doctors to patients"
        )
    
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    doctor = db.query(User).filter(User.id == doctor_id, User.role == UserRole.DOCTOR).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
        
    patient.primary_doctor_id = doctor_id
    db.commit()
    db.refresh(patient)
    
    return patient


# Health Metric Endpoints
@router.get("/{patient_id}/health-metrics", response_model=List[HealthMetricResponse])
async def get_health_metrics(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get health metrics for a specific patient"""
    # Check permissions (doctor or patient themselves)
    if current_user.role == UserRole.PATIENT:
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient or patient.id != patient_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    metrics = db.query(HealthMetric).filter(HealthMetric.patient_id == patient_id).order_by(HealthMetric.recorded_at.desc()).all()
    return metrics


@router.post("/{patient_id}/health-metrics", response_model=HealthMetricResponse)
async def log_health_metric(
    patient_id: int,
    metric_data: HealthMetricCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Log a new health metric for a patient"""
    # Confirm patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    # Check permissions
    if current_user.role == UserRole.PATIENT:
        if patient.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
            
    db_metric = HealthMetric(
        patient_id=patient_id,
        **metric_data.dict()
    )
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)
    
    return db_metric
