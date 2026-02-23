from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.base import get_db
from app.db.models import User, UserRole, Patient
from app.schemas import UserCreate, UserResponse, PatientResponse
from app.api.routes.auth import get_current_user
from app.core.security import get_password_hash

router = APIRouter(prefix="/admin", tags=["Admin"])


async def require_admin(current_user: User = Depends(get_current_user)):
    """Dependency to require admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.post("/doctors", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_doctor(
    doctor_data: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Admin endpoint to create a new doctor account"""
    # Force role to be doctor
    if doctor_data.role != UserRole.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint is for creating doctor accounts only"
        )
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == doctor_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create doctor account
    hashed_password = get_password_hash(doctor_data.password)
    new_doctor = User(
        email=doctor_data.email,
        full_name=doctor_data.full_name,
        role=UserRole.DOCTOR,
        hashed_password=hashed_password,
        is_active=True,
        specialization=doctor_data.specialization
    )
    
    db.add(new_doctor)
    db.commit()
    db.refresh(new_doctor)
    
    return new_doctor


@router.get("/doctors", response_model=List[UserResponse])
async def get_all_doctors(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Get all doctors in the system"""
    doctors = db.query(User).filter(User.role == UserRole.DOCTOR).all()
    return doctors


@router.put("/doctors/{doctor_id}/deactivate")
async def deactivate_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Deactivate a doctor account"""
    doctor = db.query(User).filter(
        User.id == doctor_id,
        User.role == UserRole.DOCTOR
    ).first()
    
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )
    
    doctor.is_active = False
    db.commit()
    
    return {"message": "Doctor deactivated successfully"}


@router.put("/doctors/{doctor_id}/activate")
async def activate_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Activate a doctor account"""
    doctor = db.query(User).filter(
        User.id == doctor_id,
        User.role == UserRole.DOCTOR
    ).first()
    
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )
    
    doctor.is_active = True
    db.commit()
    
    return {"message": "Doctor activated successfully"}


@router.get("/patients", response_model=List[PatientResponse])
async def get_all_patients(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Get all patients in the system"""
    patients = db.query(Patient).all()
    return patients


@router.put("/patients/{patient_id}/deactivate")
async def deactivate_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Deactivate a patient account"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    user = db.query(User).filter(User.id == patient.user_id).first()
    if user:
        user.is_active = False
        db.commit()
    
    return {"message": "Patient deactivated successfully"}


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    role: UserRole = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Get all users, optionally filtered by role"""
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    
    users = query.all()
    return users
