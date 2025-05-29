# RAG System Testing Suite

This folder contains comprehensive tests for the RAG (Retrieval-Augmented Generation) semantic search functionality.

## Test Files

### Core Test Scripts

- **`comprehensive_rag_test.py`** - Main comprehensive test suite with 22 test cases across 5 categories
  - Tests basic functionality, semantic understanding, similarity thresholds, specific elements, and filtering
  - Includes quality evaluation metrics (similarity scores, keyword coverage, result counts)
  - Generates detailed JSON reports with pass/fail status

- **`debug_rag_search.py`** - Debug and verification script for basic RAG functionality
  - Simple test to verify the RAG system is working correctly
  - Good for quick system validation

- **`test_rag_semantic_search.py`** - Original test template
  - Basic semantic search test framework
  - Foundation for more comprehensive testing

### Test Results and Reports

- **`rag_comprehensive_test_results.json`** - Detailed test results from comprehensive test suite
  - Contains all 22 test cases with scores, metrics, and analysis
  - Success rate: 81.8% (18/22 tests passed)

- **`rag_test_results.json`** - Earlier test results from initial testing

- **`RAG_TEST_SUMMARY.md`** - Executive summary report
  - Key findings and recommendations
  - System strengths and improvement areas
  - Optimal similarity threshold recommendations (0.2-0.4)

## How to Run Tests

### Prerequisites
Make sure the RAG system is initialized:
```bash
cd /home/nkitan/gentify
python -c "from src.code_dev_assistant.rag_system import RAGSystem; rag = RAGSystem(); rag.index_directory('src')"
```

### Running Individual Tests

1. **Comprehensive Test Suite** (Recommended):
```bash
cd /home/nkitan/gentify/tests
python comprehensive_rag_test.py
```

2. **Debug/Verification Test**:
```bash
cd /home/nkitan/gentify/tests
python debug_rag_search.py
```

3. **Basic Test**:
```bash
cd /home/nkitan/gentify/tests
python test_rag_semantic_search.py
```

## Test Results Summary

**Overall Performance**: 81.8% success rate (18/22 tests passed)

**System Strengths**:
- Excellent at finding code structures (classes, functions, imports)
- Good semantic understanding of programming concepts
- Reliable basic functionality across similarity thresholds

**Areas for Improvement**:
- Domain-specific terminology recognition
- Specific implementation detail searches
- Complex query handling

**Recommendations**:
- Lower default similarity threshold from 0.7 to 0.3-0.4
- Consider additional preprocessing for domain-specific terms
- Implement query expansion for better coverage

## Database Information

- **Database Path**: `./code_rag_db`
- **Vector Storage**: LanceDB
- **Embedding Model**: all-MiniLM-L6-v2 (sentence-transformers)
- **Indexed Content**: 151 code chunks across 10 files
- **Status**: Ready for production use

## Test Categories

1. **Basic Functionality** (4 tests) - Core search capabilities
2. **Semantic Understanding** (6 tests) - Context and meaning comprehension
3. **Similarity Thresholds** (4 tests) - Threshold optimization
4. **Specific Elements** (4 tests) - Targeted code element searches
5. **Filtering Capabilities** (4 tests) - Advanced filtering and refinement
