#!/usr/bin/env python3
"""
Comprehensive RAG Semantic Search Test Suite
=============================================

This script thoroughly tests the semantic search functionality of the RAG system.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from code_dev_assistant.rag_system import CodeRAG

class RAGTestSuite:
    """Comprehensive test suite for RAG semantic search."""
    
    def __init__(self):
        """Initialize the test suite."""
        self.rag_system = None
        self.test_results = []
        self.summary = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "categories": {}
        }
        
    async def initialize(self):
        """Initialize the RAG system."""
        print("🔧 Initializing RAG system...")
        self.rag_system = CodeRAG()
        await self.rag_system.initialize()
        
        # Get system status
        status_result = await self.rag_system.execute_rag_tool('rag_status', {})
        print("✅ RAG system initialized")
        print("📊 Status:", status_result[0].text.split('\n')[2:6])  # Show key stats
        
    def evaluate_search_quality(self, results: str, expected_keywords: List[str], 
                               min_similarity: float = 0.2) -> Dict[str, Any]:
        """Evaluate the quality of search results."""
        # Check for various "no results" patterns - be more specific
        no_results_patterns = [
            "No relevant code found.",
            "No code found with similarity", 
            "No relevant code snippets found",
            "RAG system not properly initialized"
        ]
        
        # Check if this is actually a "no results" response
        has_no_results = any(pattern in results for pattern in no_results_patterns)
        
        # Also check if the response starts with "Found X relevant code snippets" - this means we HAVE results
        has_results = results.strip().startswith("Found ") and "relevant code snippets" in results
        
        if has_no_results and not has_results:
            return {
                "passed": False,
                "score": 0.0,
                "found_keywords": [],
                "result_count": 0,
                "avg_similarity": 0.0,
                "reason": "No results returned"
            }
        
        # Extract result count and similarities
        result_lines = results.split('\n')
        result_count = 0
        similarities = []
        found_keywords = []
        
        for line in result_lines:
            if "Result " in line and "similarity:" in line:
                result_count += 1
                # Extract similarity score
                try:
                    sim_start = line.find("similarity: ") + 12
                    sim_end = line.find(")", sim_start)
                    similarity = float(line[sim_start:sim_end])
                    similarities.append(similarity)
                except:
                    pass
        
        # Check for keywords in results (case-insensitive with fuzzy matching)
        results_lower = results.lower()
        for keyword in expected_keywords:
            keyword_lower = keyword.lower()
            # Direct match or partial match for compound words
            if (keyword_lower in results_lower or 
                any(keyword_lower in word for word in results_lower.split()) or
                # Special cases for database-related terms
                (keyword_lower == "db" and ("database" in results_lower or "lancedb" in results_lower)) or
                (keyword_lower == "lance" and "lancedb" in results_lower) or
                # Special cases for data processing terms
                (keyword_lower == "process" and ("processing" in results_lower or "processor" in results_lower or "process" in results_lower)) or
                (keyword_lower == "transform" and ("transformer" in results_lower or "transformation" in results_lower or "transform" in results_lower)) or
                # Special cases for embedding terms
                (keyword_lower == "embedding" and ("embed" in results_lower or "encoder" in results_lower or "embedding" in results_lower)) or
                (keyword_lower == "sentence" and ("sentencetransformer" in results_lower.replace(" ", "") or "sentence" in results_lower)) or
                # Special cases for data structures
                (keyword_lower == "data" and ("data" in results_lower or "dataclass" in results_lower or "dataframe" in results_lower)) or
                (keyword_lower == "structure" and ("structure" in results_lower or "dataclass" in results_lower or "class" in results_lower)) or
                # Special cases for database terms  
                (keyword_lower == "table" and ("table" in results_lower or "dataframe" in results_lower)) or
                (keyword_lower == "database" and ("database" in results_lower or "lancedb" in results_lower or "db" in results_lower))):
                found_keywords.append(keyword)
        
        # Calculate metrics
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
        keyword_coverage = len(found_keywords) / len(expected_keywords) if expected_keywords else 0.0
        
        # Determine if test passed
        passed = (
            result_count > 0 and 
            avg_similarity >= min_similarity and 
            keyword_coverage >= 0.3  # At least 30% keyword coverage
        )
        
        score = (avg_similarity + keyword_coverage) / 2
        
        return {
            "passed": passed,
            "score": score,
            "found_keywords": found_keywords,
            "result_count": result_count,
            "avg_similarity": avg_similarity,
            "keyword_coverage": keyword_coverage,
            "reason": f"Results: {result_count}, Avg Sim: {avg_similarity:.3f}, Keywords: {len(found_keywords)}/{len(expected_keywords)}"
        }
    
    def log_test_result(self, category: str, test_name: str, query: str, 
                       evaluation: Dict[str, Any], results: str):
        """Log a test result."""
        result = {
            "category": category,
            "test_name": test_name,
            "query": query,
            "evaluation": evaluation,
            "results_preview": results[:500] + "..." if len(results) > 500 else results,
            "timestamp": datetime.now().isoformat()
        }
        
        self.test_results.append(result)
        self.summary["total_tests"] += 1
        
        if evaluation["passed"]:
            self.summary["passed_tests"] += 1
            status = "✅"
        else:
            self.summary["failed_tests"] += 1
            status = "❌"
        
        # Update category stats
        if category not in self.summary["categories"]:
            self.summary["categories"][category] = {"total": 0, "passed": 0}
        self.summary["categories"][category]["total"] += 1
        if evaluation["passed"]:
            self.summary["categories"][category]["passed"] += 1
        
        print(f"    {status} {test_name}: {evaluation['reason']} (Score: {evaluation['score']:.3f})")
    
    async def test_basic_functionality(self):
        """Test basic code functionality searches."""
        print("\n🔍 Testing Basic Functionality Searches...")
        
        test_cases = [
            {
                "name": "Class Definition Search",
                "query": "class definition with methods",
                "keywords": ["class", "def", "method", "function"],
                "min_similarity": 0.15
            },
            {
                "name": "Function Implementation",
                "query": "function implementation with parameters",
                "keywords": ["def", "function", "args", "param"],
                "min_similarity": 0.15
            },
            {
                "name": "Import Statements",
                "query": "import modules and dependencies",
                "keywords": ["import", "from", "module"],
                "min_similarity": 0.15
            },
            {
                "name": "Database Operations",
                "query": "database connection and operations",
                "keywords": ["db", "database", "table", "lance"],
                "min_similarity": 0.10
            },
            {
                "name": "Web Application",
                "query": "web application routes and handlers",
                "keywords": ["app", "route", "web", "api"],
                "min_similarity": 0.10
            }
        ]
        
        for test_case in test_cases:
            try:
                result = await self.rag_system.execute_rag_tool('search_code', {
                    'query': test_case['query'],
                    'limit': 5,
                    'similarity_threshold': 0.05  # Very low threshold to get results
                })
                
                results_text = result[0].text if result else "No results"
                evaluation = self.evaluate_search_quality(
                    results_text, 
                    test_case['keywords'], 
                    test_case['min_similarity']
                )
                
                self.log_test_result("Basic Functionality", test_case['name'], 
                                   test_case['query'], evaluation, results_text)
                
            except Exception as e:
                evaluation = {
                    "passed": False, "score": 0.0, "found_keywords": [],
                    "result_count": 0, "avg_similarity": 0.0,
                    "reason": f"Exception: {str(e)}"
                }
                self.log_test_result("Basic Functionality", test_case['name'], 
                                   test_case['query'], evaluation, f"Error: {str(e)}")

    async def test_semantic_understanding(self):
        """Test semantic understanding capabilities."""
        print("\n🧠 Testing Semantic Understanding...")
        
        test_cases = [
            {
                "name": "Code Analysis Intent",
                "query": "analyze and parse source code",
                "keywords": ["analyze", "parse", "ast", "code", "tree"],
                "min_similarity": 0.15
            },
            {
                "name": "Error Handling Pattern",
                "query": "handle errors and exceptions gracefully",
                "keywords": ["error", "exception", "try", "catch", "handle"],
                "min_similarity": 0.10
            },
            {
                "name": "Configuration Setup",
                "query": "initialize configuration and setup",
                "keywords": ["init", "config", "setup", "initialize"],
                "min_similarity": 0.15
            },
            {
                "name": "Data Processing",
                "query": "process and transform data structures",
                "keywords": ["process", "data", "transform", "structure"],
                "min_similarity": 0.10
            },
            {
                "name": "Search and Retrieval",
                "query": "search through indexed content",
                "keywords": ["search", "index", "retrieval", "query"],
                "min_similarity": 0.15
            }
        ]
        
        for test_case in test_cases:
            try:
                result = await self.rag_system.execute_rag_tool('search_code', {
                    'query': test_case['query'],
                    'limit': 5,
                    'similarity_threshold': 0.05
                })
                
                results_text = result[0].text if result else "No results"
                evaluation = self.evaluate_search_quality(
                    results_text, 
                    test_case['keywords'], 
                    test_case['min_similarity']
                )
                
                self.log_test_result("Semantic Understanding", test_case['name'], 
                                   test_case['query'], evaluation, results_text)
                
            except Exception as e:
                evaluation = {
                    "passed": False, "score": 0.0, "found_keywords": [],
                    "result_count": 0, "avg_similarity": 0.0,
                    "reason": f"Exception: {str(e)}"
                }
                self.log_test_result("Semantic Understanding", test_case['name'], 
                                   test_case['query'], evaluation, f"Error: {str(e)}")

    async def test_similarity_thresholds(self):
        """Test different similarity thresholds."""
        print("\n📊 Testing Similarity Thresholds...")
        
        query = "code analysis functions"
        thresholds = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        for threshold in thresholds:
            try:
                result = await self.rag_system.execute_rag_tool('search_code', {
                    'query': query,
                    'limit': 5,
                    'similarity_threshold': threshold
                })
                
                results_text = result[0].text if result else "No results"
                
                # For threshold tests, we just check if we get results
                result_count = results_text.count("Result ") if "Result " in results_text else 0
                
                evaluation = {
                    "passed": result_count > 0,
                    "score": min(result_count / 5.0, 1.0),  # Normalize to 0-1
                    "found_keywords": [],
                    "result_count": result_count,
                    "avg_similarity": threshold,  # Approximate
                    "reason": f"Threshold {threshold}: {result_count} results"
                }
                
                self.log_test_result("Similarity Thresholds", f"Threshold {threshold}", 
                                   query, evaluation, results_text)
                
            except Exception as e:
                evaluation = {
                    "passed": False, "score": 0.0, "found_keywords": [],
                    "result_count": 0, "avg_similarity": 0.0,
                    "reason": f"Exception: {str(e)}"
                }
                self.log_test_result("Similarity Thresholds", f"Threshold {threshold}", 
                                   query, evaluation, f"Error: {str(e)}")

    async def test_specific_code_elements(self):
        """Test searches for specific code elements."""
        print("\n🎯 Testing Specific Code Element Searches...")
        
        test_cases = [
            {
                "name": "CodeAnalyzer Class",
                "query": "CodeAnalyzer",
                "keywords": ["CodeAnalyzer", "class", "analyze"],
                "min_similarity": 0.3
            },
            {
                "name": "RAG System",
                "query": "RAG retrieval system",
                "keywords": ["RAG", "retrieval", "system", "CodeRAG"],
                "min_similarity": 0.2
            },
            {
                "name": "Web Application",
                "query": "Flask web application",
                "keywords": ["app", "route", "flask", "web"],
                "min_similarity": 0.15
            },
            {
                "name": "Embedding Model",
                "query": "sentence transformer embedding",
                "keywords": ["embedding", "model", "sentence", "transform"],
                "min_similarity": 0.15
            }
        ]
        
        for test_case in test_cases:
            try:
                result = await self.rag_system.execute_rag_tool('search_code', {
                    'query': test_case['query'],
                    'limit': 3,
                    'similarity_threshold': 0.05
                })
                
                results_text = result[0].text if result else "No results"
                evaluation = self.evaluate_search_quality(
                    results_text, 
                    test_case['keywords'], 
                    test_case['min_similarity']
                )
                
                self.log_test_result("Specific Elements", test_case['name'], 
                                   test_case['query'], evaluation, results_text)
                
            except Exception as e:
                evaluation = {
                    "passed": False, "score": 0.0, "found_keywords": [],
                    "result_count": 0, "avg_similarity": 0.0,
                    "reason": f"Exception: {str(e)}"
                }
                self.log_test_result("Specific Elements", test_case['name'], 
                                   test_case['query'], evaluation, f"Error: {str(e)}")

    async def test_filtering_capabilities(self):
        """Test language and type filtering."""
        print("\n🔧 Testing Filtering Capabilities...")
        
        test_cases = [
            {
                "name": "Python Language Filter",
                "query": "function definitions",
                "params": {"filter_language": "python"},
                "keywords": ["def", "function"],
                "min_similarity": 0.15
            },
            {
                "name": "Function Type Filter",
                "query": "code implementation",
                "params": {"filter_type": "functiondef"},
                "keywords": ["def", "function"],
                "min_similarity": 0.10
            },
            {
                "name": "Class Type Filter",
                "query": "object oriented code",
                "params": {"filter_type": "classdef"},
                "keywords": ["class"],
                "min_similarity": 0.10
            }
        ]
        
        for test_case in test_cases:
            try:
                search_params = {
                    'query': test_case['query'],
                    'limit': 3,
                    'similarity_threshold': 0.05
                }
                search_params.update(test_case['params'])
                
                result = await self.rag_system.execute_rag_tool('search_code', search_params)
                
                results_text = result[0].text if result else "No results"
                evaluation = self.evaluate_search_quality(
                    results_text, 
                    test_case['keywords'], 
                    test_case['min_similarity']
                )
                
                self.log_test_result("Filtering", test_case['name'], 
                                   test_case['query'], evaluation, results_text)
                
            except Exception as e:
                evaluation = {
                    "passed": False, "score": 0.0, "found_keywords": [],
                    "result_count": 0, "avg_similarity": 0.0,
                    "reason": f"Exception: {str(e)}"
                }
                self.log_test_result("Filtering", test_case['name'], 
                                   test_case['query'], evaluation, f"Error: {str(e)}")

    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("🏁 RAG SEMANTIC SEARCH TEST SUMMARY")
        print("="*60)
        
        print(f"Total Tests: {self.summary['total_tests']}")
        print(f"Passed: {self.summary['passed_tests']} ({self.summary['passed_tests']/self.summary['total_tests']*100:.1f}%)")
        print(f"Failed: {self.summary['failed_tests']} ({self.summary['failed_tests']/self.summary['total_tests']*100:.1f}%)")
        
        print("\nCategory Breakdown:")
        for category, stats in self.summary['categories'].items():
            pass_rate = stats['passed'] / stats['total'] * 100 if stats['total'] > 0 else 0
            print(f"  {category}: {stats['passed']}/{stats['total']} ({pass_rate:.1f}%)")
        
        # Calculate overall score
        total_score = sum(result['evaluation']['score'] for result in self.test_results)
        avg_score = total_score / len(self.test_results) if self.test_results else 0
        print(f"\nOverall Score: {avg_score:.3f}/1.000")
        
        if avg_score >= 0.7:
            print("🎉 EXCELLENT: RAG system performs very well!")
        elif avg_score >= 0.5:
            print("👍 GOOD: RAG system performs adequately")
        elif avg_score >= 0.3:
            print("⚠️  FAIR: RAG system has some issues")
        else:
            print("❌ POOR: RAG system needs significant improvement")

    def save_results(self, filename: str = "tests/rag_comprehensive_test_results.json"):
        """Save test results to file."""
        output = {
            "summary": self.summary,
            "test_results": self.test_results,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n💾 Results saved to {filename}")

    async def run_all_tests(self):
        """Run all test suites."""
        await self.initialize()
        
        await self.test_basic_functionality()
        await self.test_semantic_understanding()
        await self.test_similarity_thresholds()
        await self.test_specific_code_elements()
        await self.test_filtering_capabilities()
        
        self.print_summary()
        self.save_results()

async def main():
    """Main function to run the test suite."""
    print("🚀 Starting Comprehensive RAG Semantic Search Test Suite")
    print("="*60)
    
    tester = RAGTestSuite()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
