"""
Data Analyzer Module

This module provides comprehensive data analysis capabilities for various data formats
including statistical analysis, data transformation, and filtering operations.
"""

import json
import csv
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from .file_handler import FileHandler, FileHandlerError


class DataAnalyzerError(Exception):
    """Custom exception for data analysis operations."""
    pass


class DataAnalyzer:
    """
    Advanced data analysis and processing utility.
    
    Provides statistical analysis, data transformation, filtering,
    and reporting capabilities for structured data.
    """
    
    def __init__(self, file_handler: Optional[FileHandler] = None):
        """
        Initialize the data analyzer.
        
        Args:
            file_handler (Optional[FileHandler]): File handler instance
        """
        self.file_handler = file_handler or FileHandler()
        self.logger = logging.getLogger(__name__)
        self._last_analysis = None
    
    def analyze_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Perform comprehensive analysis on a data file.
        
        Args:
            file_path (Union[str, Path]): Path to the data file
            
        Returns:
            Dict[str, Any]: Analysis results
            
        Raises:
            DataAnalyzerError: If analysis fails
        """
        file_path = Path(file_path)
        
        try:
            # Get file information
            file_info = self.file_handler.get_file_info(file_path)
            
            # Determine file type and load data
            if file_path.suffix.lower() == '.csv':
                data = self.file_handler.read_csv_file(file_path)
                analysis = self._analyze_tabular_data(data)
            elif file_path.suffix.lower() == '.json':
                data = self.file_handler.read_json_file(file_path)
                analysis = self._analyze_json_data(data)
            else:
                # Treat as text file
                content = self.file_handler.read_text_file(file_path)
                analysis = self._analyze_text_data(content)
            
            # Combine file info with analysis
            result = {
                "file_info": file_info,
                "analysis": analysis,
                "timestamp": self._get_timestamp()
            }
            
            self._last_analysis = result
            self.logger.info(f"Completed analysis of file: {file_path}")
            
            return result
            
        except FileHandlerError as e:
            raise DataAnalyzerError(f"File handling error: {e}")
        except Exception as e:
            raise DataAnalyzerError(f"Analysis error for {file_path}: {e}")
    
    def _analyze_tabular_data(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze tabular data (CSV format).
        
        Args:
            data (List[Dict[str, Any]]): Tabular data
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        if not data:
            return {"error": "Empty dataset"}
        
        analysis = {
            "data_type": "tabular",
            "row_count": len(data),
            "column_count": len(data[0].keys()) if data else 0,
            "columns": list(data[0].keys()) if data else [],
            "column_analysis": {}
        }
        
        # Analyze each column
        for column in analysis["columns"]:
            values = [row.get(column) for row in data if row.get(column) is not None]
            
            column_stats = {
                "non_null_count": len(values),
                "null_count": len(data) - len(values),
                "unique_count": len(set(str(v) for v in values))
            }
            
            # Try to analyze as numeric data
            numeric_values = []
            for value in values:
                try:
                    numeric_values.append(float(value))
                except (ValueError, TypeError):
                    pass
            
            if numeric_values:
                column_stats.update({
                    "data_type": "numeric",
                    "min": min(numeric_values),
                    "max": max(numeric_values),
                    "mean": statistics.mean(numeric_values),
                    "median": statistics.median(numeric_values),
                    "std_dev": statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0
                })
            else:
                # Treat as categorical data
                value_counts = {}
                for value in values:
                    str_value = str(value)
                    value_counts[str_value] = value_counts.get(str_value, 0) + 1
                
                column_stats.update({
                    "data_type": "categorical",
                    "most_common": max(value_counts.items(), key=lambda x: x[1]) if value_counts else None,
                    "value_distribution": dict(sorted(value_counts.items(), key=lambda x: x[1], reverse=True)[:10])
                })
            
            analysis["column_analysis"][column] = column_stats
        
        return analysis
    
    def _analyze_json_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze JSON data structure.
        
        Args:
            data (Dict[str, Any]): JSON data
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        def analyze_structure(obj, path="root"):
            """Recursively analyze JSON structure."""
            if isinstance(obj, dict):
                return {
                    "type": "object",
                    "key_count": len(obj),
                    "keys": list(obj.keys()),
                    "nested_structure": {k: analyze_structure(v, f"{path}.{k}") for k, v in obj.items()}
                }
            elif isinstance(obj, list):
                return {
                    "type": "array",
                    "length": len(obj),
                    "element_types": list(set(type(item).__name__ for item in obj)),
                    "sample_elements": obj[:5] if len(obj) <= 5 else obj[:3]
                }
            else:
                return {
                    "type": type(obj).__name__,
                    "value": obj if not isinstance(obj, str) or len(str(obj)) <= 100 else str(obj)[:100] + "..."
                }
        
        return {
            "data_type": "json",
            "structure": analyze_structure(data)
        }
    
    def _analyze_text_data(self, content: str) -> Dict[str, Any]:
        """
        Analyze text file content.
        
        Args:
            content (str): Text content
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        lines = content.split('\n')
        words = content.split()
        
        # Character frequency analysis
        char_freq = {}
        for char in content:
            if char.isalpha():
                char = char.lower()
                char_freq[char] = char_freq.get(char, 0) + 1
        
        # Word frequency analysis (top 10)
        word_freq = {}
        for word in words:
            word = word.lower().strip('.,!?;:"()[]{}')
            if word:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "data_type": "text",
            "character_count": len(content),
            "line_count": len(lines),
            "word_count": len(words),
            "unique_words": len(set(word.lower() for word in words)),
            "average_words_per_line": len(words) / len(lines) if lines else 0,
            "top_words": dict(top_words),
            "character_frequency": dict(sorted(char_freq.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    
    def transform_data(self, input_file: Union[str, Path], output_file: Union[str, Path], 
                      transformation: str = "normalize") -> None:
        """
        Transform data from input file and save to output file.
        
        Args:
            input_file (Union[str, Path]): Input file path
            output_file (Union[str, Path]): Output file path
            transformation (str): Type of transformation to apply
            
        Raises:
            DataAnalyzerError: If transformation fails
        """
        input_path = Path(input_file)
        output_path = Path(output_file)
        
        try:
            if input_path.suffix.lower() == '.csv':
                data = self.file_handler.read_csv_file(input_path)
                
                if transformation == "normalize":
                    transformed_data = self._normalize_csv_data(data)
                elif transformation == "aggregate":
                    transformed_data = self._aggregate_csv_data(data)
                else:
                    raise DataAnalyzerError(f"Unknown transformation: {transformation}")
                
                self.file_handler.write_csv_file(output_path, transformed_data)
            else:
                raise DataAnalyzerError(f"Transformation not supported for {input_path.suffix} files")
            
            self.logger.info(f"Data transformed and saved to: {output_path}")
            
        except Exception as e:
            raise DataAnalyzerError(f"Transformation error: {e}")
    
    def filter_data(self, input_file: Union[str, Path], output_file: Union[str, Path], 
                   filter_condition: Optional[Dict[str, Any]] = None) -> None:
        """
        Filter data based on conditions and save to output file.
        
        Args:
            input_file (Union[str, Path]): Input file path
            output_file (Union[str, Path]): Output file path
            filter_condition (Optional[Dict[str, Any]]): Filter conditions
            
        Raises:
            DataAnalyzerError: If filtering fails
        """
        input_path = Path(input_file)
        output_path = Path(output_file)
        
        try:
            if input_path.suffix.lower() == '.csv':
                data = self.file_handler.read_csv_file(input_path)
                
                if filter_condition:
                    filtered_data = [row for row in data if self._matches_filter(row, filter_condition)]
                else:
                    # Default filter: remove rows with missing values
                    filtered_data = [row for row in data if all(value for value in row.values())]
                
                self.file_handler.write_csv_file(output_path, filtered_data)
                self.logger.info(f"Filtered {len(data)} rows to {len(filtered_data)} rows")
            else:
                raise DataAnalyzerError(f"Filtering not supported for {input_path.suffix} files")
            
        except Exception as e:
            raise DataAnalyzerError(f"Filtering error: {e}")
    
    def _normalize_csv_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize numeric columns in CSV data."""
        if not data:
            return data
        
        # Find numeric columns
        numeric_columns = []
        for column in data[0].keys():
            try:
                values = [float(row[column]) for row in data if row[column] is not None]
                if values:
                    numeric_columns.append(column)
            except (ValueError, TypeError):
                continue
        
        # Normalize each numeric column
        normalized_data = []
        for row in data:
            new_row = row.copy()
            for column in numeric_columns:
                try:
                    value = float(row[column])
                    # Simple min-max normalization (0-1 range)
                    column_values = [float(r[column]) for r in data if r[column] is not None]
                    min_val, max_val = min(column_values), max(column_values)
                    if max_val != min_val:
                        normalized_value = (value - min_val) / (max_val - min_val)
                        new_row[column] = round(normalized_value, 4)
                except (ValueError, TypeError):
                    pass
            normalized_data.append(new_row)
        
        return normalized_data
    
    def _aggregate_csv_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create aggregated summary of CSV data."""
        if not data:
            return []
        
        summary = []
        for column in data[0].keys():
            values = [row[column] for row in data if row[column] is not None]
            
            row_summary = {"column": column, "non_null_count": len(values)}
            
            # Try numeric aggregation
            try:
                numeric_values = [float(v) for v in values]
                row_summary.update({
                    "min": min(numeric_values),
                    "max": max(numeric_values),
                    "mean": round(statistics.mean(numeric_values), 2),
                    "median": statistics.median(numeric_values)
                })
            except (ValueError, TypeError):
                # Categorical aggregation
                unique_values = len(set(str(v) for v in values))
                row_summary["unique_values"] = unique_values
            
            summary.append(row_summary)
        
        return summary
    
    def _matches_filter(self, row: Dict[str, Any], filter_condition: Dict[str, Any]) -> bool:
        """Check if a row matches the filter condition."""
        for key, condition in filter_condition.items():
            if key not in row:
                return False
            
            value = row[key]
            
            if isinstance(condition, dict):
                # Complex condition like {">=": 10, "<": 100}
                for operator, target in condition.items():
                    if operator == ">=":
                        if not (float(value) >= float(target)):
                            return False
                    elif operator == ">":
                        if not (float(value) > float(target)):
                            return False
                    elif operator == "<=":
                        if not (float(value) <= float(target)):
                            return False
                    elif operator == "<":
                        if not (float(value) < float(target)):
                            return False
                    elif operator == "==":
                        if not (str(value) == str(target)):
                            return False
                    elif operator == "!=":
                        if not (str(value) != str(target)):
                            return False
            else:
                # Simple equality check
                if str(value) != str(condition):
                    return False
        
        return True
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_last_analysis(self) -> Optional[Dict[str, Any]]:
        """Get the results of the last analysis performed."""
        return self._last_analysis
