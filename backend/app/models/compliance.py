from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class CertificationRecord(Base):
    """Certification facts from certification.csv, ReportExcel.csv, schem.csv, standards.csv."""
    __tablename__ = "certification_records"

    id = Column(Integer, primary_key=True, index=True)
    standard_id = Column(Integer, ForeignKey("standards.id", ondelete="SET NULL"), index=True, nullable=True)
    standard_number = Column(String(100), index=True, nullable=False)
    product_name = Column(Text, index=True, nullable=True)
    product_rating = Column(Text, nullable=True)
    certification_type = Column(String(100), index=True, nullable=True)  # BIS_ISI, CRS, Hallmarking, Scheme-I, etc.
    certification_status = Column(String(100), nullable=True)
    is_mandatory = Column(Boolean, index=True, nullable=True)
    requirement_level = Column(String(50), default="UNKNOWN", index=True, nullable=False)  # MANDATORY, VOLUNTARY, CONDITIONAL, UNKNOWN
    source_dataset = Column(String(100), nullable=False)
    source_provenance = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    standard = relationship("Standard", foreign_keys=[standard_id])


class QCORecord(Base):
    """Quality Control Order facts from schem.csv and standards.csv."""
    __tablename__ = "qco_records"

    id = Column(Integer, primary_key=True, index=True)
    standard_id = Column(Integer, ForeignKey("standards.id", ondelete="SET NULL"), index=True, nullable=True)
    standard_number = Column(String(100), index=True, nullable=False)
    product_name = Column(Text, index=True, nullable=True)
    qco_id = Column(String(100), index=True, nullable=True)
    qco_title = Column(Text, nullable=True)
    notification_number = Column(String(255), index=True, nullable=True)
    notification_date = Column(String(100), nullable=True)
    notification_links = Column(Text, nullable=True)
    ministry_department = Column(String(255), index=True, nullable=True)
    status = Column(String(100), nullable=True)
    is_mandatory = Column(Boolean, default=True, index=True, nullable=False)
    source_dataset = Column(String(100), nullable=False)
    source_provenance = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    standard = relationship("Standard", foreign_keys=[standard_id])


class ProductLicence(Base):
    """Factual licence count per product category from productlicence.csv."""
    __tablename__ = "product_licences"

    id = Column(Integer, primary_key=True, index=True)
    product_category = Column(String(255), unique=True, index=True, nullable=False)
    licence_count = Column(Integer, nullable=False, default=0)
    raw_count_str = Column(String(100), nullable=True)
    source_dataset = Column(String(100), nullable=False, default="productlicence.csv")
    source_provenance = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
