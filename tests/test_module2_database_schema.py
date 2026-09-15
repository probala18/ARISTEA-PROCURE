import unittest
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from backend.app.core.database import Base, PGVectorType
import backend.app.models as models

class TestModule2DatabaseSchema(unittest.TestCase):
    """Module 2 automated validation tests: PostgreSQL schema, pgvector, constraints, and migrations."""

    @classmethod
    def setUpClass(cls):
        """Set up in-memory database for testing schema creation and relationships."""
        cls.test_engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.test_engine)
        cls.Session = sessionmaker(bind=cls.test_engine)

    def test_01_all_22_tables_registered(self):
        """Verify all 22 required tables are declared in Base.metadata."""
        expected_tables = {
            'source_documents',
            'departments',
            'standards',
            'standard_relationships',
            'standard_versions',
            'certification_records',
            'qco_records',
            'product_licences',
            'ministry_product_mappings',
            'procurement_ontology',
            'procurement_aliases',
            'tender_documents',
            'tender_sections',
            'tender_requirements',
            'tender_standard_references',
            'tender_audit_results',
            'analysis_sessions',
            'analysis_requirements',
            'recommendation_results',
            'generated_specifications',
            'evaluation_queries',
            'evaluation_results'
        }
        actual_tables = set(Base.metadata.tables.keys())
        self.assertTrue(expected_tables.issubset(actual_tables), f"Missing tables: {expected_tables - actual_tables}")
        self.assertEqual(len(actual_tables), 22, f"Expected exactly 22 tables, found {len(actual_tables)}")

    def test_02_primary_and_foreign_keys(self):
        """Verify primary and foreign keys across core tables."""
        inspector = inspect(self.test_engine)
        
        # Primary key checks
        for tbl in Base.metadata.tables.keys():
            pk = inspector.get_pk_constraint(tbl)
            self.assertTrue(len(pk['constrained_columns']) > 0, f"Table {tbl} has no primary key")

        # Specific Foreign Key checks
        fk_std_rels = {fk['referred_table'] for fk in inspector.get_foreign_keys('standard_relationships')}
        self.assertIn('standards', fk_std_rels)

        fk_std_vers = {fk['referred_table'] for fk in inspector.get_foreign_keys('standard_versions')}
        self.assertIn('standards', fk_std_vers)

        fk_certs = {fk['referred_table'] for fk in inspector.get_foreign_keys('certification_records')}
        self.assertIn('standards', fk_certs)

        fk_qco = {fk['referred_table'] for fk in inspector.get_foreign_keys('qco_records')}
        self.assertIn('standards', fk_qco)

        fk_tender_reqs = {fk['referred_table'] for fk in inspector.get_foreign_keys('tender_requirements')}
        self.assertIn('tender_documents', fk_tender_reqs)

    def test_03_unique_constraints(self):
        """Verify essential uniqueness constraints."""
        standards_table = Base.metadata.tables['standards']
        self.assertTrue(standards_table.c.standard_id.unique or any(
            'standard_id' in [c.name for c in uq.columns] for uq in standards_table.constraints if hasattr(uq, 'columns')
        ))

        std_rel_table = Base.metadata.tables['standard_relationships']
        uq_rel_cols = set()
        for constr in std_rel_table.constraints:
            if hasattr(constr, 'columns') and len(constr.columns) > 1:
                uq_rel_cols.update([c.name for c in constr.columns])
        self.assertIn('source_standard_id', uq_rel_cols)
        self.assertIn('target_standard_number', uq_rel_cols)
        self.assertIn('relationship_type', uq_rel_cols)
        self.assertIn('is_explicit_source', uq_rel_cols)

    def test_04_explicit_vs_derived_relationship_flag(self):
        """Verify explicit source vs derived relationship separation."""
        std_rel_table = Base.metadata.tables['standard_relationships']
        self.assertIn('is_explicit_source', std_rel_table.c)
        self.assertIn('source_dataset', std_rel_table.c)

    def test_05_provenance_fields_present(self):
        """Verify provenance fields on data-bearing tables."""
        data_tables = ['standards', 'standard_relationships', 'standard_versions', 'certification_records', 'qco_records', 'product_licences']
        for tbl_name in data_tables:
            tbl = Base.metadata.tables[tbl_name]
            self.assertTrue(
                'source_dataset' in tbl.c or 'source_file' in tbl.c,
                f"Table {tbl_name} missing source dataset/file tracking"
            )
            self.assertIn('source_provenance', tbl.c, f"Table {tbl_name} missing source_provenance column")

    def test_06_pgvector_column_definition(self):
        """Verify embedding column uses PGVectorType with dimension 384."""
        standards_table = Base.metadata.tables['standards']
        self.assertIn('embedding', standards_table.c)
        col_type = standards_table.c.embedding.type
        self.assertIsInstance(col_type, PGVectorType)
        self.assertEqual(col_type.dimension, 384)

    def test_07_alembic_migration_file_exists(self):
        """Verify Alembic migration script exists and has revision ID."""
        migration_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'alembic', 'versions', '001_initial_schema.py'
        )
        self.assertTrue(os.path.isfile(migration_path), "Migration 001_initial_schema.py missing")
        with open(migration_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("revision: str = '001_initial_schema'", content)
            self.assertIn("CREATE EXTENSION IF NOT EXISTS vector;", content)

    def test_08_crud_and_cascade_operations(self):
        """Verify basic CRUD and relationship integrity."""
        session = self.Session()
        try:
            # Create a source document
            doc = models.SourceDocument(
                document_id="DOC-001",
                filename="standards.csv",
                source_type="CSV_DATASET",
                downloaded=True,
                title="Primary Standards CSV"
            )
            session.add(doc)
            session.flush()

            # Create standard
            std = models.Standard(
                standard_id="IS 694:2010",
                is_number="IS 694",
                title="PVC Insulated Cables For Working Voltages Up To 1100 V",
                category="Electrical",
                status="CURRENT",
                publication_year=2010,
                source_file="standards.csv",
                source_document_id=doc.id,
                source_provenance={"row_index": 1, "source": "standards.csv"}
            )
            session.add(std)
            session.flush()

            # Create explicit relationship
            rel_explicit = models.StandardRelationship(
                source_standard_id=std.id,
                target_standard_number="IS 1554",
                target_standard_title="PVC insulated heavy duty cables",
                relationship_type="ALLIED",
                is_explicit_source=True,
                source_dataset="relationships.json"
            )
            session.add(rel_explicit)

            # Create derived relationship
            rel_derived = models.StandardRelationship(
                source_standard_id=std.id,
                target_standard_number="IS 1554",
                target_standard_title="PVC insulated heavy duty cables",
                relationship_type="ALLIED",
                is_explicit_source=False,
                source_dataset="standards.csv"
            )
            session.add(rel_derived)
            session.commit()

            # Verify both exist because is_explicit_source is distinct
            rels = session.query(models.StandardRelationship).filter_by(source_standard_id=std.id).all()
            self.assertEqual(len(rels), 2)
            explicit_rels = [r for r in rels if r.is_explicit_source]
            derived_rels = [r for r in rels if not r.is_explicit_source]
            self.assertEqual(len(explicit_rels), 1)
            self.assertEqual(len(derived_rels), 1)

        finally:
            session.close()

if __name__ == '__main__':
    unittest.main()
