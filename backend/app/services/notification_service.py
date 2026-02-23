import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from app.db.models import Notification, User, Appointment
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications and email delivery"""
    
    @staticmethod
    def create_notification(
        db: Session,
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        appointment_id: int = None
    ) -> Notification:
        """
        Create a notification for a user.
        
        Args:
            db: Database session
            user_id: User ID
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            appointment_id: Optional appointment ID
        
        Returns:
            Created notification
        """
        try:
            notification = Notification(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                appointment_id=appointment_id
            )
            
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            logger.info(f"Created {notification_type} notification for user {user_id}")
            return notification
        
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def get_user_notifications(db: Session, user_id: int, unread_only: bool = False) -> list:
        """Get notifications for a user"""
        query = db.query(Notification).filter(Notification.user_id == user_id)
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        return query.order_by(Notification.created_at.desc()).all()
    
    @staticmethod
    def mark_as_read(db: Session, notification_id: int) -> Notification:
        """Mark a notification as read"""
        try:
            notification = db.query(Notification).filter(Notification.id == notification_id).first()
            if not notification:
                raise ValueError("Notification not found")
            
            notification.is_read = True
            db.commit()
            db.refresh(notification)
            
            return notification
        
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def send_appointment_reminder(db: Session, appointment_id: int):
        """Send appointment reminder notification"""
        try:
            appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
            if not appointment:
                return
            
            patient = appointment.patient
            if not patient or not patient.user:
                return
            
            # Create notification
            NotificationService.create_notification(
                db=db,
                user_id=patient.user.id,
                notification_type="appointment_reminder",
                title="Appointment Reminder",
                message=f"You have an appointment on {appointment.appointment_date.strftime('%Y-%m-%d %H:%M')}",
                appointment_id=appointment_id
            )
            
            # Send email
            send_email_notification(
                to_email=patient.user.email,
                subject="Appointment Reminder - AgentHealth",
                body=f"Dear {patient.user.full_name},\n\n"
                     f"This is a reminder of your upcoming appointment:\n"
                     f"Date: {appointment.appointment_date.strftime('%Y-%m-%d %H:%M')}\n"
                     f"Reason: {appointment.reason or 'General checkup'}\n\n"
                     f"Please arrive 10 minutes early.\n\n"
                     f"Best regards,\nAgentHealth Team"
            )
            
            logger.info(f"Sent appointment reminder for appointment {appointment_id}")
        
        except Exception as e:
            logger.error(f"Error sending appointment reminder: {e}")


def send_email_notification(to_email: str, subject: str, body: str) -> bool:
    """
    Send email notification (placeholder implementation).
    
    In production, this should use a proper email service like SendGrid, AWS SES, etc.
    For now, this just logs the email.
    
    Args:
        to_email: Recipient email
        subject: Email subject
        body: Email body
    
    Returns:
        Success status
    """
    try:
        logger.info(f"EMAIL NOTIFICATION:")
        logger.info(f"To: {to_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Body: {body}")
        logger.info("=" * 50)
        
        # TODO: Implement actual email sending
        # Example with SMTP:
        # msg = MIMEMultipart()
        # msg['From'] = "noreply@agenthealth.com"
        # msg['To'] = to_email
        # msg['Subject'] = subject
        # msg.attach(MIMEText(body, 'plain'))
        # 
        # server = smtplib.SMTP('smtp.gmail.com', 587)
        # server.starttls()
        # server.login("your-email@gmail.com", "your-password")
        # server.send_message(msg)
        # server.quit()
        
        return True
    
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False


# Create singleton instance
notification_service = NotificationService()
