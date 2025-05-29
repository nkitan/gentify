#!/usr/bin/env python3
"""
Comprehensive test suite for RAG system semantic search functionality.
Tests various search scenarios and evaluates the quality of semantic matching.
"""

import asyncio
import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from code_dev_assistant.rag_system import CodeRAG


class RAGSemanticSearchTester:
    """Test suite for RAG semantic search functionality."""
    
    def __init__(self):
        """Initialize the tester."""
        self.rag_system = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    async def initialize(self):
        """Initialize the RAG system."""
        print("🔧 Initializing RAG system...")
        self.rag_system = CodeRAG()
        await self.rag_system.initialize()
        print("✅ RAG system initialized successfully")
        
    def log_test_result(self, test_name: str, query: str, results: str, 
                       expected_concepts: List[str], passed: bool, notes: str = ""):
        """Log a test result."""
        self.test_results.append({
            "test_name": test_name,
            "query": query,
            "results": results,
            "expected_concepts": expected_concepts,
            "passed": passed,
            "notes": notes,
            "timestamp": datetime.now().isoformat()
        })
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
    
    def evaluate_search_results(self, results: str, expected_concepts: List[str], 
                               min_results: int = 1) -> Tuple[bool, str]:
        """Evaluate if search results contain expected concepts."""
        if "No relevant code found" in results or "No code found" in results:
            return False, "No results returned"
        
        # Count how many expected concepts are found
        found_concepts = []
        for concept in expected_concepts:
            if concept.lower() in results.lower():
                found_concepts.append(concept)
        
        # Check if we have minimum results
        result_count = results.count("Result ")
        if result_count < min_results:
            return False, f"Insufficient results: {result_count} < {min_results}"
        
        # Success if at least 50% of expected concepts are found
        success_ratio = len(found_concepts) / len(expected_concepts)
        if success_ratio >= 0.5:
            return True, f"Found {len(found_concepts)}/{len(expected_concepts)} concepts: {found_concepts}"
        else:
            return False, f"Only found {len(found_concepts)}/{len(expected_concepts)} concepts: {found_concepts}"

    async def test_basic_functionality_search(self):
        """Test basic functionality searches."""
        print("\n📋 Testing Basic Functionality Searches...")
        
        test_cases = [
            {
                "name": "Database Operations",
                "query": "database operations and connections",
                "expected": ["database", "db", "connect", "table", "lance"],
                "min_results": 1
            },
            {
                "name": "File Analysis",
                "query": "analyze code files and extract functions",
                "expected": ["analyze", "file", "function", "extract", "ast"],
                "min_results": 2
            },
            {
                "name": "Web Interface",
                "query": "web application routes and endpoints",
                "expected": ["route", "app", "endpoint", "api", "web"],
                "min_results": 1
            },
            {
                "name": "Git Operations",
                "query": "git version control operations",
                "expected": ["git", "commit", "branch", "repository"],
                "min_results": 1
            }
        ]
        
        for test_case in test_cases:
            print(f"  🔍 Testing: {test_case['name']}")
            try:
                result = await self.rag_system.execute_rag_tool('search_code', {
                    'query': test_case['query'],
                    'limit': 5,
                    'similarity_threshold': 0.6
                })
                
                results_text = result[0].text if result else "No results"
                passed, notes = self.evaluate_search_results(
                    results_text, 
                    test_case['expected'], 
                    test_case['min_results']
                )
                
                status = "✅" if passed else "❌"
                print(f"    {status} {test_case['name']}: {notes}")
                
                self.log_test_result(
                    test_case['name'],
                    test_case['query'],
                    results_text,
                    test_case['expected'],
                    passed,
                    notes
                )
                
            except Exception as e:
                print(f"    ❌ {test_case['name']}: Error - {str(e)}")
                self.log_test_result(
                    test_case['name'],
                    test_case['query'],
                    f"Error: {str(e)}",
                    test_case['expected'],
                    False,
                    f"Exception: {str(e)}"
                )

    async def test_semantic_understanding(self):
        """Test semantic understanding capabilities."""
        print("\n🧠 Testing Semantic Understanding...")
        
        test_cases = [
            {
                "name": "Natural Language Query",
                "query": "functions that handle user authentication and login",
                "expected": ["function", "user", "auth", "login", "handle"],
                "min_results": 1
            },
            {
                "name": "Code Pattern Recognition",
                "query": "error handling and exception management",
                "expected": ["error", "exception", "try", "catch", "handle"],
                "min_results": 1
            },
            {
                "name": "Data Processing",
                "query": "parse and process data structures",
                "expected": ["parse", "process", "data", "structure"],
                "min_results": 1
            },
            {
                "name": "Configuration Management",
                "query": "configuration setup and initialization",
                "expected": ["config", "setup", "init", "configure"],
                "min_results": 1
            }
        ]
        
        for test_case in test_cases:
            print(f"  🔍 Testing: {test_case['name']}")
            try:
                result = await self.rag_system.execute_rag_tool('search_code', {
                    'query': test_case['query'],
                    'limit': 5,
                    'similarity_threshold': 0.5  # Lower threshold for semantic matching
                })
                
                results_text = result[0].text if result else "No results"
                passed, notes = self.evaluate_search_results(
                    results_text, 
                    test_case['expected'], 
                    test_case['min_results']
                )
                
                status = "✅" if passed else "❌"
                print(f"    {status} {test_case['name']}: {notes}")
                
                self.log_test_result(
                    test_case['name'],
                    test_case['query'],
                    results_text,
                    test_case['expected'],
                    passed,
                    notes
                )
                
            except Exception as e:
                print(f"    ❌ {test_case['name']}: Error - {str(e)}")
                self.log_test_result(
                    test_case['name'],
                    test_case['query'],
                    f"Error: {str(e)}",
                    test_case['expected'],
                    False,
                    f"Exception: {str(e)}"
                )

    async def test_similarity_thresholds(self):
        """Test different similarity thresholds."""
        print("\n📊 Testing Similarity Thresholds...")
        
        query = "code analysis and parsing"
        thresholds = [0.9, 0.8, 0.7, 0.6, 0.5]
        
        for threshold in thresholds:
            print(f"  🎯 Testing threshold: {threshold}")
            try:
                result = await self.rag_system.execute_rag_tool('search_code', {
                    'query': query,
                    'limit': 5,
                    'similarity_threshold': threshold
                })
                
                results_text = result[0].text if result else "No results"
                result_count = results_text.count("Result ") if "Result " in results_text else 0
                
                if "No code found" in results_text or result_count == 0:
                    status = "❌"
                    notes = "No results"
                else:
                    status = "✅"
                    notes = f"{result_count} results found"
                
                print(f"    {status} Threshold {threshold}: {notes}")
                
                self.log_test_result(
                    f"Threshold {threshold}",
                    query,
                    results_text,
                    ["analysis", "parsing"],
                    result_count > 0,
                    notes
                )
                
            except Exception as e:
                print(f"    ❌ Threshold {threshold}: Error - {str(e)}")
                self.log_test_result(
                    f"Threshold {threshold}",
                    query,
                    f"Error: {str(e)}",
                    ["analysis", "parsing"],
                    False,
                    f"Exception: {str(e)}"
                )

    async def test_language_filtering(self):
        """Test language-specific filtering."""
        print("\n🔤 Testing Language Filtering...")
        
        test_cases = [
            {
                "name": "Python Filter",
                "query": "class definitions",
                "filter_language": "python",
                "expected": ["class", "def", "python"]
            },
            {
                "name": "No Filter",
                "query": "class definitions",
                "filter_language": None,
                "expected": ["class", "def"]
            }
        ]
        
        for test_case in test_cases:
            print(f"  🔍 Testing: {test_case['name']}")
            try:
                search_params = {
                    'query': test_case['query'],
                    'limit': 5,
                    'similarity_threshold': 0.6
                }
                
                if test_case['filter_language']:
                    search_params['filter_language'] = test_case['filter_language']
                
                result = await self.rag_system.execute_rag_tool('search_code', search_params)
                
                results_text = result[0].text if result else "No results"
                passed, notes = self.evaluate_search_results(
                    results_text, 
                    test_case['expected'], 
                    1
                )
                
                status = "✅" if passed else "❌"
                print(f"    {status} {test_case['name']}: {notes}")
                
                self.log_test_result(
                    test_case['name'],
                    test_case['query'],
                    results_text,
                    test_case['expected'],
                    passed,
                    notes
                )
                
            except Exception as e:
                print(f"    ❌ {test_case['name']}: Error - {str(e)}")
                self.log_test_result(
                    test_case['name'],
                    test_case['query'],
                    f"Error: {str(e)}",
                    test_case['expected'],
                    False,
                    f"Exception: {str(e)}"
                )

    async def test_chunk_type_filtering(self):
        """Test chunk type filtering."""
        print("\n📦 Testing Chunk Type Filtering...")
        
        test_cases = [
            {
                "name": "Function Filter",
                "query": "code implementation",
                "filter_type": "functiondef",
                "expected": ["def", "function"]
            },
            {
                "name": "Class Filter", 
                "query": "object definitions",
                "filter_type": "classdef",
                "expected": ["class"]
            },
            {
                "name": "Import Filter",
                "query": "dependencies",
                "filter_type": "imports",
                "expected": ["import", "from"]
            }
        ]
        
        for test_case in test_cases:
            print(f"  🔍 Testing: {test_case['name']}")
            try:
                result = await self.rag_system.execute_rag_tool('search_code', {
                    'query': test_case['query'],
                    'limit': 5,
                    'similarity_threshold': 0.5,
                    'filter_type': test_case['filter_type']
                })
                
                results_text = result[0].text if result else "No results"
                passed, notes = self.evaluate_search_results(
                    results_text, 
                    test_case['expected'], 
                    1
                )
                
                status = "✅" if passed else "❌"
                print(f"    {status} {test_case['name']}: {notes}")
                
                self.log_test_result(
                    test_case['name'],
                    test_case['query'],
                    results_text,
                    test_case['expected'],
                    passed,
                    notes
                )
                
            except Exception as e:
                print(f"    ❌ {test_case['name']}: Error - {str(e)}")
                self.log_test_result(
                    test_case['name'],
                    test_case['query'],
                    f"Error: {str(e)}",
                    test_case['expected'],
                    False,
                    f"Exception: {str(e)}"
                )

    async def test_edge_cases(self):
        """Test edge cases and error handling."""
        print("\n⚠️  Testing Edge Cases...")
        
        test_cases = [
            {
                "name": "Empty Query",
                "query": "",
                "expected_error": True
            },
            {
                "name": "Very Specific Query",
                "query": "async def _find_class implementation with search_path parameter",
                "expected_error": False
            },
            {
                "name": "Nonsense Query",
                "query": "xyzabc123 nonexistent blahblah",
                "expected_error": False  # Should return no results, not error
            },
            {
                "name": "High Similarity Threshold",
                "query": "function definition",
                "similarity_threshold": 0.95,
                "expected_error": False
            }
        ]
        
        for test_case in test_cases:
            print(f"  🔍 Testing: {test_case['name']}")
            try:
                search_params = {
                    'query': test_case['query'],
                    'limit': 5,
                    'similarity_threshold': test_case.get('similarity_threshold', 0.7)
                }
                
                result = await self.rag_system.execute_rag_tool('search_code', search_params)
                results_text = result[0].text if result else "No results"
                
                if test_case['expected_error']:
                    # For empty query, we expect an error or no results
                    if "error" in results_text.lower() or "No relevant code found" in results_text:
                        passed = True
                        notes = "Properly handled edge case"
                    else:
                        passed = False
                        notes = "Expected error or no results"
                else:
                    # For valid queries, we expect either results or "no results" message
                    if "failed" in results_text.lower() and "error" in results_text.lower():
                        passed = False
                        notes = "Unexpected error"
                    else:
                        passed = True
                        notes = "Query processed successfully"
                
                status = "✅" if passed else "❌"
                print(f"    {status} {test_case['name']}: {notes}")
                
                self.log_test_result(
                    test_case['name'],
                    test_case['query'],
                    results_text,
                    [],
                    passed,
                    notes
                )
                
            except Exception as e:
                if test_case['expected_error']:
                    print(f"    ✅ {test_case['name']}: Expected error - {str(e)}")
                    self.log_test_result(
                        test_case['name'],
                        test_case['query'],
                        f"Error: {str(e)}",
                        [],
                        True,
                        f"Expected exception: {str(e)}"
                    )
                else:
                    print(f"    ❌ {test_case['name']}: Unexpected error - {str(e)}")
                    self.log_test_result(
                        test_case['name'],
                        test_case['query'],
                        f"Error: {str(e)}",
                        [],
                        False,
                        f"Unexpected exception: {str(e)}"
                    )

    async def test_performance(self):
        """Test search performance."""
        print("\n⚡ Testing Performance...")
        
        import time
        
        queries = [
            "function definitions and implementations",
            "class structure and methods",
            "database operations and queries",
            "error handling and exceptions",
            "configuration and setup"
        ]
        
        total_time = 0
        successful_searches = 0
        
        for i, query in enumerate(queries, 1):
            print(f"  🔍 Performance test {i}/5: {query[:30]}...")
            try:
                start_time = time.time()
                
                result = await self.rag_system.execute_rag_tool('search_code', {
                    'query': query,
                    'limit': 5,
                    'similarity_threshold': 0.6
                })
                
                end_time = time.time()
                search_time = end_time - start_time
                total_time += search_time
                
                results_text = result[0].text if result else "No results"
                has_results = "Result " in results_text
                
                if has_results:
                    successful_searches += 1
                    status = "✅"
                else:
                    status = "⚠️"
                
                print(f"    {status} Search {i}: {search_time:.3f}s {'(results found)' if has_results else '(no results)'}")
                
                self.log_test_result(
                    f"Performance Test {i}",
                    query,
                    results_text,
                    [],
                    has_results,
                    f"Search time: {search_time:.3f}s"
                )
                
            except Exception as e:
                print(f"    ❌ Search {i}: Error - {str(e)}")
                self.log_test_result(
                    f"Performance Test {i}",
                    query,
                    f"Error: {str(e)}",
                    [],
                    False,
                    f"Performance test failed: {str(e)}"
                )
        
        avg_time = total_time / len(queries) if queries else 0
        success_rate = (successful_searches / len(queries)) * 100 if queries else 0
        
        print(f"  📊 Performance Summary:")
        print(f"    • Average search time: {avg_time:.3f}s")
        print(f"    • Success rate: {success_rate:.1f}% ({successful_searches}/{len(queries)})")
        print(f"    • Total time: {total_time:.3f}s")

    def save_test_results(self):
        """Save test results to a JSON file."""
        results_file = Path(__file__).parent / "tests/rag_test_results.json"
        
        summary = {
            "test_summary": {
                "total_tests": self.total_tests,
                "passed_tests": self.passed_tests,
                "failed_tests": self.total_tests - self.passed_tests,
                "success_rate": (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0,
                "timestamp": datetime.now().isoformat()
            },
            "detailed_results": self.test_results
        }
        
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n💾 Test results saved to: {results_file}")

    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("🎯 RAG SEMANTIC SEARCH TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        
        if self.total_tests > 0:
            success_rate = (self.passed_tests / self.total_tests) * 100
            print(f"Success Rate: {success_rate:.1f}%")
            
            if success_rate >= 80:
                print("🎉 EXCELLENT: RAG system is performing very well!")
            elif success_rate >= 60:
                print("👍 GOOD: RAG system is performing adequately")
            elif success_rate >= 40:
                print("⚠️  FAIR: RAG system needs improvement")
            else:
                print("❌ POOR: RAG system requires significant fixes")
        
        print("="*60)

    async def run_all_tests(self):
        """Run all test suites."""
        print("🚀 Starting RAG Semantic Search Tests")
        print("="*60)
        
        await self.initialize()
        
        # Run all test suites
        await self.test_basic_functionality_search()
        await self.test_semantic_understanding()
        await self.test_similarity_thresholds()
        await self.test_language_filtering()
        await self.test_chunk_type_filtering()
        await self.test_edge_cases()
        await self.test_performance()
        
        # Generate summary and save results
        self.print_summary()
        self.save_test_results()


async def main():
    """Main test runner."""
    tester = RAGSemanticSearchTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
