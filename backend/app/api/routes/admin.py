from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.db.base import get_db
from app.db.models import User, UserRole, Patient
from app.schemas import UserCreate, UserResponse, PatientResponse
from app.api.routes.auth import get_current_user
from app.core.security import get_password_hash
import random, string

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
    patients = db.query(Patient).options(joinedload(Patient.user)).all()
    return patients


@router.post("/patients", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_patient(
    data: dict,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Admin endpoint to create a new patient account"""
    email = data.get("email")
    full_name = data.get("full_name")
    password = data.get("password")

    if not email or not full_name or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email, full_name, and password are required"
        )

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    hashed_password = get_password_hash(password)
    new_user = User(
        email=email,
        full_name=full_name,
        role=UserRole.PATIENT,
        hashed_password=hashed_password,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate medical ID
    while True:
        digits = ''.join(random.choices(string.digits, k=5))
        medical_id = f"AH-{digits}"
        exists = db.query(Patient).filter(Patient.medical_id == medical_id).first()
        if not exists:
            break

    # Create patient profile
    patient = Patient(
        user_id=new_user.id,
        medical_id=medical_id,
        gender=data.get("gender"),
        blood_type=data.get("blood_type"),
        phone=data.get("phone"),
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    # Load with user relation
    patient = db.query(Patient).options(joinedload(Patient.user)).filter(Patient.id == patient.id).first()
    return patient


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
