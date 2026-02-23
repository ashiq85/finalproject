from sqlalchemy.orm import Session
from app.db.models import Alert, AlertSeverity, Patient, Appointment, AppointmentStatus
from app.services.notification_service import send_email_notification
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AlertService:
    """Service for managing health alerts and emergency detection"""
    
    @staticmethod
    def create_alert(
        db: Session,
        patient_id: int,
        severity: AlertSeverity,
        title: str,
        description: str,
        recommended_actions: list = None,
        auto_book_appointment: bool = False
    ) -> Alert:
        """
        Create a health alert for a patient.
        
        Args:
            db: Database session
            patient_id: Patient ID
            severity: Alert severity level
            title: Alert title
            description: Alert description
            recommended_actions: List of recommended actions
            auto_book_appointment: Whether to auto-book an appointment for critical alerts
        
        Returns:
            Created alert
        """
        try:
            # Create alert
            alert = Alert(
                patient_id=patient_id,
                severity=severity,
                title=title,
                description=description,
                recommended_actions=recommended_actions or []
            )
            
            db.add(alert)
            db.commit()
            db.refresh(alert)
            
            logger.info(f"Created {severity} alert for patient {patient_id}")
            
            # Send notification based on severity
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
            if patient and patient.user:
                if severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
                    send_email_notification(
                        to_email=patient.user.email,
                        subject=f"URGENT: {title}",
                        body=f"{description}\n\nRecommended Actions:\n" + 
                             "\n".join(f"- {action}" for action in (recommended_actions or []))
                    )
                    
                    # Notify emergency contact for critical alerts
                    if severity == AlertSeverity.CRITICAL and patient.emergency_contact:
                        logger.info(f"Emergency contact notification needed for patient {patient_id}")
            
            # Auto-book appointment for critical cases
            if auto_book_appointment and severity == AlertSeverity.CRITICAL:
                AlertService._auto_book_emergency_appointment(db, patient_id, alert.id)
            
            return alert
        
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def _auto_book_emergency_appointment(db: Session, patient_id: int, alert_id: int):
        """Auto-book an emergency appointment"""
        try:
            from app.db.models import User, UserRole
            
            # Find first available doctor
            doctor = db.query(User).filter(User.role == UserRole.DOCTOR, User.is_active == True).first()
            
            if doctor:
                # Create emergency appointment for next available slot (simplified)
                from datetime import timedelta
                appointment_time = datetime.now() + timedelta(hours=2)
                
                appointment = Appointment(
                    patient_id=patient_id,
                    doctor_id=doctor.id,
                    appointment_date=appointment_time,
                    duration_minutes=30,
                    status=AppointmentStatus.SCHEDULED,
                    reason="Emergency - Auto-booked due to critical alert",
                    notes=f"Auto-booked for alert ID: {alert_id}"
                )
                
                db.add(appointment)
                
                # Update alert with appointment reference
                alert = db.query(Alert).filter(Alert.id == alert_id).first()
                if alert:
                    alert.auto_booked_appointment_id = appointment.id
                
                db.commit()
                logger.info(f"Auto-booked emergency appointment for patient {patient_id}")
        
        except Exception as e:
            logger.error(f"Error auto-booking appointment: {e}")
    
    @staticmethod
    def get_patient_alerts(db: Session, patient_id: int, active_only: bool = True) -> list:
        """Get alerts for a patient"""
        query = db.query(Alert).filter(Alert.patient_id == patient_id)
        
        if active_only:
            query = query.filter(Alert.is_resolved == False)
        
        return query.order_by(Alert.created_at.desc()).all()
    
    @staticmethod
    def resolve_alert(db: Session, alert_id: int) -> Alert:
        """Mark an alert as resolved"""
        try:
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                raise ValueError("Alert not found")
            
            alert.is_resolved = True
            alert.resolved_at = datetime.utcnow()
            
            db.commit()
            db.refresh(alert)
            
            logger.info(f"Resolved alert {alert_id}")
            return alert
        
        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def detect_emergency(symptoms: list, vitals: dict = None) -> dict:
        """
        Detect emergency conditions from symptoms and vitals.
        
        Args:
            symptoms: List of symptoms
            vitals: Vital signs dictionary
        
        Returns:
            Emergency detection result
        """
        from app.agents.emergency_detection_agent import (
            detect_stroke_symptoms,
            detect_heart_attack,
            detect_cardiac_emergency
        )
        
        results = {
            "is_emergency": False,
            "detected_conditions": [],
            "emergency_actions": [],
            "severity": "LOW"
        }
        
        # Check for stroke
        stroke_result = detect_stroke_symptoms(symptoms, vitals or {})
        if stroke_result["is_emergency"]:
            results["is_emergency"] = True
            results["detected_conditions"].append(stroke_result["condition"])
            results["emergency_actions"].extend(stroke_result["emergency_actions"])
            results["severity"] = "CRITICAL"
        
        # Check for heart attack
        heart_attack_result = detect_heart_attack(symptoms, vitals or {})
        if heart_attack_result["is_emergency"]:
            results["is_emergency"] = True
            results["detected_conditions"].append(heart_attack_result["condition"])
            results["emergency_actions"].extend(heart_attack_result["emergency_actions"])
            results["severity"] = "CRITICAL"
        
        # Check cardiac emergency
        if vitals:
            cardiac_result = detect_cardiac_emergency(vitals)
            if cardiac_result["is_emergency"]:
                results["is_emergency"] = True
                results["detected_conditions"].append(cardiac_result["condition"])
                results["emergency_actions"].extend(cardiac_result["emergency_actions"])
                results["severity"] = "CRITICAL"
        
        return results


# Create singleton instance
alert_service = AlertService()
