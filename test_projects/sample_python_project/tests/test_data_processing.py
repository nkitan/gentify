"""
Unit tests for data processing modules.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.data_processing.file_handler import FileHandler, FileHandlerError
from src.data_processing.data_analyzer import DataAnalyzer, DataAnalyzerError


class TestFileHandler:
    """Test cases for FileHandler class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.handler = FileHandler()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_read_write_text_file(self):
        """Test reading and writing text files."""
        test_content = "Hello, World!\nThis is a test file."
        test_file = Path(self.temp_dir) / "test.txt"
        
        # Write text file
        self.handler.write_text_file(test_file, test_content)
        assert test_file.exists()
        
        # Read text file
        content = self.handler.read_text_file(test_file)
        assert content == test_content
    
    def test_read_nonexistent_file(self):
        """Test reading a non-existent file raises error."""
        nonexistent_file = Path(self.temp_dir) / "nonexistent.txt"
        
        with pytest.raises(FileHandlerError, match="File does not exist"):
            self.handler.read_text_file(nonexistent_file)
    
    def test_read_write_json_file(self):
        """Test reading and writing JSON files."""
        test_data = {
            "name": "John Doe",
            "age": 30,
            "skills": ["Python", "JavaScript", "SQL"],
            "active": True
        }
        test_file = Path(self.temp_dir) / "test.json"
        
        # Write JSON file
        self.handler.write_json_file(test_file, test_data)
        assert test_file.exists()
        
        # Read JSON file
        data = self.handler.read_json_file(test_file)
        assert data == test_data
    
    def test_read_invalid_json(self):
        """Test reading invalid JSON raises error."""
        invalid_json = "{ invalid json content"
        test_file = Path(self.temp_dir) / "invalid.json"
        
        with open(test_file, 'w') as f:
            f.write(invalid_json)
        
        with pytest.raises(FileHandlerError, match="Invalid JSON"):
            self.handler.read_json_file(test_file)
    
    def test_read_write_csv_file(self):
        """Test reading and writing CSV files."""
        test_data = [
            {"name": "Alice", "age": "25", "city": "New York"},
            {"name": "Bob", "age": "30", "city": "San Francisco"},
            {"name": "Charlie", "age": "35", "city": "Chicago"}
        ]
        test_file = Path(self.temp_dir) / "test.csv"
        
        # Write CSV file
        self.handler.write_csv_file(test_file, test_data)
        assert test_file.exists()
        
        # Read CSV file
        data = self.handler.read_csv_file(test_file)
        assert data == test_data
    
    def test_write_empty_csv(self):
        """Test writing empty CSV data raises error."""
        test_file = Path(self.temp_dir) / "empty.csv"
        
        with pytest.raises(FileHandlerError, match="Cannot write empty data to CSV"):
            self.handler.write_csv_file(test_file, [])
    
    def test_get_file_info(self):
        """Test getting file information."""
        test_content = "Test file content"
        test_file = Path(self.temp_dir) / "info_test.txt"
        
        self.handler.write_text_file(test_file, test_content)
        
        info = self.handler.get_file_info(test_file)
        
        assert info["name"] == "info_test.txt"
        assert info["extension"] == ".txt"
        assert info["size_bytes"] == len(test_content.encode('utf-8'))
        assert info["is_file"] is True
        assert info["is_directory"] is False
    
    def test_get_file_info_nonexistent(self):
        """Test getting info for non-existent file raises error."""
        nonexistent_file = Path(self.temp_dir) / "nonexistent.txt"
        
        with pytest.raises(FileHandlerError, match="File does not exist"):
            self.handler.get_file_info(nonexistent_file)
    
    def test_encoding_handling(self):
        """Test handling different encodings."""
        # Test with UTF-8 content including special characters
        test_content = "Hello 世界! Café naïve résumé"
        test_file = Path(self.temp_dir) / "utf8_test.txt"
        
        self.handler.write_text_file(test_file, test_content)
        content = self.handler.read_text_file(test_file)
        
        assert content == test_content


class TestDataAnalyzer:
    """Test cases for DataAnalyzer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = DataAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_analyze_csv_file(self):
        """Test analyzing a CSV file."""
        # Create test CSV data
        csv_data = [
            {"name": "Alice", "age": "25", "salary": "50000"},
            {"name": "Bob", "age": "30", "salary": "60000"},
            {"name": "Charlie", "age": "35", "salary": "70000"}
        ]
        csv_file = Path(self.temp_dir) / "test_data.csv"
        
        # Use file handler to create the CSV
        file_handler = FileHandler()
        file_handler.write_csv_file(csv_file, csv_data)
        
        # Analyze the file
        result = self.analyzer.analyze_file(csv_file)
        
        assert result["analysis"]["data_type"] == "tabular"
        assert result["analysis"]["row_count"] == 3
        assert result["analysis"]["column_count"] == 3
        assert "name" in result["analysis"]["columns"]
        assert "age" in result["analysis"]["columns"]
        assert "salary" in result["analysis"]["columns"]
        
        # Check numeric column analysis
        age_analysis = result["analysis"]["column_analysis"]["age"]
        assert age_analysis["data_type"] == "numeric"
        assert age_analysis["min"] == 25
        assert age_analysis["max"] == 35
        assert age_analysis["mean"] == 30
    
    def test_analyze_json_file(self):
        """Test analyzing a JSON file."""
        # Create test JSON data
        json_data = {
            "users": [
                {"id": 1, "name": "Alice", "active": True},
                {"id": 2, "name": "Bob", "active": False}
            ],
            "metadata": {
                "total": 2,
                "page": 1
            }
        }
        json_file = Path(self.temp_dir) / "test_data.json"
        
        # Use file handler to create the JSON
        file_handler = FileHandler()
        file_handler.write_json_file(json_file, json_data)
        
        # Analyze the file
        result = self.analyzer.analyze_file(json_file)
        
        assert result["analysis"]["data_type"] == "json"
        assert result["analysis"]["structure"]["type"] == "object"
        assert "users" in result["analysis"]["structure"]["keys"]
        assert "metadata" in result["analysis"]["structure"]["keys"]
    
    def test_analyze_text_file(self):
        """Test analyzing a text file."""
        # Create test text data
        text_content = """
        This is a sample text file for testing.
        It contains multiple lines and various words.
        Some words appear more than once in this text.
        Testing testing testing.
        """
        text_file = Path(self.temp_dir) / "test_data.txt"
        
        # Use file handler to create the text file
        file_handler = FileHandler()
        file_handler.write_text_file(text_file, text_content.strip())
        
        # Analyze the file
        result = self.analyzer.analyze_file(text_file)
        
        assert result["analysis"]["data_type"] == "text"
        assert result["analysis"]["line_count"] == 4
        assert result["analysis"]["word_count"] > 0
        assert "testing" in result["analysis"]["top_words"]
    
    def test_transform_csv_data(self):
        """Test transforming CSV data."""
        # Create test CSV data with numeric columns
        csv_data = [
            {"name": "Alice", "score": "85", "rating": "4.2"},
            {"name": "Bob", "score": "92", "rating": "4.8"},
            {"name": "Charlie", "score": "78", "rating": "3.9"}
        ]
        input_file = Path(self.temp_dir) / "input.csv"
        output_file = Path(self.temp_dir) / "output.csv"
        
        # Create input file
        file_handler = FileHandler()
        file_handler.write_csv_file(input_file, csv_data)
        
        # Transform data (normalize)
        self.analyzer.transform_data(input_file, output_file, "normalize")
        
        # Verify output file was created
        assert output_file.exists()
        
        # Read and verify transformed data
        transformed_data = file_handler.read_csv_file(output_file)
        assert len(transformed_data) == 3
        
        # Check that numeric columns were normalized (values between 0 and 1)
        for row in transformed_data:
            score = float(row["score"])
            rating = float(row["rating"])
            assert 0 <= score <= 1
            assert 0 <= rating <= 1
    
    def test_filter_csv_data(self):
        """Test filtering CSV data."""
        # Create test CSV data
        csv_data = [
            {"name": "Alice", "age": "25", "active": "true"},
            {"name": "Bob", "age": "30", "active": "false"},
            {"name": "Charlie", "age": "35", "active": "true"},
            {"name": "David", "age": "", "active": "true"}  # Missing age
        ]
        input_file = Path(self.temp_dir) / "input.csv"
        output_file = Path(self.temp_dir) / "filtered.csv"
        
        # Create input file
        file_handler = FileHandler()
        file_handler.write_csv_file(input_file, csv_data)
        
        # Filter data (remove rows with missing values)
        self.analyzer.filter_data(input_file, output_file)
        
        # Verify output file was created
        assert output_file.exists()
        
        # Read and verify filtered data
        filtered_data = file_handler.read_csv_file(output_file)
        assert len(filtered_data) == 3  # Should exclude David (missing age)
        
        # Verify David's row was filtered out
        names = [row["name"] for row in filtered_data]
        assert "David" not in names
    
    def test_get_last_analysis(self):
        """Test getting last analysis results."""
        # Initially should be None
        assert self.analyzer.get_last_analysis() is None
        
        # Create and analyze a simple text file
        text_content = "Simple test content"
        text_file = Path(self.temp_dir) / "simple.txt"
        
        file_handler = FileHandler()
        file_handler.write_text_file(text_file, text_content)
        
        # Analyze file
        result = self.analyzer.analyze_file(text_file)
        
        # Check that last analysis is stored
        last_analysis = self.analyzer.get_last_analysis()
        assert last_analysis is not None
        assert last_analysis == result
    
    def test_analyze_nonexistent_file(self):
        """Test analyzing non-existent file raises error."""
        nonexistent_file = Path(self.temp_dir) / "nonexistent.csv"
        
        with pytest.raises(DataAnalyzerError, match="File handling error"):
            self.analyzer.analyze_file(nonexistent_file)
    
    def test_transform_unsupported_format(self):
        """Test transforming unsupported file format raises error."""
        # Create a text file
        text_file = Path(self.temp_dir) / "test.txt"
        output_file = Path(self.temp_dir) / "output.txt"
        
        file_handler = FileHandler()
        file_handler.write_text_file(text_file, "test content")
        
        with pytest.raises(DataAnalyzerError, match="Transformation not supported"):
            self.analyzer.transform_data(text_file, output_file)


class TestDataProcessingIntegration:
    """Integration tests for data processing components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.file_handler = FileHandler()
        self.analyzer = DataAnalyzer(self.file_handler)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_end_to_end_csv_processing(self):
        """Test complete CSV processing workflow."""
        # Create sample data
        original_data = [
            {"product": "Widget A", "price": "10.50", "quantity": "100"},
            {"product": "Widget B", "price": "15.75", "quantity": "50"},
            {"product": "Widget C", "price": "8.25", "quantity": "200"},
            {"product": "Widget D", "price": "", "quantity": "75"}  # Missing price
        ]
        
        # Step 1: Create original file
        original_file = Path(self.temp_dir) / "products.csv"
        self.file_handler.write_csv_file(original_file, original_data)
        
        # Step 2: Analyze original data
        analysis = self.analyzer.analyze_file(original_file)
        assert analysis["analysis"]["row_count"] == 4
        assert analysis["analysis"]["column_count"] == 3
        
        # Step 3: Filter out incomplete records
        filtered_file = Path(self.temp_dir) / "products_filtered.csv"
        self.analyzer.filter_data(original_file, filtered_file)
        
        # Step 4: Analyze filtered data
        filtered_analysis = self.analyzer.analyze_file(filtered_file)
        assert filtered_analysis["analysis"]["row_count"] == 3  # One row filtered out
        
        # Step 5: Transform filtered data
        transformed_file = Path(self.temp_dir) / "products_normalized.csv"
        self.analyzer.transform_data(filtered_file, transformed_file, "normalize")
        
        # Step 6: Verify final result
        final_data = self.file_handler.read_csv_file(transformed_file)
        assert len(final_data) == 3
        
        # Verify normalization worked (price and quantity should be 0-1)
        for row in final_data:
            if row["price"]:  # Skip empty prices
                price = float(row["price"])
                quantity = float(row["quantity"])
                assert 0 <= price <= 1
                assert 0 <= quantity <= 1
