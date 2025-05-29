"""
RAG (Retrieval-Augmented Generation) system for codebase understanding.
Uses LanceDB for vector storage and sentence-transformers for embeddings.
"""
import os
import asyncio
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass, asdict
import json

# Check for optional dependencies
DEPENDENCIES_AVAILABLE = True
try:
    import lancedb
    import pandas as pd
    from sentence_transformers import SentenceTransformer
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    # Create stubs for type checking
    if TYPE_CHECKING:
        import lancedb
        import pandas as pd
        from sentence_transformers import SentenceTransformer
    else:
        class SentenceTransformer:
            def __init__(self, *args, **kwargs): 
                pass
            def encode(self, *args, **kwargs): 
                return []
        
        class LanceDBStub:
            @staticmethod
            def connect(*args, **kwargs): 
                return None
            def open_table(self, *args, **kwargs):
                return None
            def create_table(self, *args, **kwargs):
                return None
            def drop_table(self, *args, **kwargs):
                pass
        
        class PandasStub:
            class DataFrame:
                def nunique(self): return 0
                def value_counts(self): return {}
                def empty(self): return True
                def iloc(self): return None
                def iterrows(self): return []
        
        lancedb = LanceDBStub()
        pd = PandasStub()

import mcp.types as types

from .code_analyzer import CodeAnalyzer, CodeChunk


@dataclass
class CodeDocument:
    """Represents a document in the RAG system."""
    id: str
    content: str
    file_path: str
    chunk_type: str
    start_line: int
    end_line: int
    name: Optional[str] = None
    docstring: Optional[str] = None
    language: Optional[str] = None
    embedding: Optional[List[float]] = None
    metadata: Optional[str] = None  # JSON string


class CodeRAG:
    """RAG system for code understanding and retrieval."""
    
    def __init__(self, db_path: str = "./code_rag_db", model_name: str = "all-MiniLM-L6-v2"):
        """Initialize RAG system with LanceDB and sentence transformer."""
        self.db_path = db_path
        self.model_name = model_name
        self.embedding_model = None
        self.db = None
        self.table = None
        self.code_analyzer = CodeAnalyzer()
        self._initialized = False
    
    async def initialize(self):
        """Initialize the RAG system."""
        if self._initialized:
            return
        
        if not DEPENDENCIES_AVAILABLE:
            raise RuntimeError("RAG system dependencies not available. Please install: pip install lancedb pandas sentence-transformers")
        
        try:
            # Initialize embedding model
            self.embedding_model = SentenceTransformer(self.model_name)
            
            # Initialize LanceDB
            self.db = lancedb.connect(self.db_path)
            
            # Try to open existing table or create new one
            try:
                self.table = self.db.open_table("code_chunks")
            except Exception:
                # Create new table with schema
                # First, get the actual embedding dimension from the model
                test_embedding = self.embedding_model.encode(["test"])
                embedding_dim = len(test_embedding[0])
                
                sample_data = [{
                    "id": "sample",
                    "content": "sample code",
                    "file_path": "sample.py",
                    "chunk_type": "function",
                    "start_line": 1,
                    "end_line": 5,
                    "name": "sample_function",
                    "docstring": "Sample docstring",
                    "language": "python",
                    "embedding": [0.0] * embedding_dim,
                    "metadata": "{}"
                }]
                
                # Create table with pandas DataFrame
                df = pd.DataFrame(sample_data)
                self.table = self.db.create_table("code_chunks", df)
                
                # Remove sample data
                self.table.delete("id = 'sample'")
            
            self._initialized = True
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize RAG system: {str(e)}")
    
    def get_rag_tools(self) -> List[types.Tool]:
        """Return list of RAG-related MCP tools."""
        return [
            types.Tool(
                name="index_codebase",
                description="Index the entire codebase for RAG retrieval",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Directory to index",
                            "default": "."
                        },
                        "file_extensions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "File extensions to include",
                            "default": [".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c", ".h"]
                        },
                        "exclude_dirs": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Directories to exclude",
                            "default": [".git", "__pycache__", "node_modules", ".venv", "venv"]
                        },
                        "force_reindex": {
                            "type": "boolean",
                            "description": "Force reindexing even if files haven't changed",
                            "default": False
                        }
                    },
                    "required": [],
                }
            ),
            types.Tool(
                name="search_code",
                description="Search for relevant code using semantic similarity",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language query to search for"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 5
                        },
                        "similarity_threshold": {
                            "type": "number",
                            "description": "Minimum similarity score (0-1)",
                            "default": 0.7
                        },
                        "filter_language": {
                            "type": "string",
                            "description": "Filter results by programming language"
                        },
                        "filter_type": {
                            "type": "string",
                            "description": "Filter results by chunk type (function, class, etc.)"
                        }
                    },
                    "required": ["query"],
                }
            ),
            types.Tool(
                name="get_context",
                description="Get relevant code context for a specific function or class",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "identifier": {
                            "type": "string",
                            "description": "Function or class name to get context for"
                        },
                        "include_related": {
                            "type": "boolean",
                            "description": "Include related functions/classes",
                            "default": True
                        }
                    },
                    "required": ["identifier"],
                }
            ),
            types.Tool(
                name="rag_status",
                description="Get status of the RAG index",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                }
            ),
            types.Tool(
                name="clear_index",
                description="Clear the RAG index",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "confirm": {
                            "type": "boolean",
                            "description": "Confirm deletion of index",
                            "default": False
                        }
                    },
                    "required": [],
                }
            )
        ]
    
    async def execute_rag_tool(self, name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Execute a RAG tool."""
        await self.initialize()
        
        try:
            if name == "index_codebase":
                return await self._index_codebase(
                    arguments.get("directory", "."),
                    arguments.get("file_extensions", [".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c", ".h"]),
                    arguments.get("exclude_dirs", [".git", "__pycache__", "node_modules", ".venv", "venv"]),
                    arguments.get("force_reindex", False)
                )
            elif name == "search_code":
                return await self._search_code(
                    arguments["query"],
                    arguments.get("limit", 5),
                    arguments.get("similarity_threshold", 0.7),
                    arguments.get("filter_language"),
                    arguments.get("filter_type")
                )
            elif name == "get_context":
                return await self._get_context(
                    arguments["identifier"],
                    arguments.get("include_related", True)
                )
            elif name == "rag_status":
                return await self._rag_status()
            elif name == "clear_index":
                return await self._clear_index(arguments.get("confirm", False))
            else:
                raise ValueError(f"Unknown RAG tool: {name}")
        except Exception as e:
            return [types.TextContent(type="text", text=f"RAG operation failed: {str(e)}")]
    
    async def _index_codebase(self, directory: str, file_extensions: List[str], 
                            exclude_dirs: List[str], force_reindex: bool) -> List[types.TextContent]:
        """Index the codebase for RAG retrieval."""
        if not DEPENDENCIES_AVAILABLE or not self._initialized or self.table is None or self.embedding_model is None:
            return [types.TextContent(type="text", text="RAG system not properly initialized")]
        
        try:
            indexed_files = 0
            total_chunks = 0
            search_dir = Path(directory).resolve()
            
            print(f"DEBUG: Indexing directory: {search_dir}")
            print(f"DEBUG: File extensions: {file_extensions}")
            print(f"DEBUG: Exclude dirs: {exclude_dirs}")
            
            # Track existing files to detect deletions
            existing_files = set()
            try:
                for record in self.table.to_pandas().itertuples():
                    existing_files.add(record.file_path)
            except Exception:
                pass  # Table might be empty
            
            current_files = set()
            
            for ext in file_extensions:
                print(f"DEBUG: Looking for files with extension: {ext}")
                for file_path in search_dir.rglob(f"*{ext}"):
                    print(f"DEBUG: Found file: {file_path}")
                    # Skip excluded directories
                    if any(exclude_dir in file_path.parts for exclude_dir in exclude_dirs):
                        print(f"DEBUG: Skipping excluded file: {file_path}")
                        continue
                    
                    file_path_str = str(file_path)
                    current_files.add(file_path_str)
                    
                    # Check if file needs reindexing
                    if not force_reindex and await self._is_file_indexed(file_path_str):
                        print(f"DEBUG: File already indexed: {file_path_str}")
                        continue
                    
                    try:
                        print(f"DEBUG: Processing file: {file_path_str}")
                        # Remove existing chunks for this file
                        if file_path_str in existing_files:
                            self.table.delete(f"file_path = '{file_path_str}'")
                        
                        # Extract and index chunks
                        chunks = await self._extract_and_embed_chunks(file_path_str)
                        print(f"DEBUG: Extracted {len(chunks)} chunks from {file_path_str}")
                        if chunks:
                            # Convert chunks to dict format for LanceDB with proper vector handling
                            chunk_data = []
                            for chunk in chunks:
                                # Convert to dict manually to ensure proper types
                                chunk_data.append({
                                    "id": chunk.id,
                                    "content": chunk.content,
                                    "file_path": chunk.file_path,
                                    "chunk_type": chunk.chunk_type,
                                    "start_line": chunk.start_line,
                                    "end_line": chunk.end_line,
                                    "name": chunk.name,
                                    "docstring": chunk.docstring,
                                    "language": chunk.language,
                                    "embedding": chunk.embedding,  # Keep as list
                                    "metadata": chunk.metadata
                                })
                            
                            # Create DataFrame with proper dtypes
                            df = pd.DataFrame(chunk_data)
                            
                            # Convert embedding column to proper format for LanceDB
                            import pyarrow as pa
                            import numpy as np
                            
                            # Create proper PyArrow schema with fixed-size list for embeddings
                            embedding_dim = len(chunk_data[0]['embedding'])
                            schema = pa.schema([
                                ('id', pa.string()),
                                ('content', pa.string()),
                                ('file_path', pa.string()),
                                ('chunk_type', pa.string()),
                                ('start_line', pa.int64()),
                                ('end_line', pa.int64()),
                                ('name', pa.string()),
                                ('docstring', pa.string()),
                                ('language', pa.string()),
                                ('embedding', pa.list_(pa.float32(), embedding_dim)),
                                ('metadata', pa.string())
                            ])
                            
                            # Convert to PyArrow table with explicit schema
                            table = pa.Table.from_pandas(df, schema=schema)
                            
                            # Add to database
                            self.table.add(table)
                            
                            indexed_files += 1
                            total_chunks += len(chunks)
                            
                    except Exception as e:
                        print(f"Error indexing {file_path}: {e}")
                        continue
            
            # Remove chunks for deleted files
            deleted_files = existing_files - current_files
            for deleted_file in deleted_files:
                self.table.delete(f"file_path = '{deleted_file}'")
            
            result = f"Indexing complete!\n"
            result += f"Indexed {indexed_files} files\n"
            result += f"Created {total_chunks} code chunks\n"
            if deleted_files:
                result += f"Removed {len(deleted_files)} deleted files"
            
            return [types.TextContent(type="text", text=result)]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Failed to index codebase: {str(e)}")]
    
    async def _extract_and_embed_chunks(self, file_path: str) -> List[CodeDocument]:
        """Extract and embed code chunks from a file."""
        if not DEPENDENCIES_AVAILABLE or not self.embedding_model:
            return []
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract chunks using code analyzer
            ext = Path(file_path).suffix.lower()
            if ext == '.py':
                raw_chunks = self.code_analyzer._extract_python_chunks(file_path, content, 2000)
            else:
                raw_chunks = self.code_analyzer._extract_generic_chunks(file_path, content, 2000)
            
            # Convert to CodeDocument and add embeddings
            documents = []
            for chunk in raw_chunks:
                # Create embedding text (combine content with metadata)
                embedding_text = chunk.content
                if chunk.name:
                    embedding_text = f"{chunk.name}\n{embedding_text}"
                if chunk.docstring:
                    embedding_text = f"{embedding_text}\n{chunk.docstring}"
                
                # Generate embedding - handle both numpy and list return types
                embedding_result = self.embedding_model.encode(embedding_text)
                if hasattr(embedding_result, 'tolist'):
                    embedding = embedding_result.tolist()
                else:
                    embedding = [float(x) for x in embedding_result]  # Ensure float type
                
                # Create document ID
                doc_id = hashlib.md5(f"{file_path}:{chunk.start_line}:{chunk.end_line}".encode()).hexdigest()
                
                doc = CodeDocument(
                    id=doc_id,
                    content=chunk.content,
                    file_path=file_path,
                    chunk_type=chunk.chunk_type,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    name=chunk.name,
                    docstring=chunk.docstring,
                    language=chunk.language,
                    embedding=embedding,
                    metadata=json.dumps({
                        "file_size": len(content),
                        "chunk_size": len(chunk.content)
                    })
                )
                
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            print(f"Error extracting chunks from {file_path}: {e}")
            return []
    
    async def _is_file_indexed(self, file_path: str) -> bool:
        """Check if a file is already indexed and up to date."""
        if not DEPENDENCIES_AVAILABLE or not self.table:
            return False
            
        try:
            # Check if file exists in index
            results = self.table.search().where(f"file_path = '{file_path}'").limit(1).to_pandas()
            if results.empty:
                return False
            
            # Check if file modification time is newer than index
            file_mtime = os.path.getmtime(file_path)
            # For simplicity, we'll reindex if we can't determine the index time
            # In a production system, you'd store indexing timestamps
            
            return False  # For now, always reindex to be safe
            
        except Exception:
            return False
    
    async def _search_code(self, query: str, limit: int, similarity_threshold: float,
                          filter_language: Optional[str], filter_type: Optional[str]) -> List[types.TextContent]:
        """Search for code using semantic similarity."""
        if not DEPENDENCIES_AVAILABLE or not self._initialized or self.table is None or self.embedding_model is None:
            return [types.TextContent(type="text", text="RAG system not properly initialized")]
            
        try:
            # Generate query embedding - handle both numpy and list return types
            embedding_result = self.embedding_model.encode(query)
            if hasattr(embedding_result, 'tolist'):
                query_embedding = embedding_result.tolist()
            else:
                query_embedding = [float(x) for x in embedding_result]  # Ensure float type
            
            # Build search - specify the vector column name
            search = self.table.search(query_embedding, vector_column_name="embedding").limit(limit * 2)  # Get more for filtering
            
            # Apply filters
            where_clauses = []
            if filter_language:
                where_clauses.append(f"language = '{filter_language}'")
            if filter_type:
                where_clauses.append(f"chunk_type = '{filter_type}'")
            
            if where_clauses:
                search = search.where(" AND ".join(where_clauses))
            
            # Execute search
            results = search.to_pandas()
            
            if results.empty:
                return [types.TextContent(type="text", text="No relevant code found.")]
            
            # Filter by similarity threshold and format results
            filtered_results = []
            for _, row in results.iterrows():
                # LanceDB returns _distance, convert to similarity (1 - normalized_distance)
                similarity = 1 - (row['_distance'] / 2)  # Assuming cosine distance
                
                if similarity >= similarity_threshold:
                    filtered_results.append((row, similarity))
            
            # Sort by similarity
            filtered_results.sort(key=lambda x: x[1], reverse=True)
            filtered_results = filtered_results[:limit]
            
            if not filtered_results:
                return [types.TextContent(type="text", text=f"No code found with similarity >= {similarity_threshold}")]
            
            # Format response
            response_lines = [f"Found {len(filtered_results)} relevant code snippets:\n"]
            
            for i, (row, similarity) in enumerate(filtered_results, 1):
                response_lines.append(f"Result {i} (similarity: {similarity:.3f}):")
                response_lines.append(f"File: {row['file_path']}")
                response_lines.append(f"Type: {row['chunk_type']}")
                if row['name']:
                    response_lines.append(f"Name: {row['name']}")
                response_lines.append(f"Lines: {row['start_line']}-{row['end_line']}")
                if row['docstring']:
                    response_lines.append(f"Description: {row['docstring']}")
                response_lines.append("Code:")
                response_lines.append("```")
                response_lines.append(row['content'])
                response_lines.append("```\n")
            
            return [types.TextContent(type="text", text="\n".join(response_lines))]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Search failed: {str(e)}")]
    
    async def _get_context(self, identifier: str, include_related: bool) -> List[types.TextContent]:
        """Get context for a specific function or class."""
        if not DEPENDENCIES_AVAILABLE or not self._initialized or self.table is None:
            return [types.TextContent(type="text", text="RAG system not properly initialized")]
            
        try:
            # Search for the identifier by name
            results = self.table.search().where(f"name = '{identifier}'").to_pandas()
            
            if results.empty:
                return [types.TextContent(type="text", text=f"No code found for identifier: {identifier}")]
            
            response_lines = [f"Context for '{identifier}':\n"]
            
            # Show direct matches
            for _, row in results.iterrows():
                response_lines.append(f"Found in: {row['file_path']}")
                response_lines.append(f"Type: {row['chunk_type']}")
                response_lines.append(f"Lines: {row['start_line']}-{row['end_line']}")
                if row['docstring']:
                    response_lines.append(f"Description: {row['docstring']}")
                response_lines.append("Code:")
                response_lines.append("```")
                response_lines.append(row['content'])
                response_lines.append("```\n")
            
            # If requested, find related code
            if include_related and not results.empty:
                # Use the first result to find related code in the same file
                first_result = results.iloc[0]
                file_path = first_result['file_path']
                
                related_results = self.table.search().where(
                    f"file_path = '{file_path}' AND name != '{identifier}'"
                ).limit(3).to_pandas()
                
                if not related_results.empty:
                    response_lines.append("Related code in the same file:")
                    for _, row in related_results.iterrows():
                        response_lines.append(f"- {row['name']} ({row['chunk_type']}, lines {row['start_line']}-{row['end_line']})")
            
            return [types.TextContent(type="text", text="\n".join(response_lines))]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Failed to get context: {str(e)}")]
    
    async def _rag_status(self) -> List[types.TextContent]:
        """Get RAG system status."""
        if not DEPENDENCIES_AVAILABLE:
            return [types.TextContent(type="text", text="RAG system dependencies not available")]
        
        if not self._initialized or self.table is None:
            return [types.TextContent(type="text", text="RAG system not properly initialized")]
            
        try:
            # Get table stats
            table_df = self.table.to_pandas()
            total_records = len(table_df)
            
            # Get file statistics
            unique_files = table_df['file_path'].nunique() if not table_df.empty else 0
            
            # Get language statistics
            language_counts = table_df['language'].value_counts().to_dict() if not table_df.empty else {}
            
            # Get chunk type statistics
            type_counts = table_df['chunk_type'].value_counts().to_dict() if not table_df.empty else {}
            
            status_lines = [
                "RAG System Status:",
                "=" * 30,
                f"Total code chunks: {total_records}",
                f"Unique files indexed: {unique_files}",
                f"Database path: {self.db_path}",
                f"Embedding model: {self.model_name}",
                ""
            ]
            
            if language_counts:
                status_lines.append("Languages:")
                for lang, count in language_counts.items():
                    status_lines.append(f"  {lang}: {count} chunks")
                status_lines.append("")
            
            if type_counts:
                status_lines.append("Chunk types:")
                for chunk_type, count in type_counts.items():
                    status_lines.append(f"  {chunk_type}: {count} chunks")
            
            return [types.TextContent(type="text", text="\n".join(status_lines))]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Failed to get status: {str(e)}")]
    
    async def _clear_index(self, confirm: bool) -> List[types.TextContent]:
        """Clear the RAG index."""
        if not DEPENDENCIES_AVAILABLE or not self.db:
            return [types.TextContent(type="text", text="RAG system not properly initialized")]
            
        if not confirm:
            return [types.TextContent(
                type="text", 
                text="Index clear cancelled. Use 'confirm: true' to actually clear the index."
            )]
        
        try:
            # Drop and recreate table
            self.db.drop_table("code_chunks")
            
            # Recreate empty table with correct schema
            if self.embedding_model:
                # Get the actual embedding dimension from the model
                test_embedding = self.embedding_model.encode(["test"])
                embedding_dim = len(test_embedding[0])
            else:
                embedding_dim = 384  # Default dimension for all-MiniLM-L6-v2
            
            sample_data = [{
                "id": "sample",
                "content": "sample code",
                "file_path": "sample.py", 
                "chunk_type": "function",
                "start_line": 1,
                "end_line": 5,
                "name": "sample_function",
                "docstring": "Sample docstring",
                "language": "python",
                "embedding": [0.0] * embedding_dim,
                "metadata": "{}"
            }]
            
            # Create table with pandas DataFrame
            import pyarrow as pa
            df = pd.DataFrame(sample_data)
            
            # Create proper PyArrow schema with fixed-size list for embeddings
            schema = pa.schema([
                ('id', pa.string()),
                ('content', pa.string()),
                ('file_path', pa.string()),
                ('chunk_type', pa.string()),
                ('start_line', pa.int64()),
                ('end_line', pa.int64()),
                ('name', pa.string()),
                ('docstring', pa.string()),
                ('language', pa.string()),
                ('embedding', pa.list_(pa.float32(), embedding_dim)),
                ('metadata', pa.string())
            ])
            
            # Convert to PyArrow table with explicit schema
            table = pa.Table.from_pandas(df, schema=schema)
            self.table = self.db.create_table("code_chunks", table)
            self.table.delete("id = 'sample'")
            
            return [types.TextContent(type="text", text="RAG index cleared successfully.")]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Failed to clear index: {str(e)}")]