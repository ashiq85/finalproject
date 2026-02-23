from sqlalchemy.orm import Session
from app.db.models import Document, Patient
from app.services.vector_service import vector_service
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for managing medical documents and extracting information"""
    
    @staticmethod
    def process_document(db: Session, document_id: int) -> dict:
        """
        Process a document and extract information.
        
        Args:
            db: Database session
            document_id: Document ID
        
        Returns:
            Extracted information
        """
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise ValueError("Document not found")
            
            logger.info(f"Processing document {document_id}: {document.filename}")
            
            # Read file content
            if not os.path.exists(document.file_path):
                raise FileNotFoundError(f"Document file not found: {document.file_path}")
            
            # Extract text based on file type
            extracted_text = DocumentService._extract_text(document.file_path, document.file_type)
            
            # Extract structured data
            extracted_data = DocumentService._extract_medical_data(extracted_text, document.document_type)
            
            # Update document with extracted data
            document.extracted_data = extracted_data
            db.commit()
            
            # Add to vector database for similarity search
            if extracted_text:
                vector_service.add_document_embedding(
                    document_id=str(document_id),
                    content=extracted_text,
                    metadata={
                        "patient_id": document.patient_id,
                        "document_type": document.document_type,
                        "filename": document.filename
                    }
                )
            
            logger.info(f"Successfully processed document {document_id}")
            return extracted_data
        
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            raise
    
    @staticmethod
    def _extract_text(file_path: str, file_type: str) -> str:
        """
        Extract text from document file.
        
        Args:
            file_path: Path to file
            file_type: MIME type
        
        Returns:
            Extracted text
        """
        try:
            # For text files
            if "text" in file_type:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            # For PDF files
            elif "pdf" in file_type:
                # TODO: Implement PDF text extraction using PyPDF2 or pdfplumber
                logger.warning("PDF extraction not yet implemented")
                return "PDF text extraction pending"
            
            # For images (OCR)
            elif "image" in file_type:
                # TODO: Implement OCR using pytesseract
                logger.warning("Image OCR not yet implemented")
                return "Image OCR pending"
            
            else:
                logger.warning(f"Unsupported file type: {file_type}")
                return ""
        
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""
    
    @staticmethod
    def _extract_medical_data(text: str, document_type: str) -> dict:
        """
        Extract structured medical data from text.
        
        Args:
            text: Document text
            document_type: Type of document
        
        Returns:
            Extracted structured data
        """
        # TODO: Implement AI-powered extraction using Ollama
        # For now, return basic structure
        
        extracted = {
            "document_type": document_type,
            "raw_text": text[:500] if text else "",  # First 500 chars
            "extraction_status": "pending_ai_integration"
        }
        
        # Basic keyword extraction for lab reports
        if document_type == "lab_report":
            extracted["potential_values"] = DocumentService._extract_lab_values(text)
        
        return extracted
    
    @staticmethod
    def _extract_lab_values(text: str) -> dict:
        """Extract lab values from text (basic implementation)"""
        # TODO: Implement proper lab value extraction
        return {
            "note": "Lab value extraction requires AI integration",
            "raw_text_sample": text[:200] if text else ""
        }
    
    @staticmethod
    def search_patient_documents(db: Session, patient_id: int, query: str, limit: int = 5) -> list:
        """
        Search patient documents using vector similarity.
        
        Args:
            db: Database session
            patient_id: Patient ID
            query: Search query
            limit: Maximum results
        
        Returns:
            List of relevant documents
        """
        try:
            # Search in vector database
            similar_docs = vector_service.search_documents(query, n_results=limit)
            
            # Filter by patient and get full document info
            results = []
            for doc in similar_docs:
                doc_id = int(doc["document_id"])
                document = db.query(Document).filter(
                    Document.id == doc_id,
                    Document.patient_id == patient_id
                ).first()
                
                if document:
                    results.append({
                        "document_id": document.id,
                        "filename": document.filename,
                        "document_type": document.document_type,
                        "similarity_score": doc["similarity_score"],
                        "extracted_data": document.extracted_data
                    })
            
            return results
        
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []


# Create singleton instance
document_service = DocumentService()
