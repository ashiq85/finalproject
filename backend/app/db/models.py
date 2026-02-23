from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum


class UserRole(str, enum.Enum):
    """User role enumeration"""
    ADMIN = "admin"
    DOCTOR = "doctor"
    PATIENT = "patient"


class AlertSeverity(str, enum.Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AppointmentStatus(str, enum.Enum):
    """Appointment status"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULE_REQUESTED = "reschedule_requested"


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    patient_profile = relationship("Patient", back_populates="user", uselist=False, foreign_keys="Patient.user_id")
    doctor_appointments = relationship("Appointment", foreign_keys="Appointment.doctor_id", back_populates="doctor")
    patients = relationship("Patient", back_populates="primary_doctor", foreign_keys="Patient.primary_doctor_id")


class Patient(Base):
    """Patient model with EHR data"""
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    date_of_birth = Column(DateTime)
    gender = Column(String(20))
    blood_type = Column(String(5))
    phone = Column(String(20))
    address = Column(Text)
    emergency_contact = Column(String(100))
    emergency_phone = Column(String(20))
    medical_history = Column(JSON)  # Store as JSON
    allergies = Column(JSON)  # List of allergies
    current_medications = Column(JSON)  # List of medications
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    medical_id = Column(String, unique=True, index=True, nullable=True)
    primary_doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="patient_profile", foreign_keys=[user_id])
    primary_doctor = relationship("User", foreign_keys=[primary_doctor_id], back_populates="patients")
    appointments = relationship("Appointment", back_populates="patient")
    medical_records = relationship("MedicalRecord", back_populates="patient")
    documents = relationship("Document", back_populates="patient")
    alerts = relationship("Alert", back_populates="patient")
    health_reports = relationship("HealthReport", back_populates="patient")
    health_metrics = relationship("HealthMetric", back_populates="patient")


class Appointment(Base):
    """Appointment model with follow-up tracking"""
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    appointment_date = Column(DateTime, nullable=False)
    requested_new_date = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, default=30)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED)
    reason = Column(Text)
    notes = Column(Text)
    is_follow_up = Column(Boolean, default=False)
    parent_appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("User", foreign_keys=[doctor_id])
    notifications = relationship("Notification", back_populates="appointment")


class MedicalRecord(Base):
    """Medical record model"""
    __tablename__ = "medical_records"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    visit_date = Column(DateTime, nullable=False)
    chief_complaint = Column(Text)
    symptoms = Column(JSON)  # List of symptoms
    vitals = Column(JSON)  # Vital signs
    diagnosis = Column(Text)
    treatment_plan = Column(Text)
    prescriptions = Column(JSON)  # List of prescriptions
    lab_results = Column(JSON)  # Lab test results
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="medical_records")


class Document(Base):
    """Document model for uploaded files"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String)
    file_size = Column(Integer)
    document_type = Column(String)  # lab_report, prescription, imaging, etc.
    extracted_data = Column(JSON)  # Extracted information
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="documents")


class Alert(Base):
    """Alert model for critical health notifications"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    severity = Column(Enum(AlertSeverity), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    recommended_actions = Column(JSON)  # List of recommended actions
    is_resolved = Column(Boolean, default=False)
    auto_booked_appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    
    # Relationships
    patient = relationship("Patient", back_populates="alerts")


class HealthReport(Base):
    """Health report model"""
    __tablename__ = "health_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    report_type = Column(String)  # summary, detailed, etc.
    report_data = Column(JSON)  # Report content
    pdf_path = Column(String)  # Path to generated PDF
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="health_reports")


class HealthMetric(Base):
    """Model for tracking health metrics like sugar, pressure, cholesterol, etc."""
    __tablename__ = "health_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    metric_name = Column(String, nullable=False)  # sugar_before, sugar_after, bp_systolic, bp_diastolic, cholesterol, etc.
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="health_metrics")


class Notification(Base):
    """Notification model"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notification_type = Column(String)  # appointment, alert, reminder, etc.
    title = Column(String, nullable=False)
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    appointment = relationship("Appointment", back_populates="notifications")


class AuditLog(Base):
    """Audit log for HIPAA compliance"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String, nullable=False)
    resource_type = Column(String)
    resource_id = Column(Integer)
    details = Column(JSON)
    ip_address = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
