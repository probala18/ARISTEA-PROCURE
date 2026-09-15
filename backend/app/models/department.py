from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Department(Base):
    """Department / technical committee context."""
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, index=True, nullable=False)  # e.g., 'ETD 09', 'CED 2'
    name = Column(String(255), nullable=False)  # e.g., 'Cables & Conductors'
    ministry = Column(String(255), index=True, nullable=True)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class MinistryProductMapping(Base):
    """Ministry / Department -> Product -> Indian Standard mapping from upcomming.csv."""
    __tablename__ = "ministry_product_mappings"

    id = Column(Integer, primary_key=True, index=True)
    ministry_department = Column(String(255), index=True, nullable=False)
    product_name = Column(Text, index=True, nullable=False)
    standard_number = Column(String(100), index=True, nullable=False)
    standard_id = Column(Integer, ForeignKey("standards.id", ondelete="SET NULL"), index=True, nullable=True)
    source_dataset = Column(String(100), nullable=False, default="upcomming.csv")
    source_provenance = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
