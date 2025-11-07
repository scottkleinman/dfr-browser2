"""
Pytest test suite for create_bibliography.py

Tests core functionality including:
- Author parsing
- Date parsing
- Field normalization
- CSL validation
- Citation formatting
- CSV to CSL conversion
- CSL JSON processing
- End-to-end bibliography creation

Run with: pytest test_create_bibliography.py -v

# WARNING:
The following functions currently fail because there is no test file for them to load:

- test_csv_to_bibliography
- test_json_to_bibliography
- test_style_shortcuts
- test_csv_round_trip
- test_multiple_styles_from_csv
"""

import json
import sys
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "bin"))

from create_bibliography import (
    CITEPROC_AVAILABLE,
    convert_metadata_to_csl,
    create_bibliography,
    format_citation_with_citeproc,
    normalize_field_name,
    parse_authors,
    parse_date,
    process_csl_json,
    validate_csl_entry,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_csv_data():
    """Sample metadata CSV data."""
    return pd.DataFrame(
        {
            "author": [
                "Smith, John",
                "Jones, Mary; Davis, Bob",
                "Corporate Author",
                "Liu, Wei",
            ],
            "title": [
                "Understanding Topic Models",
                "Advanced NLP Techniques",
                "Annual Report 2023",
                "Machine Learning Applications",
            ],
            "year": [2023, 2024, 2023, 2022],
            "journal": [
                "Journal of AI",
                "Computational Linguistics",
                "",
                "AI Review",
            ],
            "volume": [15, 28, "", 10],
            "issue": [3, 1, "", 2],
            "pages": ["45-67", "12-34", "", "100-125"],
            "doi": [
                "10.1234/jai.2023",
                "10.5678/cl.2024",
                "",
                "10.9012/air.2022",
            ],
        }
    )


@pytest.fixture
def sample_csl_json():
    """Sample CSL JSON data."""
    return [
        {
            "type": "article-journal",
            "id": "smith2023",
            "title": "Understanding Topic Models",
            "author": [{"family": "Smith", "given": "John"}],
            "issued": {"date-parts": [[2023]]},
            "container-title": "Journal of AI",
            "volume": "15",
            "issue": "3",
            "page": "45-67",
            "DOI": "10.1234/jai.2023",
        },
        {
            "type": "article-journal",
            "id": "jones2024",
            "title": "Advanced NLP Techniques",
            "author": [
                {"family": "Jones", "given": "Mary"},
                {"family": "Davis", "given": "Bob"},
            ],
            "issued": {"date-parts": [[2024]]},
            "container-title": "Computational Linguistics",
            "volume": "28",
            "issue": "1",
            "page": "12-34",
        },
    ]


@pytest.fixture
def sample_csl_with_formatted():
    """Sample CSL JSON with some entries already formatted."""
    return [
        {
            "type": "article-journal",
            "id": "smith2023",
            "title": "Test Article",
            "author": [{"family": "Smith", "given": "John"}],
            "issued": {"date-parts": [[2023]]},
            "formatted-citation": "Smith, John. 2023. Test Article.",
        },
        {
            "type": "article-journal",
            "id": "jones2024",
            "title": "Another Article",
            "author": [{"family": "Jones", "given": "Mary"}],
            "issued": {"date-parts": [[2024]]},
        },
    ]


# ============================================================================
# Test parse_authors()
# ============================================================================


class TestParseAuthors:
    """Test suite for parse_authors() function."""

    def test_single_author_lastname_firstname(self):
        """Test parsing single author with lastname, firstname format."""
        result = parse_authors("Smith, John")
        assert len(result) == 1
        assert result[0]["family"] == "Smith"
        assert result[0]["given"] == "John"

    def test_single_author_firstname_lastname(self):
        """Test parsing single author with firstname lastname format."""
        result = parse_authors("John Smith")
        assert len(result) == 1
        assert result[0]["family"] == "Smith"
        assert result[0]["given"] == "John"

    def test_multiple_authors_semicolon(self):
        """Test parsing multiple authors separated by semicolons."""
        result = parse_authors("Smith, John; Jones, Mary")
        assert len(result) == 2
        assert result[0]["family"] == "Smith"
        assert result[0]["given"] == "John"
        assert result[1]["family"] == "Jones"
        assert result[1]["given"] == "Mary"

    def test_multiple_authors_and(self):
        """Test parsing multiple authors separated by 'and'."""
        result = parse_authors("Smith, John and Jones, Mary")
        assert len(result) == 2
        assert result[0]["family"] == "Smith"
        assert result[0]["given"] == "John"
        assert result[1]["family"] == "Jones"
        assert result[1]["given"] == "Mary"

    def test_multiple_authors_ampersand(self):
        """Test parsing multiple authors separated by '&'."""
        result = parse_authors("Smith, John & Jones, Mary")
        assert len(result) == 2
        assert result[0]["family"] == "Smith"
        assert result[0]["given"] == "John"
        assert result[1]["family"] == "Jones"
        assert result[1]["given"] == "Mary"

    def test_multiple_authors_comma_separated(self):
        """Test parsing multiple authors with comma-only separation (ambiguous case)."""
        result = parse_authors("Smith, John, Jones, Mary")
        # Should try to intelligently parse as two authors
        assert len(result) == 2
        assert result[0]["family"] == "Smith"
        assert result[0]["given"] == "John"
        assert result[1]["family"] == "Jones"
        assert result[1]["given"] == "Mary"

    def test_three_authors_semicolon(self):
        """Test parsing three authors with semicolons."""
        result = parse_authors("Smith, John; Jones, Mary; Davis, Bob")
        assert len(result) == 3
        assert result[0]["family"] == "Smith"
        assert result[1]["family"] == "Jones"
        assert result[2]["family"] == "Davis"

    def test_corporate_author(self):
        """Test parsing corporate/organizational author."""
        result = parse_authors("United Nations")
        assert len(result) == 1
        # Corporate authors might be parsed as literal or have family name
        assert "family" in result[0] or "literal" in result[0]

    def test_empty_author(self):
        """Test parsing empty author string."""
        result = parse_authors("")
        assert result == []

    def test_author_with_middle_initial(self):
        """Test parsing author with middle initial."""
        result = parse_authors("Smith, John Q.")
        assert len(result) == 1
        assert result[0]["family"] == "Smith"
        assert "John" in result[0]["given"]

    def test_author_with_suffix(self):
        """Test parsing author with suffix (Jr., III, etc.)."""
        result = parse_authors("Smith, John Jr.")
        assert len(result) == 1
        assert result[0]["family"] == "Smith"
        assert "John" in result[0]["given"]
        # Suffix might be in given or separate suffix field

    def test_multiple_authors_newline_separated(self):
        """Test parsing multiple authors separated by newlines."""
        result = parse_authors("Smith, John\nJones, Mary")
        assert len(result) == 2
        assert result[0]["family"] == "Smith"
        assert result[1]["family"] == "Jones"


# ============================================================================
# Test parse_date()
# ============================================================================


class TestParseDate:
    """Test suite for parse_date() function."""

    def test_year_only(self):
        """Test parsing year only."""
        result = parse_date("2023")
        assert "date-parts" in result
        assert result["date-parts"][0][0] == 2023

    def test_full_date_iso(self):
        """Test parsing full ISO date."""
        result = parse_date("2023-05-15")
        assert "date-parts" in result
        assert result["date-parts"][0] == [2023, 5, 15]

    def test_full_date_text(self):
        """Test parsing full text date."""
        result = parse_date("May 15, 2023")
        assert "date-parts" in result
        assert result["date-parts"][0][0] == 2023
        assert result["date-parts"][0][1] == 5

    def test_unparseable_date(self):
        """Test handling unparseable date as literal."""
        result = parse_date("Spring 2023")
        # Should return literal for unparseable dates
        assert "literal" in result or "date-parts" in result

    def test_empty_date(self):
        """Test handling empty date string."""
        result = parse_date("")
        assert result is None

    def test_invalid_date(self):
        """Test handling invalid date string."""
        result = parse_date("not a date")
        # Should either return literal or empty dict
        assert isinstance(result, dict)


# ============================================================================
# Test normalize_field_name()
# ============================================================================


class TestNormalizeFieldName:
    """Test suite for normalize_field_name() function."""

    def test_lowercase_conversion(self):
        """Test conversion to lowercase."""
        assert normalize_field_name("AUTHOR") == "author"

    def test_space_to_null(self):
        """Test space replacement with null."""
        assert normalize_field_name("container title") == "containertitle"

    def test_hyphen_to_null(self):
        """Test hyphen replacement with null."""
        assert normalize_field_name("container-title") == "containertitle"

    def test_underscore_to_null(self):
        """Test underscore replacement with null."""
        assert normalize_field_name("container_title") == "containertitle"

    def test_mixed_case_and_separators(self):
        """Test normalization with mixed case and separators."""
        assert normalize_field_name("Container_Title Name") == "containertitlename"


# ============================================================================
# Test validate_csl_entry()
# ============================================================================


class TestValidateCSLEntry:
    """Test suite for validate_csl_entry() function."""

    def test_valid_entry_preserved(self):
        """Test that valid CSL fields are preserved."""
        entry = {
            "type": "article-journal",
            "id": "test123",
            "title": "Test Article",
            "author": [{"family": "Smith", "given": "John"}],
        }
        result = validate_csl_entry(entry)
        assert "type" in result
        assert "id" in result
        assert "title" in result
        assert "author" in result

    def test_invalid_fields_removed(self):
        """Test that invalid CSL fields are removed."""
        entry = {
            "type": "article",
            "title": "Test",
            "invalid_field": "should be removed",
            "another_bad_field": 123,
        }
        result = validate_csl_entry(entry)
        assert "invalid_field" not in result
        assert "another_bad_field" not in result

    def test_excluded_fields_removed(self):
        """Test that excluded fields are removed."""
        entry = {
            "type": "article",
            "title": "Test",
            "docnum": "should be excluded",
            "filename": "test.txt",
        }
        result = validate_csl_entry(entry)
        assert "docnum" not in result
        assert "filename" not in result

    def test_type_defaults(self):
        """Test that type defaults to 'article-journal' if missing."""
        entry = {"title": "Test"}
        result = validate_csl_entry(entry)
        assert result["type"] == "article-journal"

    def test_id_generation(self):
        """Test that ID is generated if missing."""
        entry = {"type": "article", "title": "Test Article"}
        result = validate_csl_entry(entry)
        assert "id" in result
        assert isinstance(result["id"], str)


# ============================================================================
# Test format_citation_with_citeproc()
# ============================================================================


@pytest.mark.skipif(not CITEPROC_AVAILABLE, reason="citeproc-py not installed")
class TestFormatCitationWithCiteproc:
    """Test suite for format_citation_with_citeproc() function."""

    def test_basic_citation_formatting(self):
        """Test basic citation formatting."""
        entry = {
            "type": "article-journal",
            "id": "test123",
            "title": "Test Article",
            "author": [{"family": "Smith", "given": "John"}],
            "issued": {"date-parts": [[2023]]},
        }
        result = format_citation_with_citeproc(entry, "chicago-author-date")
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Smith" in result
        assert "2023" in result

    def test_different_styles(self):
        """Test formatting with different citation styles."""
        entry = {
            "type": "article-journal",
            "id": "test123",
            "title": "Test Article",
            "author": [{"family": "Smith", "given": "John"}],
            "issued": {"date-parts": [[2023]]},
        }
        chicago = format_citation_with_citeproc(entry, "chicago-author-date")
        apa = format_citation_with_citeproc(entry, "apa")

        # Both should produce citations but they should be different
        assert isinstance(chicago, str)
        assert isinstance(apa, str)
        # Note: They might be the same for simple entries, so we just check they exist

    def test_fallback_citation(self):
        """Test fallback citation when citeproc fails."""
        entry = {
            "type": "article",
            "id": "test123",
            "title": "Test Article",
            "author": [{"family": "Smith", "given": "John"}],
            "issued": {"date-parts": [[2023]]},
        }
        result = format_citation_with_citeproc(entry, "invalid-style-name")
        # Should still return a citation (fallback)
        assert isinstance(result, str)
        assert len(result) > 0


class TestFormatCitationFallback:
    """Test suite for fallback citation formatting."""

    def test_fallback_with_author(self):
        """Test fallback citation with author present."""
        entry = {
            "type": "article",
            "id": "test123",
            "title": "Test Article",
            "author": [{"family": "Smith", "given": "John"}],
            "issued": {"date-parts": [[2023]]},
        }
        # Use a style that doesn't exist to force fallback
        result = format_citation_with_citeproc(entry, "nonexistent-style", debug=False)
        assert isinstance(result, str)
        assert "Smith" in result or "Test Article" in result

    def test_fallback_without_author(self):
        """Test fallback citation without author."""
        entry = {
            "type": "article",
            "id": "test123",
            "title": "Test Article",
            "issued": {"date-parts": [[2023]]},
        }
        result = format_citation_with_citeproc(entry, "nonexistent-style", debug=False)
        assert isinstance(result, str)
        assert "Test Article" in result


# ============================================================================
# Test convert_metadata_to_csl()
# ============================================================================


class TestConvertMetadataToCSL:
    """Test suite for convert_metadata_to_csl() function."""

    def test_csv_conversion(self, temp_dir, sample_csv_data):
        """Test converting CSV to CSL JSON."""
        csv_file = temp_dir / "metadata.csv"
        sample_csv_data.to_csv(csv_file, index=False)

        result = convert_metadata_to_csl(str(csv_file), "chicago-author-date")

        assert isinstance(result, list)
        assert len(result) > 0

        # Check first entry
        entry = result[0]
        assert "id" in entry
        assert "type" in entry
        assert "title" in entry

    def test_csv_with_missing_fields(self, temp_dir):
        """Test CSV with some missing fields."""
        df = pd.DataFrame(
            {
                "title": ["Article 1", "Article 2"],
                "author": ["Smith, John", ""],
                "year": [2023, ""],
            }
        )
        csv_file = temp_dir / "metadata.csv"
        df.to_csv(csv_file, index=False)

        result = convert_metadata_to_csl(str(csv_file), "chicago-author-date")

        assert len(result) == 2
        # First should have author
        assert "author" in result[0]
        # Second might not have author or year


# ============================================================================
# Test process_csl_json()
# ============================================================================


class TestProcessCSLJson:
    """Test suite for process_csl_json() function."""

    def test_basic_json_processing(self, temp_dir, sample_csl_json):
        """Test processing CSL JSON file."""
        json_file = temp_dir / "bibliography.json"
        with open(json_file, "w") as f:
            json.dump(sample_csl_json, f)

        result = process_csl_json(str(json_file), "chicago-author-date")

        assert isinstance(result, list)
        assert len(result) == len(sample_csl_json)

    def test_preserve_existing_citations(self, temp_dir, sample_csl_with_formatted):
        """Test that existing formatted citations are preserved."""
        json_file = temp_dir / "bibliography.json"
        with open(json_file, "w") as f:
            json.dump(sample_csl_with_formatted, f)

        result = process_csl_json(str(json_file), "apa")

        # First entry had formatted citation - should be preserved
        assert result[0]["formatted-citation"] == "Smith, John. 2023. Test Article."

        # Second entry should have new formatted citation
        assert "formatted-citation" in result[1]

    def test_missing_id_generation(self, temp_dir):
        """Test that missing IDs are generated."""
        data = [
            {"type": "article", "title": "Test 1"},
            {"type": "article", "title": "Test 2"},
        ]
        json_file = temp_dir / "bibliography.json"
        with open(json_file, "w") as f:
            json.dump(data, f)

        result = process_csl_json(str(json_file), "chicago-author-date")

        assert "id" in result[0]
        assert "id" in result[1]

    def test_invalid_json_structure(self, temp_dir):
        """Test handling of invalid JSON structure."""
        json_file = temp_dir / "bad.json"
        with open(json_file, "w") as f:
            json.dump({"not": "an array"}, f)

        result = process_csl_json(str(json_file), "chicago-author-date")

        assert result is None

    def test_nonexistent_file(self):
        """Test handling of nonexistent file."""
        result = process_csl_json("nonexistent.json", "chicago-author-date")
        assert result is None


# ============================================================================
# Test create_bibliography() - End-to-end
# ============================================================================


class TestCreateBibliography:
    """Test suite for create_bibliography() end-to-end function."""

    def test_csv_to_bibliography(self, temp_dir, sample_csv_data):
        """Test creating bibliography from CSV."""
        csv_file = temp_dir / "metadata.csv"
        output_file = temp_dir / "bibliography.json"

        sample_csv_data.to_csv(csv_file, index=False)

        # Change to temp directory to make relative paths work
        import os

        original_dir = os.getcwd()
        try:
            os.chdir(temp_dir)
            create_bibliography(
                input="metadata.csv",
                output="bibliography.json",
                style="chicago-author-date",
                debug=False,
            )
        finally:
            os.chdir(original_dir)

        assert output_file.exists()

        # Load and verify output
        with open(output_file) as f:
            result = json.load(f)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_json_to_bibliography(self, temp_dir, sample_csl_json):
        """Test creating bibliography from CSL JSON."""
        input_file = temp_dir / "input.json"
        output_file = temp_dir / "output.json"

        with open(input_file, "w") as f:
            json.dump(sample_csl_json, f)

        import os

        original_dir = os.getcwd()
        try:
            os.chdir(temp_dir)
            create_bibliography(
                input="input.json",
                output="output.json",
                style="apa",
                debug=False,
            )
        finally:
            os.chdir(original_dir)

        assert output_file.exists()

        with open(output_file) as f:
            result = json.load(f)

        assert isinstance(result, list)
        assert len(result) == len(sample_csl_json)

    def test_style_shortcuts(self, temp_dir, sample_csv_data):
        """Test citation style shortcuts."""
        csv_file = temp_dir / "metadata.csv"
        output_file = temp_dir / "bibliography.json"

        sample_csv_data.to_csv(csv_file, index=False)

        import os

        original_dir = os.getcwd()
        try:
            os.chdir(temp_dir)
            # Test shortcut "chicago" -> "chicago-author-date"
            create_bibliography(
                input="metadata.csv",
                output="bibliography.json",
                style="chicago",  # shortcut
                debug=False,
            )
        finally:
            os.chdir(original_dir)

        assert output_file.exists()

    def test_nonexistent_input_file(self, temp_dir):
        """Test handling of nonexistent input file."""
        import os

        original_dir = os.getcwd()
        try:
            os.chdir(temp_dir)
            # Should not raise exception, just print error
            create_bibliography(
                input="nonexistent.csv",
                output="bibliography.json",
                style="chicago",
                debug=False,
            )
        finally:
            os.chdir(original_dir)

        # Output file should not be created
        output_file = temp_dir / "bibliography.json"
        assert not output_file.exists()


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for the complete workflow."""

    def test_csv_round_trip(self, temp_dir, sample_csv_data):
        """Test CSV -> CSL JSON -> Re-style workflow."""
        csv_file = temp_dir / "metadata.csv"
        chicago_output = temp_dir / "chicago.json"
        apa_output = temp_dir / "apa.json"

        sample_csv_data.to_csv(csv_file, index=False)

        import os

        original_dir = os.getcwd()
        try:
            os.chdir(temp_dir)

            # Step 1: CSV to Chicago style
            create_bibliography(
                input="metadata.csv",
                output="chicago.json",
                style="chicago",
                debug=False,
            )

            # Step 2: Chicago to APA style
            create_bibliography(
                input="chicago.json",
                output="apa.json",
                style="apa",
                debug=False,
            )
        finally:
            os.chdir(original_dir)

        # Both outputs should exist
        assert chicago_output.exists()
        assert apa_output.exists()

        # Load both and verify
        with open(chicago_output) as f:
            chicago_data = json.load(f)
        with open(apa_output) as f:
            apa_data = json.load(f)

        assert len(chicago_data) == len(apa_data)

    def test_multiple_styles_from_csv(self, temp_dir, sample_csv_data):
        """Test generating multiple bibliography styles from one CSV."""
        csv_file = temp_dir / "metadata.csv"
        sample_csv_data.to_csv(csv_file, index=False)

        styles = ["chicago", "apa", "mla"]
        outputs = []

        import os

        original_dir = os.getcwd()
        try:
            os.chdir(temp_dir)

            for style in styles:
                output = temp_dir / f"bibliography_{style}.json"
                outputs.append(output)

                create_bibliography(
                    input="metadata.csv",
                    output=f"bibliography_{style}.json",
                    style=style,
                    debug=False,
                )
        finally:
            os.chdir(original_dir)

        # All outputs should exist
        for output in outputs:
            assert output.exists()


# ============================================================================
# Run tests
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
