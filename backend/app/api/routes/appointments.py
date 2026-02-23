from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.db.base import get_db
from app.db.models import Appointment, User, Patient, AppointmentStatus, UserRole, Notification
from app.api.routes.auth import get_current_user
from app.schemas import AppointmentCreate, AppointmentUpdate, AppointmentResponse, AppointmentRescheduleSchema

router = APIRouter(prefix="/appointments", tags=["appointments"])

@router.post("/{appointment_id}/request-reschedule", response_model=AppointmentResponse)
async def request_reschedule(
    appointment_id: int,
    reschedule: AppointmentRescheduleSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Request to reschedule an appointment (Patient only)"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(status_code=403, detail="Only patients can request rescheduling")
    
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient or appointment.patient_id != patient.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    appointment.requested_new_date = reschedule.requested_new_date
    appointment.status = AppointmentStatus.RESCHEDULE_REQUESTED
    
    # Create notification for doctor
    notification = Notification(
        user_id=appointment.doctor_id,
        notification_type="appointment",
        title="Reschedule Request",
        message=f"Patient {current_user.full_name} has requested to reschedule an appointment to {reschedule.requested_new_date}.",
        appointment_id=appointment.id
    )
    db.add(notification)
    
    db.commit()
    db.refresh(appointment)
    return appointment


@router.post("/{appointment_id}/approve-reschedule", response_model=AppointmentResponse)
async def approve_reschedule(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve a reschedule request (Doctor/Admin only)"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if current_user.role not in [UserRole.DOCTOR, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only doctors or admins can approve rescheduling")
    
    if appointment.status != AppointmentStatus.RESCHEDULE_REQUESTED or not appointment.requested_new_date:
        raise HTTPException(status_code=400, detail="No reschedule request pending")
    
    old_date = appointment.appointment_date
    appointment.appointment_date = appointment.requested_new_date
    appointment.requested_new_date = None
    appointment.status = AppointmentStatus.SCHEDULED
    
    # Create notification for patient
    patient_user_id = db.query(Patient).filter(Patient.id == appointment.patient_id).first().user_id
    notification = Notification(
        user_id=patient_user_id,
        notification_type="appointment",
        title="Reschedule Approved",
        message=f"Your reschedule request for {old_date} has been approved. New date: {appointment.appointment_date}.",
        appointment_id=appointment.id
    )
    db.add(notification)
    
    db.commit()
    db.refresh(appointment)
    return appointment


@router.post("/{appointment_id}/reject-reschedule", response_model=AppointmentResponse)
async def reject_reschedule(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reject a reschedule request (Doctor/Admin only)"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if current_user.role not in [UserRole.DOCTOR, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only doctors or admins can reject rescheduling")
    
    if appointment.status != AppointmentStatus.RESCHEDULE_REQUESTED:
        raise HTTPException(status_code=400, detail="No reschedule request pending")
    
    appointment.requested_new_date = None
    appointment.status = AppointmentStatus.SCHEDULED
    
    # Create notification for patient
    patient_user_id = db.query(Patient).filter(Patient.id == appointment.patient_id).first().user_id
    notification = Notification(
        user_id=patient_user_id,
        notification_type="appointment",
        title="Reschedule Rejected",
        message=f"Your reschedule request for {appointment.appointment_date} was rejected. Please contact the clinic.",
        appointment_id=appointment.id
    )
    db.add(notification)
    
    db.commit()
    db.refresh(appointment)
    return appointment






@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appointment: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new appointment"""
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Verify doctor exists and has doctor role
    doctor = db.query(User).filter(User.id == appointment.doctor_id, User.role == UserRole.DOCTOR).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Create appointment
    db_appointment = Appointment(**appointment.dict())
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    
    return db_appointment


@router.get("/", response_model=List[AppointmentResponse])
async def get_appointments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get appointments based on user role"""
    if current_user.role == UserRole.ADMIN:
        appointments = db.query(Appointment).offset(skip).limit(limit).all()
    elif current_user.role == UserRole.DOCTOR:
        appointments = db.query(Appointment).filter(Appointment.doctor_id == current_user.id).offset(skip).limit(limit).all()
    else:  # Patient
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient:
            return []
        appointments = db.query(Appointment).filter(Appointment.patient_id == patient.id).offset(skip).limit(limit).all()
    
    return appointments


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific appointment"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Check permissions
    if current_user.role == UserRole.PATIENT:
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient or appointment.patient_id != patient.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    elif current_user.role == UserRole.DOCTOR:
        if appointment.doctor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    return appointment


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: int,
    appointment_update: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an appointment"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Check permissions
    if current_user.role == UserRole.PATIENT:
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient or appointment.patient_id != patient.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    elif current_user.role == UserRole.DOCTOR:
        if appointment.doctor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    # Update fields
    update_data = appointment_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(appointment, field, value)
    
    db.commit()
    db.refresh(appointment)
    return appointment


@router.delete("/{appointment_id}")
async def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel an appointment"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Check permissions
    if current_user.role == UserRole.PATIENT:
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient or appointment.patient_id != patient.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    elif current_user.role == UserRole.DOCTOR:
        if appointment.doctor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    appointment.status = AppointmentStatus.CANCELLED
    db.commit()
    return {"message": "Appointment cancelled successfully"}
