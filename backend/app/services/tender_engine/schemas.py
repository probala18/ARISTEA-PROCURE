"""
Pydantic schemas for Module 11: Tender Document Engine.
Defines data structures for document parsing, clause detection, requirements, and standard extraction.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class TenderProcessingStatus(str, Enum):
    """Lifecycle status of tender document processing."""
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SectionType(str, Enum):
    """Categorized section types in tender specifications."""
    TECHNICAL_SPEC = "TECHNICAL_SPEC"
    ELIGIBILITY = "ELIGIBILITY"
    BOQ = "BOQ"
    GENERAL_TERMS = "GENERAL_TERMS"
    TESTING_AND_COMPLIANCE = "TESTING_AND_COMPLIANCE"
    SCOPE_OF_WORK = "SCOPE_OF_WORK"
    OTHER = "OTHER"


class ExtractedClause(BaseModel):
    """A detected clause or requirement within a section."""
    clause_number: Optional[str] = Field(None, description="Clause identifier, e.g. '3.1', 'Clause 4.2'")
    page_number: Optional[int] = Field(None, description="Page number where the clause appears (1-indexed)")
    text: str = Field(..., description="Full text of the detected clause")
    extracted_intent: Optional[str] = Field(None, description="Detected intent or topic of requirement")
    product_keywords: List[str] = Field(default_factory=list, description="Extracted product keywords")
    technical_attributes: Dict[str, Any] = Field(default_factory=dict, description="Extracted specs/parameters")
    is_mandatory: bool = Field(True, description="Whether the clause indicates a mandatory requirement")


class ExtractedStandardReference(BaseModel):
    """An explicit standard reference identified within tender text."""
    standard_number_raw: str = Field(..., description="Raw standard citation as matched in text, e.g. 'IS 12615:2018'")
    canonical_identifier: str = Field(..., description="Normalized canonical standard number, e.g. 'IS 12615:2018'")
    detected_standard_id: Optional[int] = Field(None, description="Foreign key ID in standards table if resolved")
    title: Optional[str] = Field(None, description="Title of standard if resolved from database")
    is_valid: bool = Field(True, description="Whether this reference exists in the BIS standards registry")
    is_superseded: bool = Field(False, description="Whether the cited standard is superseded in Module 4 graph")
    superseded_by_standard_id: Optional[int] = Field(None, description="Successor standard ID if superseded")
    superseded_by_identifier: Optional[str] = Field(None, description="Successor canonical number if superseded")
    page_number: Optional[int] = Field(None, description="Page number where standard citation occurs")
    clause_number: Optional[str] = Field(None, description="Clause where standard citation occurs")
    detected_clause: Optional[str] = Field(None, description="Snippet or clause text mentioning the standard")


class ExtractedSection(BaseModel):
    """A detected section/chapter in the tender document."""
    section_number: Optional[str] = Field(None, description="Section identifier, e.g. 'Section 3'")
    section_title: Optional[str] = Field(None, description="Title of the section")
    page_number: Optional[int] = Field(None, description="Starting page number")
    section_type: SectionType = Field(SectionType.OTHER, description="Classified section type")
    content: str = Field(..., description="Full text content of the section")
    clauses: List[ExtractedClause] = Field(default_factory=list, description="Clauses within this section")
    standard_references: List[ExtractedStandardReference] = Field(
        default_factory=list, 
        description="Standards referenced within this section"
    )


class TenderUploadResponse(BaseModel):
    """Response returned upon tender document upload and initial parsing."""
    tender_id: int = Field(..., description="Unique database ID of the tender document")
    tender_number: Optional[str] = Field(None, description="Tender or reference number")
    filename: str = Field(..., description="Uploaded filename")
    file_type: str = Field(..., description="File format: PDF, DOCX, or TXT")
    file_size: int = Field(..., description="File size in bytes")
    status: TenderProcessingStatus = Field(..., description="Current processing status")
    total_pages: int = Field(0, description="Total number of pages parsed")
    total_sections: int = Field(0, description="Total number of sections identified")
    total_clauses: int = Field(0, description="Total number of clauses identified")
    total_standards_detected: int = Field(0, description="Total explicit standard references detected")
    extracted_text: Optional[str] = Field(None, description="Clean extracted plain text from document parser")
    created_at: Optional[datetime] = None


class TenderDetailResponse(BaseModel):
    """Comprehensive details of a parsed tender document."""
    id: int
    tender_number: Optional[str] = None
    filename: str
    title: Optional[str] = None
    organization: Optional[str] = None
    file_type: str
    file_size: Optional[int] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    total_sections: int = 0
    total_requirements: int = 0
    total_standard_references: int = 0
    sections: List[Dict[str, Any]] = Field(default_factory=list)


class TenderStatusResponse(BaseModel):
    """Status polling response for tender document processing."""
    tender_id: int
    filename: str
    status: TenderProcessingStatus
    progress_percentage: int = 100
    message: str = "Processing complete"
    updated_at: Optional[datetime] = None


class TenderRequirementsResponse(BaseModel):
    """Extracted technical requirements response."""
    tender_id: int
    total_requirements: int
    requirements: List[Dict[str, Any]] = Field(default_factory=list)


class TenderReferencesResponse(BaseModel):
    """Explicit standard references response."""
    tender_id: int
    total_references: int
    references: List[ExtractedStandardReference] = Field(default_factory=list)
