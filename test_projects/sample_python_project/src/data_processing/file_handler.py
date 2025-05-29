"""
File Handler Module

This module provides utilities for reading, writing, and manipulating various file formats
including CSV, JSON, XML, and plain text files.
"""

import json
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging


class FileHandlerError(Exception):
    """Custom exception for file handling operations."""
    pass


class FileHandler:
    """
    A utility class for handling various file operations.
    
    Supports reading and writing CSV, JSON, XML, and text files with
    proper error handling and encoding management.
    """
    
    def __init__(self, default_encoding: str = "utf-8"):
        """
        Initialize the file handler.
        
        Args:
            default_encoding (str): Default encoding for file operations
        """
        self.default_encoding = default_encoding
        self.logger = logging.getLogger(__name__)
    
    def read_text_file(self, file_path: Union[str, Path], encoding: Optional[str] = None) -> str:
        """
        Read content from a text file.
        
        Args:
            file_path (Union[str, Path]): Path to the text file
            encoding (Optional[str]): File encoding (uses default if None)
            
        Returns:
            str: File content
            
        Raises:
            FileHandlerError: If file cannot be read
        """
        encoding = encoding or self.default_encoding
        file_path = Path(file_path)
        
        try:
            if not file_path.exists():
                raise FileHandlerError(f"File does not exist: {file_path}")
            
            with open(file_path, 'r', encoding=encoding) as file:
                content = file.read()
            
            self.logger.info(f"Successfully read text file: {file_path}")
            return content
            
        except UnicodeDecodeError as e:
            raise FileHandlerError(f"Encoding error reading file {file_path}: {e}")
        except Exception as e:
            raise FileHandlerError(f"Error reading file {file_path}: {e}")
    
    def write_text_file(self, file_path: Union[str, Path], content: str, 
                       encoding: Optional[str] = None, create_dirs: bool = True) -> None:
        """
        Write content to a text file.
        
        Args:
            file_path (Union[str, Path]): Path to the output file
            content (str): Content to write
            encoding (Optional[str]): File encoding (uses default if None)
            create_dirs (bool): Whether to create parent directories
            
        Raises:
            FileHandlerError: If file cannot be written
        """
        encoding = encoding or self.default_encoding
        file_path = Path(file_path)
        
        try:
            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding=encoding) as file:
                file.write(content)
            
            self.logger.info(f"Successfully wrote text file: {file_path}")
            
        except Exception as e:
            raise FileHandlerError(f"Error writing file {file_path}: {e}")
    
    def read_json_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Read and parse a JSON file.
        
        Args:
            file_path (Union[str, Path]): Path to the JSON file
            
        Returns:
            Dict[str, Any]: Parsed JSON data
            
        Raises:
            FileHandlerError: If file cannot be read or parsed
        """
        file_path = Path(file_path)
        
        try:
            content = self.read_text_file(file_path)
            data = json.loads(content)
            
            self.logger.info(f"Successfully parsed JSON file: {file_path}")
            return data
            
        except json.JSONDecodeError as e:
            raise FileHandlerError(f"Invalid JSON in file {file_path}: {e}")
        except Exception as e:
            raise FileHandlerError(f"Error reading JSON file {file_path}: {e}")
    
    def write_json_file(self, file_path: Union[str, Path], data: Dict[str, Any], 
                       indent: int = 2, create_dirs: bool = True) -> None:
        """
        Write data to a JSON file.
        
        Args:
            file_path (Union[str, Path]): Path to the output file
            data (Dict[str, Any]): Data to write
            indent (int): JSON indentation
            create_dirs (bool): Whether to create parent directories
            
        Raises:
            FileHandlerError: If file cannot be written
        """
        try:
            json_content = json.dumps(data, indent=indent, ensure_ascii=False)
            self.write_text_file(file_path, json_content, create_dirs=create_dirs)
            
            self.logger.info(f"Successfully wrote JSON file: {file_path}")
            
        except Exception as e:
            raise FileHandlerError(f"Error writing JSON file {file_path}: {e}")
    
    def read_csv_file(self, file_path: Union[str, Path], delimiter: str = ',', 
                     has_header: bool = True) -> List[Dict[str, Any]]:
        """
        Read and parse a CSV file.
        
        Args:
            file_path (Union[str, Path]): Path to the CSV file
            delimiter (str): CSV delimiter
            has_header (bool): Whether the CSV has a header row
            
        Returns:
            List[Dict[str, Any]]: List of row dictionaries
            
        Raises:
            FileHandlerError: If file cannot be read or parsed
        """
        file_path = Path(file_path)
        
        try:
            with open(file_path, 'r', encoding=self.default_encoding, newline='') as file:
                if has_header:
                    reader = csv.DictReader(file, delimiter=delimiter)
                    data = list(reader)
                else:
                    reader = csv.reader(file, delimiter=delimiter)
                    data = [{"col_" + str(i): value for i, value in enumerate(row)} 
                           for row in reader]
            
            self.logger.info(f"Successfully read CSV file: {file_path} ({len(data)} rows)")
            return data
            
        except Exception as e:
            raise FileHandlerError(f"Error reading CSV file {file_path}: {e}")
    
    def write_csv_file(self, file_path: Union[str, Path], data: List[Dict[str, Any]], 
                      delimiter: str = ',', create_dirs: bool = True) -> None:
        """
        Write data to a CSV file.
        
        Args:
            file_path (Union[str, Path]): Path to the output file
            data (List[Dict[str, Any]]): Data to write
            delimiter (str): CSV delimiter
            create_dirs (bool): Whether to create parent directories
            
        Raises:
            FileHandlerError: If file cannot be written
        """
        file_path = Path(file_path)
        
        try:
            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if not data:
                raise FileHandlerError("Cannot write empty data to CSV")
            
            fieldnames = data[0].keys()
            
            with open(file_path, 'w', encoding=self.default_encoding, newline='') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=delimiter)
                writer.writeheader()
                writer.writerows(data)
            
            self.logger.info(f"Successfully wrote CSV file: {file_path} ({len(data)} rows)")
            
        except Exception as e:
            raise FileHandlerError(f"Error writing CSV file {file_path}: {e}")
    
    def get_file_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get information about a file.
        
        Args:
            file_path (Union[str, Path]): Path to the file
            
        Returns:
            Dict[str, Any]: File information
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileHandlerError(f"File does not exist: {file_path}")
        
        stat = file_path.stat()
        
        return {
            "path": str(file_path),
            "name": file_path.name,
            "extension": file_path.suffix,
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "is_file": file_path.is_file(),
            "is_directory": file_path.is_dir()
        }
