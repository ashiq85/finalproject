from sqlalchemy.orm import Session
from app.db.models import HealthReport, Patient, MedicalRecord
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class ReportService:
    """Service for generating health reports and analytics"""
    
    @staticmethod
    def generate_health_summary(db: Session, patient_id: int) -> dict:
        """
        Generate a comprehensive health summary for a patient.
        
        Args:
            db: Database session
            patient_id: Patient ID
        
        Returns:
            Health summary report data
        """
        try:
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                raise ValueError("Patient not found")
            
            # Get recent medical records
            recent_records = db.query(MedicalRecord).filter(
                MedicalRecord.patient_id == patient_id
            ).order_by(MedicalRecord.visit_date.desc()).limit(10).all()
            
            # Compile health summary
            summary = {
                "patient_info": {
                    "patient_id": patient.id,
                    "name": patient.user.full_name if patient.user else "Unknown",
                    "date_of_birth": str(patient.date_of_birth) if patient.date_of_birth else None,
                    "age": ReportService._calculate_age(patient.date_of_birth) if patient.date_of_birth else None,
                    "gender": patient.gender,
                    "blood_type": patient.blood_type
                },
                "medical_history": {
                    "conditions": patient.medical_history or [],
                    "allergies": patient.allergies or [],
                    "current_medications": patient.current_medications or []
                },
                "recent_visits": [
                    {
                        "date": str(record.visit_date),
                        "chief_complaint": record.chief_complaint,
                        "diagnosis": record.diagnosis,
                        "treatment": record.treatment_plan
                    }
                    for record in recent_records
                ],
                "vital_trends": ReportService._analyze_vital_trends(recent_records),
                "health_metrics": ReportService._calculate_health_metrics(patient, recent_records),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return summary
        
        except Exception as e:
            logger.error(f"Error generating health summary: {e}")
            raise
    
    @staticmethod
    def create_health_report(db: Session, patient_id: int, report_type: str = "summary") -> HealthReport:
        """
        Create and save a health report.
        
        Args:
            db: Database session
            patient_id: Patient ID
            report_type: Type of report
        
        Returns:
            Created health report
        """
        try:
            # Generate report data
            report_data = ReportService.generate_health_summary(db, patient_id)
            
            # Create health report record
            health_report = HealthReport(
                patient_id=patient_id,
                report_type=report_type,
                report_data=report_data
            )
            
            db.add(health_report)
            db.commit()
            db.refresh(health_report)
            
            # TODO: Generate PDF version
            # pdf_path = ReportService._generate_pdf(health_report)
            # health_report.pdf_path = pdf_path
            # db.commit()
            
            logger.info(f"Created {report_type} health report for patient {patient_id}")
            return health_report
        
        except Exception as e:
            logger.error(f"Error creating health report: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def _calculate_age(date_of_birth: datetime) -> int:
        """Calculate age from date of birth"""
        today = datetime.now()
        age = today.year - date_of_birth.year
        if today.month < date_of_birth.month or (today.month == date_of_birth.month and today.day < date_of_birth.day):
            age -= 1
        return age
    
    @staticmethod
    def _analyze_vital_trends(medical_records: list) -> dict:
        """Analyze trends in vital signs"""
        trends = {
            "blood_pressure": [],
            "heart_rate": [],
            "temperature": [],
            "note": "Vital trends analysis"
        }
        
        for record in medical_records:
            if record.vitals:
                vitals = record.vitals
                if "blood_pressure" in vitals:
                    trends["blood_pressure"].append({
                        "date": str(record.visit_date),
                        "value": vitals["blood_pressure"]
                    })
                if "heart_rate" in vitals:
                    trends["heart_rate"].append({
                        "date": str(record.visit_date),
                        "value": vitals["heart_rate"]
                    })
                if "temperature" in vitals:
                    trends["temperature"].append({
                        "date": str(record.visit_date),
                        "value": vitals["temperature"]
                    })
        
        return trends
    
    @staticmethod
    def _calculate_health_metrics(patient: Patient, medical_records: list) -> dict:
        """Calculate health metrics and risk scores"""
        metrics = {
            "total_visits": len(medical_records),
            "chronic_conditions": len(patient.medical_history or []),
            "active_medications": len(patient.current_medications or []),
            "allergy_count": len(patient.allergies or []),
            "risk_assessment": "Low"  # TODO: Implement AI-powered risk assessment
        }
        
        # Simple risk assessment based on conditions
        if metrics["chronic_conditions"] > 3:
            metrics["risk_assessment"] = "High"
        elif metrics["chronic_conditions"] > 1:
            metrics["risk_assessment"] = "Medium"
        
        return metrics
    
    @staticmethod
    def _generate_pdf(health_report: HealthReport) -> str:
        """
        Generate PDF version of health report.
        
        TODO: Implement PDF generation using ReportLab or WeasyPrint
        """
        logger.warning("PDF generation not yet implemented")
        return None


# Create singleton instance
report_service = ReportService()
