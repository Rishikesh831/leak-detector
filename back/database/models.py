"""
Database models for the Leak Detector application
Using SQLAlchemy ORM for PostgreSQL
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, DECIMAL, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class Upload(Base):
    """Stores metadata about uploaded CSV files"""
    __tablename__ = "uploads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    rows_count = Column(Integer, nullable=False)
    columns_count = Column(Integer, nullable=False)
    file_path = Column(Text, nullable=False)
    status = Column(String(50), default="uploaded")  # uploaded, processing, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    anomalies = relationship("Anomaly", back_populates="upload", cascade="all, delete-orphan")
    processing_jobs = relationship("ProcessingJob", back_populates="upload", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Upload(id={self.id}, filename='{self.filename}', status='{self.status}')>"


class Anomaly(Base):
    """Stores detected anomalies from ML processing"""
    __tablename__ = "anomalies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_id = Column(UUID(as_uuid=True), ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False)
    row_index = Column(Integer, nullable=False)  # Original row in CSV
    anomaly_score = Column(DECIMAL(10, 8), nullable=False)  # 0.0 to 1.0
    severity = Column(String(20), default="medium")  # high, medium, low
    status = Column(String(50), default="unreviewed")  # unreviewed, reviewed, actioned
    timestamp = Column(DateTime(timezone=True))
    feature_values = Column(JSONB)  # Store all feature values as JSON
    shap_values = Column(JSONB)  # Cached SHAP explanations
    model_prediction = Column(String(50))  # Classification result
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    upload = relationship("Upload", back_populates="anomalies")
    actions = relationship("Action", back_populates="anomaly", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Anomaly(id={self.id}, score={self.anomaly_score}, severity='{self.severity}')>"

    @property
    def severity_level(self):
        """Calculate severity based on anomaly score"""
        if float(self.anomaly_score) >= 0.8:
            return "high"
        elif float(self.anomaly_score) >= 0.5:
            return "medium"
        else:
            return "low"


class Action(Base):
    """Stores user actions taken on anomalies"""
    __tablename__ = "actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    anomaly_id = Column(UUID(as_uuid=True), ForeignKey("anomalies.id", ondelete="CASCADE"), nullable=False)
    action_type = Column(String(50), nullable=False)  # mark_reviewed, create_work_order, export
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(255))  # Optional: user identifier

    # Relationships
    anomaly = relationship("Anomaly", back_populates="actions")

    def __repr__(self):
        return f"<Action(id={self.id}, type='{self.action_type}')>"


class ProcessingJob(Base):
    """Tracks ML processing job status"""
    __tablename__ = "processing_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_id = Column(UUID(as_uuid=True), ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="queued")  # queued, processing, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    anomalies_found = Column(Integer, default=0)
    processing_time = Column(DECIMAL(10, 2))  # seconds
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    upload = relationship("Upload", back_populates="processing_jobs")

    def __repr__(self):
        return f"<ProcessingJob(id={self.id}, status='{self.status}', progress={self.progress}%)>"


# Indexes are defined in the schema.sql file
# But can also be defined here using Index objects for reference
__table_args__ = (
    Index('idx_anomalies_upload_id', Anomaly.upload_id),
    Index('idx_anomalies_severity', Anomaly.severity),
    Index('idx_anomalies_status', Anomaly.status),
)
