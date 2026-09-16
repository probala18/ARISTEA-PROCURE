"""
Unit tests for standard ID normalization and conversion utilities (Module 3).
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from backend.app.core.normalizers import (
    parse_standard_id,
    normalize_standard_id,
    extract_is_number,
    normalize_status,
    normalize_relationship_type,
    clean_text,
    safe_int,
    safe_bool,
    normalize_certification_type,
)

def test_parse_standard_id_basic():
    res = parse_standard_id("IS 12615:2018")
    assert res["canonical_id"] == "IS 12615:2018"
    assert res["is_number"] == "IS 12615"
    assert res["number"] == "12615"
    assert res["year"] == 2018
    assert res["prefix"] == "IS"

def test_parse_standard_id_no_year():
    res = parse_standard_id("IS 694")
    assert res["canonical_id"] == "IS 694"
    assert res["is_number"] == "IS 694"
    assert res["year"] is None

def test_parse_standard_id_no_space():
    res = parse_standard_id("IS694")
    assert res["canonical_id"] == "IS 694"
    assert res["is_number"] == "IS 694"
    assert res["number"] == "694"

def test_parse_standard_id_iec():
    res = parse_standard_id("IS/IEC 60947: Part 2:2016")
    assert res["prefix"] == "IS/IEC"
    assert res["number"] == "60947"
    assert res["part"] == "2"
    assert res["year"] == 2016
    assert res["canonical_id"] == "IS/IEC 60947 (Part 2):2016"
    assert res["is_number"] == "IS/IEC 60947 (Part 2)"

def test_parse_standard_id_part_and_section():
    res = parse_standard_id("IS 15999 (Part 2/Sec 1)")
    assert res["is_number"] == "IS 15999 (Part 2/Sec 1)"
    assert res["part"] == "2"
    assert res["section"] == "1"

def test_parse_standard_id_spaces_around_colon():
    res = parse_standard_id("IS 1 : 1968")
    assert res["canonical_id"] == "IS 1:1968"
    assert res["is_number"] == "IS 1"
    assert res["year"] == 1968

def test_parse_standard_id_bare_digits():
    res = parse_standard_id("4003 (Part 1):1978", assume_is_prefix=True)
    assert res["canonical_id"] == "IS 4003 (Part 1):1978"
    assert res["is_number"] == "IS 4003 (Part 1)"
    assert res["year"] == 1978

def test_normalize_status():
    assert normalize_status("active") == "CURRENT"
    assert normalize_status("Current") == "CURRENT"
    assert normalize_status("superseded") == "SUPERSEDED"
    assert normalize_status("obsolete") == "SUPERSEDED"
    assert normalize_status("withdrawn") == "SUPERSEDED"
    assert normalize_status(None) == "CURRENT"

def test_normalize_relationship_type():
    assert normalize_relationship_type("testing_standards") == "TESTING"
    assert normalize_relationship_type("safety_standards") == "SAFETY"
    assert normalize_relationship_type("normative_references") == "NORMATIVE_REFERENCE"
    assert normalize_relationship_type("superseded_by_current") == "SUPERSEDES"
    assert normalize_relationship_type(None) == "OTHER"

def test_clean_text():
    assert clean_text("  IS  694 \n") == "IS 694"
    assert clean_text("\ufeffHello") == "Hello"
    assert clean_text(None) is None
    assert clean_text("") is None

def test_safe_int_and_bool():
    assert safe_int("2018") == 2018
    assert safe_int("2018.0") == 2018
    assert safe_int("invalid", default=0) == 0
    assert safe_bool("True") is True
    assert safe_bool("mandatory") is True
    assert safe_bool("False") is False
    assert safe_bool("voluntary") is False
    assert safe_bool("unknown", default=None) is None

def test_normalize_certification_type():
    assert normalize_certification_type("Scheme-I / ISI Mark") == "BIS_ISI"
    assert normalize_certification_type("Compulsory Registration Scheme (CRS)") == "CRS"
    assert normalize_certification_type("Hallmarking") == "HALLMARKING"
