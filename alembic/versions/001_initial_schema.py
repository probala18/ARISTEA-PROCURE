"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-15 22:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension if on PostgreSQL
    conn = op.get_bind()
    if conn and conn.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 1. source_documents
    op.create_table(
        'source_documents',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('document_id', sa.String(length=100), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('standard_number', sa.String(length=100), nullable=True),
        sa.Column('revision', sa.String(length=50), nullable=True),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('local_path', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('downloaded', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('document_id', name='uq_source_doc_document_id')
    )
    op.create_index('ix_source_documents_document_id', 'source_documents', ['document_id'])
    op.create_index('ix_source_documents_standard_number', 'source_documents', ['standard_number'])

    # 2. departments
    op.create_table(
        'departments',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('ministry', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('code', name='uq_departments_code')
    )
    op.create_index('ix_departments_code', 'departments', ['code'])
    op.create_index('ix_departments_ministry', 'departments', ['ministry'])

    # 3. standards
    # Note: embedding uses Vector(384) on PostgreSQL, Text/JSON on other dialects
    embedding_col = sa.Column('embedding', Vector(384), nullable=True) if conn and conn.dialect.name == "postgresql" else sa.Column('embedding', sa.JSON(), nullable=True)

    op.create_table(
        'standards',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('standard_id', sa.String(length=100), nullable=False),
        sa.Column('is_number', sa.String(length=100), nullable=False),
        sa.Column('part', sa.String(length=50), nullable=True),
        sa.Column('section', sa.String(length=50), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('scope', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('subject_area', sa.String(length=100), nullable=True),
        sa.Column('division', sa.String(length=100), nullable=True),
        sa.Column('department_id', sa.Integer(), sa.ForeignKey('departments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('technical_committee', sa.String(length=100), nullable=True),
        sa.Column('publication_year', sa.Integer(), nullable=True),
        sa.Column('latest_year', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='CURRENT'),
        sa.Column('supersedes', sa.String(length=255), nullable=True),
        sa.Column('certification_scheme', sa.String(length=255), nullable=True),
        sa.Column('is_mandatory_certification', sa.Boolean(), nullable=True),
        sa.Column('qco_applicable', sa.Boolean(), nullable=True),
        sa.Column('qco_reference', sa.Text(), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('source_document_id', sa.Integer(), sa.ForeignKey('source_documents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('source_file', sa.String(length=100), nullable=False),
        sa.Column('source_provenance', sa.JSON(), nullable=True),
        embedding_col,
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('standard_id', name='uq_standards_standard_id')
    )
    op.create_index('ix_standards_standard_id', 'standards', ['standard_id'])
    op.create_index('ix_standards_is_number', 'standards', ['is_number'])
    op.create_index('ix_standards_category', 'standards', ['category'])
    op.create_index('ix_standards_status', 'standards', ['status'])
    op.create_index('ix_standards_publication_year', 'standards', ['publication_year'])
    op.create_index('ix_standards_department_id', 'standards', ['department_id'])

    # 4. standard_relationships
    op.create_table(
        'standard_relationships',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('source_standard_id', sa.Integer(), sa.ForeignKey('standards.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_standard_id', sa.Integer(), sa.ForeignKey('standards.id', ondelete='SET NULL'), nullable=True),
        sa.Column('source_standard_number', sa.String(length=100), nullable=True),
        sa.Column('target_standard_number', sa.String(length=100), nullable=False),
        sa.Column('target_standard_title', sa.Text(), nullable=True),
        sa.Column('relationship_type', sa.String(length=100), nullable=False),
        sa.Column('relationship_category', sa.String(length=100), nullable=True),
        sa.Column('relationship_description', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('is_explicit_source', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('source_dataset', sa.String(length=100), nullable=False),
        sa.Column('source_provenance', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('source_standard_id', 'target_standard_number', 'relationship_type', 'is_explicit_source', name='uq_std_rel_source_target_type_explicit')
    )
    op.create_index('ix_std_rel_source', 'standard_relationships', ['source_standard_id'])
    op.create_index('ix_std_rel_target', 'standard_relationships', ['target_standard_id'])
    op.create_index('ix_std_rel_type', 'standard_relationships', ['relationship_type'])
    op.create_index('ix_std_rel_explicit', 'standard_relationships', ['is_explicit_source'])

    # 5. standard_versions
    op.create_table(
        'standard_versions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('standard_id', sa.Integer(), sa.ForeignKey('standards.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_number', sa.String(length=100), nullable=False),
        sa.Column('version_year', sa.Integer(), nullable=True),
        sa.Column('latest_year', sa.Integer(), nullable=True),
        sa.Column('amendment_number', sa.Integer(), nullable=True),
        sa.Column('amendment_year', sa.Integer(), nullable=True),
        sa.Column('change_description', sa.Text(), nullable=True),
        sa.Column('current_state', sa.String(length=50), nullable=False, server_default='CURRENT'),
        sa.Column('superseded_by', sa.String(length=100), nullable=True),
        sa.Column('superseded_state', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('effective_date', sa.String(length=100), nullable=True),
        sa.Column('source_dataset', sa.String(length=100), nullable=False),
        sa.Column('source_provenance', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('ix_std_versions_standard_id', 'standard_versions', ['standard_id'])
    op.create_index('ix_std_versions_is_number', 'standard_versions', ['is_number'])
    op.create_index('ix_std_versions_state', 'standard_versions', ['current_state'])

    # 6. certification_records
    op.create_table(
        'certification_records',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('standard_id', sa.Integer(), sa.ForeignKey('standards.id', ondelete='SET NULL'), nullable=True),
        sa.Column('standard_number', sa.String(length=100), nullable=False),
        sa.Column('product_name', sa.Text(), nullable=True),
        sa.Column('product_rating', sa.Text(), nullable=True),
        sa.Column('certification_type', sa.String(length=100), nullable=True),
        sa.Column('certification_status', sa.String(length=100), nullable=True),
        sa.Column('is_mandatory', sa.Boolean(), nullable=True),
        sa.Column('requirement_level', sa.String(length=50), nullable=False, server_default='UNKNOWN'),
        sa.Column('source_dataset', sa.String(length=100), nullable=False),
        sa.Column('source_provenance', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('ix_cert_records_standard_id', 'certification_records', ['standard_id'])
    op.create_index('ix_cert_records_std_num', 'certification_records', ['standard_number'])
    op.create_index('ix_cert_records_req_level', 'certification_records', ['requirement_level'])

    # 7. qco_records
    op.create_table(
        'qco_records',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('standard_id', sa.Integer(), sa.ForeignKey('standards.id', ondelete='SET NULL'), nullable=True),
        sa.Column('standard_number', sa.String(length=100), nullable=False),
        sa.Column('product_name', sa.Text(), nullable=True),
        sa.Column('qco_id', sa.String(length=100), nullable=True),
        sa.Column('qco_title', sa.Text(), nullable=True),
        sa.Column('notification_number', sa.String(length=255), nullable=True),
        sa.Column('notification_date', sa.String(length=100), nullable=True),
        sa.Column('notification_links', sa.Text(), nullable=True),
        sa.Column('ministry_department', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=100), nullable=True),
        sa.Column('is_mandatory', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('source_dataset', sa.String(length=100), nullable=False),
        sa.Column('source_provenance', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('ix_qco_records_std_id', 'qco_records', ['standard_id'])
    op.create_index('ix_qco_records_std_num', 'qco_records', ['standard_number'])
    op.create_index('ix_qco_records_qco_id', 'qco_records', ['qco_id'])

    # 8. product_licences
    op.create_table(
        'product_licences',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('product_category', sa.String(length=255), nullable=False),
        sa.Column('licence_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('raw_count_str', sa.String(length=100), nullable=True),
        sa.Column('source_dataset', sa.String(length=100), nullable=False, server_default='productlicence.csv'),
        sa.Column('source_provenance', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('product_category', name='uq_product_licence_category')
    )
    op.create_index('ix_product_licences_category', 'product_licences', ['product_category'])

    # 9. ministry_product_mappings
    op.create_table(
        'ministry_product_mappings',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('ministry_department', sa.String(length=255), nullable=False),
        sa.Column('product_name', sa.Text(), nullable=False),
        sa.Column('standard_number', sa.String(length=100), nullable=False),
        sa.Column('standard_id', sa.Integer(), sa.ForeignKey('standards.id', ondelete='SET NULL'), nullable=True),
        sa.Column('source_dataset', sa.String(length=100), nullable=False, server_default='upcomming.csv'),
        sa.Column('source_provenance', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('ix_ministry_mappings_dept', 'ministry_product_mappings', ['ministry_department'])
    op.create_index('ix_ministry_mappings_std', 'ministry_product_mappings', ['standard_number'])

    # 10. procurement_ontology
    op.create_table(
        'procurement_ontology',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('term', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('domain', sa.String(length=100), nullable=True),
        sa.Column('definition', sa.Text(), nullable=True),
        sa.Column('canonical_name', sa.String(length=255), nullable=True),
        sa.Column('synonyms', sa.JSON(), nullable=True),
        sa.Column('parent_term_id', sa.Integer(), sa.ForeignKey('procurement_ontology.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('term', name='uq_procurement_ontology_term')
    )
    op.create_index('ix_procurement_ontology_term', 'procurement_ontology', ['term'])
    op.create_index('ix_procurement_ontology_canonical', 'procurement_ontology', ['canonical_name'])

    # 11. procurement_aliases
    op.create_table(
        'procurement_aliases',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('alias', sa.String(length=255), nullable=False),
        sa.Column('canonical_standard_number', sa.String(length=100), nullable=False),
        sa.Column('standard_id', sa.Integer(), sa.ForeignKey('standards.id', ondelete='CASCADE'), nullable=True),
        sa.Column('product_context', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('alias', 'canonical_standard_number', name='uq_procurement_alias_std')
    )
    op.create_index('ix_procurement_aliases_alias', 'procurement_aliases', ['alias'])
    op.create_index('ix_procurement_aliases_std', 'procurement_aliases', ['canonical_standard_number'])

    # 12. tender_documents
    op.create_table(
        'tender_documents',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tender_number', sa.String(length=100), nullable=True),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('organization', sa.String(length=255), nullable=True),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('parsed_metadata', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='UPLOADED'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('tender_number', name='uq_tender_number')
    )
    op.create_index('ix_tender_documents_status', 'tender_documents', ['status'])

    # 13. tender_sections
    op.create_table(
        'tender_sections',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tender_id', sa.Integer(), sa.ForeignKey('tender_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('section_title', sa.String(length=255), nullable=True),
        sa.Column('section_number', sa.String(length=50), nullable=True),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('section_type', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('ix_tender_sections_tender_id', 'tender_sections', ['tender_id'])

    # 14. tender_requirements
    op.create_table(
        'tender_requirements',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tender_id', sa.Integer(), sa.ForeignKey('tender_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('section_id', sa.Integer(), sa.ForeignKey('tender_sections.id', ondelete='SET NULL'), nullable=True),
        sa.Column('requirement_text', sa.Text(), nullable=False),
        sa.Column('extracted_intent', sa.String(length=100), nullable=True),
        sa.Column('product_keywords', sa.JSON(), nullable=True),
        sa.Column('technical_attributes', sa.JSON(), nullable=True),
        sa.Column('is_mandatory', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('ix_tender_requirements_tender_id', 'tender_requirements', ['tender_id'])

    # 15. tender_standard_references
    op.create_table(
        'tender_standard_references',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tender_id', sa.Integer(), sa.ForeignKey('tender_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('section_id', sa.Integer(), sa.ForeignKey('tender_sections.id', ondelete='SET NULL'), nullable=True),
        sa.Column('requirement_id', sa.Integer(), sa.ForeignKey('tender_requirements.id', ondelete='SET NULL'), nullable=True),
        sa.Column('standard_number_raw', sa.String(length=100), nullable=False),
        sa.Column('detected_standard_id', sa.Integer(), sa.ForeignKey('standards.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_valid', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_superseded', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('superseded_by_standard_id', sa.Integer(), sa.ForeignKey('standards.id', ondelete='SET NULL'), nullable=True),
        sa.Column('detected_clause', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('ix_tender_std_refs_tender_id', 'tender_standard_references', ['tender_id'])

    # 16. tender_audit_results
    op.create_table(
        'tender_audit_results',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tender_id', sa.Integer(), sa.ForeignKey('tender_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('audit_summary', sa.JSON(), nullable=True),
        sa.Column('expected_standards', sa.JSON(), nullable=True),
        sa.Column('missing_standards', sa.JSON(), nullable=True),
        sa.Column('outdated_standards', sa.JSON(), nullable=True),
        sa.Column('testing_gaps', sa.JSON(), nullable=True),
        sa.Column('safety_gaps', sa.JSON(), nullable=True),
        sa.Column('certification_gaps', sa.JSON(), nullable=True),
        sa.Column('coverage_score', sa.Float(), nullable=True),
        sa.Column('audit_report', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('tender_id', name='uq_tender_audit_tender_id')
    )
    op.create_index('ix_tender_audit_tender_id', 'tender_audit_results', ['tender_id'])

    # 17. analysis_sessions
    op.create_table(
        'analysis_sessions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('session_id', sa.String(length=100), nullable=False),
        sa.Column('session_type', sa.String(length=50), nullable=False),
        sa.Column('user_input', sa.Text(), nullable=False),
        sa.Column('detected_language', sa.String(length=20), nullable=False, server_default='en'),
        sa.Column('intent', sa.String(length=100), nullable=True),
        sa.Column('ambiguity_flag', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('clarification_prompt', sa.Text(), nullable=True),
        sa.Column('conversation_context', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('session_id', name='uq_analysis_session_id')
    )
    op.create_index('ix_analysis_sessions_session_id', 'analysis_sessions', ['session_id'])
    op.create_index('ix_analysis_sessions_type', 'analysis_sessions', ['session_type'])
    op.create_index('ix_analysis_sessions_intent', 'analysis_sessions', ['intent'])

    # 18. analysis_requirements
    op.create_table(
        'analysis_requirements',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('session_id', sa.Integer(), sa.ForeignKey('analysis_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('requirement_type', sa.String(length=100), nullable=False),
        sa.Column('extracted_key', sa.String(length=100), nullable=False),
        sa.Column('extracted_value', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('ix_analysis_reqs_session_id', 'analysis_requirements', ['session_id'])

    # 19. recommendation_results
    op.create_table(
        'recommendation_results',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('session_id', sa.Integer(), sa.ForeignKey('analysis_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('primary_standard_id', sa.Integer(), sa.ForeignKey('standards.id', ondelete='SET NULL'), nullable=True),
        sa.Column('primary_standard_number', sa.String(length=100), nullable=False),
        sa.Column('relevance_score', sa.Float(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('evidence_summary', sa.JSON(), nullable=True),
        sa.Column('matched_requirements', sa.JSON(), nullable=True),
        sa.Column('rank', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('ix_rec_results_session_id', 'recommendation_results', ['session_id'])
    op.create_index('ix_rec_results_std_num', 'recommendation_results', ['primary_standard_number'])

    # 20. generated_specifications
    op.create_table(
        'generated_specifications',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('session_id', sa.Integer(), sa.ForeignKey('analysis_sessions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('tender_id', sa.Integer(), sa.ForeignKey('tender_documents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('standard_id', sa.Integer(), sa.ForeignKey('standards.id', ondelete='SET NULL'), nullable=True),
        sa.Column('spec_type', sa.String(length=100), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('grounding_evidence', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('ix_gen_specs_spec_type', 'generated_specifications', ['spec_type'])

    # 21. evaluation_queries
    op.create_table(
        'evaluation_queries',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('query_id', sa.String(length=50), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('expected_intent', sa.String(length=100), nullable=False),
        sa.Column('clarification_expected', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('expected_retrieval_operations', sa.JSON(), nullable=True),
        sa.Column('expected_evidence', sa.Text(), nullable=True),
        sa.Column('answerable_with_current_data', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('query_id', name='uq_evaluation_query_id')
    )
    op.create_index('ix_eval_queries_query_id', 'evaluation_queries', ['query_id'])
    op.create_index('ix_eval_queries_intent', 'evaluation_queries', ['expected_intent'])

    # 22. evaluation_results
    op.create_table(
        'evaluation_results',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('evaluation_query_id', sa.Integer(), sa.ForeignKey('evaluation_queries.id', ondelete='CASCADE'), nullable=False),
        sa.Column('test_run_id', sa.String(length=100), nullable=False),
        sa.Column('actual_intent', sa.String(length=100), nullable=True),
        sa.Column('actual_retrieved_standards', sa.JSON(), nullable=True),
        sa.Column('precision_at_1', sa.Float(), nullable=True),
        sa.Column('precision_at_3', sa.Float(), nullable=True),
        sa.Column('recall_at_5', sa.Float(), nullable=True),
        sa.Column('mrr', sa.Float(), nullable=True),
        sa.Column('latency_ms', sa.Float(), nullable=True),
        sa.Column('pass_fail', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('ix_eval_results_query_id', 'evaluation_results', ['evaluation_query_id'])
    op.create_index('ix_eval_results_run_id', 'evaluation_results', ['test_run_id'])


def downgrade() -> None:
    op.drop_table('evaluation_results')
    op.drop_table('evaluation_queries')
    op.drop_table('generated_specifications')
    op.drop_table('recommendation_results')
    op.drop_table('analysis_requirements')
    op.drop_table('analysis_sessions')
    op.drop_table('tender_audit_results')
    op.drop_table('tender_standard_references')
    op.drop_table('tender_requirements')
    op.drop_table('tender_sections')
    op.drop_table('tender_documents')
    op.drop_table('procurement_aliases')
    op.drop_table('procurement_ontology')
    op.drop_table('ministry_product_mappings')
    op.drop_table('product_licences')
    op.drop_table('qco_records')
    op.drop_table('certification_records')
    op.drop_table('standard_versions')
    op.drop_table('standard_relationships')
    op.drop_table('standards')
    op.drop_table('departments')
    op.drop_table('source_documents')
