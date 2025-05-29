#!/usr/bin/env python3
"""
Debug script to investigate RAG search issues.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from code_dev_assistant.rag_system import CodeRAG

async def debug_rag_search():
    """Debug RAG search functionality."""
    print("🔧 Initializing RAG system...")
    rag_system = CodeRAG()
    await rag_system.initialize()
    
    # Check status first
    print("\n📊 Checking RAG status...")
    status_result = await rag_system.execute_rag_tool('rag_status', {})
    print("Status:", status_result[0].text if status_result else "No status")
    
    # Try a very simple search
    print("\n🔍 Testing simple search...")
    try:
        result = await rag_system.execute_rag_tool('search_code', {
            'query': 'function',
            'limit': 3,
            'similarity_threshold': 0.1  # Very low threshold
        })
        print("Simple search result:")
        print(result[0].text if result else "No result")
    except Exception as e:
        print(f"Error in simple search: {e}")
    
    # Try searching for known content
    print("\n🔍 Testing search for known content...")
    try:
        result = await rag_system.execute_rag_tool('search_code', {
            'query': 'CodeAnalyzer',
            'limit': 3,
            'similarity_threshold': 0.1
        })
        print("Known content search result:")
        print(result[0].text if result else "No result")
    except Exception as e:
        print(f"Error in known content search: {e}")
    
    # Check if we can access the database directly
    print("\n🗄️  Checking database directly...")
    try:
        if rag_system.table is not None:
            # Try to get some basic info about the table
            print("Table exists")
            # Get a few records
            try:
                import pandas as pd
                results = rag_system.table.to_pandas().head(3)
                print(f"Sample records: {len(results)} rows")
                if not results.empty:
                    print("Columns:", list(results.columns))
                    print("Sample content:", results['content'].iloc[0][:100] if 'content' in results.columns else "No content column")
                else:
                    print("Table is empty!")
            except Exception as e:
                print(f"Error reading table: {e}")
        else:
            print("Table is None!")
    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == "__main__":
    asyncio.run(debug_rag_search())
