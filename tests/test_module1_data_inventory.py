import unittest
import os
import csv
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_DIR = os.path.join(BASE_DIR, 'Skill-Connect', 'csvfiles')
DOCS_DIR = os.path.join(BASE_DIR, 'docs')

class TestModule1DataInventory(unittest.TestCase):
    """Module 1 automated validation tests: dataset inspection and data dictionary."""

    def test_01_all_files_exist(self):
        """Verify all 12 data files exist in Skill-Connect/csvfiles/."""
        expected_files = [
            'standards.csv',
            'sample_standards.json',
            'ReportExcel.csv',
            'schem.csv',
            'certification.csv',
            'productlicence.csv',
            'bis_standards.csv',
            'bis_standards.json',
            'relationships.json',
            'manifest.json',
            'query_dataset.json',
            'upcomming.csv'
        ]
        for fname in expected_files:
            fpath = os.path.join(CSV_DIR, fname)
            self.assertTrue(os.path.isfile(fpath), f"File missing: {fname}")
            self.assertGreater(os.path.getsize(fpath), 0, f"File empty: {fname}")

    def test_02_data_inventory_doc_exists(self):
        """Verify the comprehensive data inventory document exists and is populated."""
        doc_path = os.path.join(DOCS_DIR, 'data-inventory.md')
        self.assertTrue(os.path.isfile(doc_path), "docs/data-inventory.md does not exist")
        size = os.path.getsize(doc_path)
        self.assertGreater(size, 10000, f"docs/data-inventory.md too small: {size} bytes")

    def test_03_standards_csv_integrity(self):
        """Verify standards.csv schema and record count."""
        fpath = os.path.join(CSV_DIR, 'standards.csv')
        with open(fpath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            expected_headers = {
                'standard_id', 'title', 'description', 'category', 'department',
                'year', 'status', 'supersedes', 'certification_scheme',
                'qco_applicable', 'qco_reference'
            }
            self.assertEqual(set(reader.fieldnames), expected_headers)
            rows = list(reader)
            self.assertEqual(len(rows), 234, f"Expected 234 standards, found {len(rows)}")
            
            # Check primary key uniqueness
            ids = [r['standard_id'] for r in rows]
            self.assertEqual(len(ids), len(set(ids)), "standard_id must be unique")

    def test_04_sample_standards_json_integrity(self):
        """Verify sample_standards.json schema and records."""
        fpath = os.path.join(CSV_DIR, 'sample_standards.json')
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 78, f"Expected 78 standards, found {len(data)}")
            
            for item in data:
                self.assertIn('is_number', item)
                self.assertIn('title', item)
                self.assertIn('description', item)
                self.assertIn('scope', item)

    def test_05_relationships_graph(self):
        """Verify relationships.json has valid graph edges and standard nodes."""
        fpath = os.path.join(CSV_DIR, 'relationships.json')
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertIsInstance(data, dict)
            self.assertEqual(len(data), 9, "Expected 9 standards in relationships.json")
            
            total_edges = 0
            for std_id, rels in data.items():
                for rel_key, targets in rels.items():
                    if isinstance(targets, list):
                        total_edges += len(targets)
            self.assertEqual(total_edges, 27, f"Expected 27 relationship edges, found {total_edges}")

    def test_06_report_excel_classification(self):
        """Verify ReportExcel.csv contains standard classifications."""
        fpath = os.path.join(CSV_DIR, 'ReportExcel.csv')
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = list(reader)
            self.assertEqual(len(rows), 1476, f"Expected 1,476 rows, found {len(rows)}")

    def test_07_schem_qco_mapping(self):
        """Verify schem.csv contains QCO scheme data."""
        fpath = os.path.join(CSV_DIR, 'schem.csv')
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = list(reader)
            self.assertEqual(len(rows), 711, f"Expected 711 rows, found {len(rows)}")

    def test_08_query_dataset_for_evaluation(self):
        """Verify query_dataset.json contains evaluation test queries."""
        fpath = os.path.join(CSV_DIR, 'query_dataset.json')
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 14, f"Expected 14 test cases, found {len(data)}")
            
            for tc in data:
                self.assertIn('id', tc)
                self.assertIn('query', tc)
                self.assertIn('expected_intent', tc)

if __name__ == '__main__':
    unittest.main()
