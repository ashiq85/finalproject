try:
    from crewai.tools import tool
except ImportError:
    # Fallback: plain decorator when crewai is not installed
    def tool(name=None):
        def decorator(func):
            return func
        if callable(name):
            return name
        return decorator

from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.db.models import Patient, User, MedicalRecord, Appointment, Alert, HealthMetric
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


@tool("Query Patient Database")
def query_patient_db(patient_id: int) -> Dict:
    """
    Query patient information from the database.
    Returns patient demographics, medical history, and current medications.
    """
    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return {"error": "Patient not found"}
        
        return {
            "patient_id": patient.id,
            "date_of_birth": str(patient.date_of_birth) if patient.date_of_birth else None,
            "gender": patient.gender,
            "blood_type": patient.blood_type,
            "medical_history": patient.medical_history or [],
            "allergies": patient.allergies or [],
            "current_medications": patient.current_medications or []
        }
    except Exception as e:
        logger.error(f"Error querying patient database: {e}")
        return {"error": str(e)}
    finally:
        db.close()


@tool("Query Medical Records")
def query_medical_records(patient_id: int, limit: int = 10) -> List[Dict]:
    """
    Query patient's medical records from the database.
    Returns recent medical visits, diagnoses, and treatments.
    """
    db = SessionLocal()
    try:
        records = db.query(MedicalRecord).filter(
            MedicalRecord.patient_id == patient_id
        ).order_by(MedicalRecord.visit_date.desc()).limit(limit).all()
        
        return [
            {
                "visit_date": str(record.visit_date),
                "chief_complaint": record.chief_complaint,
                "symptoms": record.symptoms or [],
                "vitals": record.vitals or {},
                "diagnosis": record.diagnosis,
                "treatment_plan": record.treatment_plan,
                "prescriptions": record.prescriptions or []
            }
            for record in records
        ]
    except Exception as e:
        logger.error(f"Error querying medical records: {e}")
        return []
    finally:
        db.close()


@tool("Check Doctor Availability")
def check_doctor_availability(doctor_id: int, date: str) -> Dict:
    """
    Check doctor's availability for appointments on a specific date.
    Returns available time slots.
    """
    db = SessionLocal()
    try:
        # Get doctor's appointments for the date
        from datetime import datetime, timedelta
        target_date = datetime.fromisoformat(date).date()
        
        appointments = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date >= target_date,
            Appointment.appointment_date < target_date + timedelta(days=1)
        ).all()
        
        # Generate available slots (9 AM to 5 PM, 30-minute slots)
        all_slots = []
        start_hour = 9
        end_hour = 17
        
        for hour in range(start_hour, end_hour):
            for minute in [0, 30]:
                slot_time = datetime.combine(target_date, datetime.min.time()).replace(hour=hour, minute=minute)
                all_slots.append(slot_time)
        
        # Remove booked slots
        booked_times = [apt.appointment_date for apt in appointments]
        available_slots = [slot for slot in all_slots if slot not in booked_times]
        
        return {
            "doctor_id": doctor_id,
            "date": date,
            "available_slots": [str(slot) for slot in available_slots],
            "total_available": len(available_slots)
        }
    except Exception as e:
        logger.error(f"Error checking doctor availability: {e}")
        return {"error": str(e)}
    finally:
        db.close()


@tool("Create Alert")
def create_alert_tool(patient_id: int, severity: str, title: str, description: str, actions: List[str]) -> Dict:
    """
    Create a health alert for a patient.
    Severity levels: LOW, MEDIUM, HIGH, CRITICAL
    """
    db = SessionLocal()
    try:
        from app.db.models import AlertSeverity
        
        alert = Alert(
            patient_id=patient_id,
            severity=AlertSeverity[severity.upper()],
            title=title,
            description=description,
            recommended_actions=actions
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        return {
            "alert_id": alert.id,
            "patient_id": patient_id,
            "severity": severity,
            "title": title,
            "created": True
        }
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        return {"error": str(e), "created": False}
    finally:
        db.close()


@tool("Search Similar Cases")
def search_similar_cases(symptoms: List[str], diagnosis: str = None) -> List[Dict]:
    """
    Search for similar medical cases based on symptoms and diagnosis.
    This will integrate with ChromaDB vector search in the future.
    """
    # TODO: Integrate with ChromaDB vector service
    # For now, return placeholder
    return [
        {
            "case_id": "placeholder",
            "similarity_score": 0.0,
            "symptoms": symptoms,
            "diagnosis": "Pending vector search integration",
            "treatment": "Integration with ChromaDB pending"
        }
    ]


@tool("Emergency Detection")
def emergency_detection_tool(symptoms: List[str], vitals: Dict = None) -> Dict:
    """
    Detect emergency health conditions from symptoms and vital signs.
    Returns emergency status and recommended actions.
    """
    from app.agents.emergency_detection_agent import (
        detect_stroke_symptoms,
        detect_heart_attack,
        detect_cardiac_emergency
    )
    
    results = {
        "is_emergency": False,
        "detected_conditions": [],
        "emergency_actions": []
    }
    
    # Check for stroke
    stroke_result = detect_stroke_symptoms(symptoms, vitals or {})
    if stroke_result["is_emergency"]:
        results["is_emergency"] = True
        results["detected_conditions"].append(stroke_result["condition"])
        results["emergency_actions"].extend(stroke_result["emergency_actions"])
    
    # Check for heart attack
    heart_attack_result = detect_heart_attack(symptoms, vitals or {})
    if heart_attack_result["is_emergency"]:
        results["is_emergency"] = True
        results["detected_conditions"].append(heart_attack_result["condition"])
        results["emergency_actions"].extend(heart_attack_result["emergency_actions"])
    
    # Check cardiac emergency
    if vitals:
        cardiac_result = detect_cardiac_emergency(vitals)
        if cardiac_result["is_emergency"]:
            results["is_emergency"] = True
            results["detected_conditions"].append(cardiac_result["condition"])
            results["emergency_actions"].extend(cardiac_result["emergency_actions"])
    
@tool("Query Health Metrics")
def query_health_metrics(patient_id: int, limit: int = 10) -> List[Dict]:
    """
    Query patient's daily health metrics (sugar, pressure, cholesterol, etc.) from the database.
    Returns recent health measurements and vitals.
    """
    db = SessionLocal()
    try:
        metrics = db.query(HealthMetric).filter(
            HealthMetric.patient_id == patient_id
        ).order_by(HealthMetric.recorded_at.desc()).limit(limit).all()
        
        return [
            {
                "recorded_at": str(metric.recorded_at),
                "metric_name": metric.metric_name,
                "value": metric.value,
                "unit": metric.unit,
                "notes": metric.notes
            }
            for metric in metrics
        ]
    except Exception as e:
        logger.error(f"Error querying health metrics: {e}")
        return []
    finally:
        db.close()
