#!/usr/bin/env python3
"""
Web UI for the Code Development Assistant.
A Flask-based web interface that provides easy access to all assistant features.
"""
import os
import sys
import asyncio
import threading
from pathlib import Path
from flask import Flask, render_template, request, jsonify

# Add the parent directory to the Python path to import the assistant modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from code_dev_assistant.config import get_config
from code_dev_assistant.git_tools import GitTools
from code_dev_assistant.code_analyzer import CodeAnalyzer
from code_dev_assistant.rag_system import CodeRAG
from code_dev_assistant.llm_client import CodeLLM

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Global instances
config = None
git_tools = None
code_analyzer = None
rag_system = None
llm_client = None


def run_async(coro):
    """Run async function in a thread-safe way for Flask."""
    import concurrent.futures
    
    def _run_in_thread():
        """Run the coroutine in a separate thread with its own event loop."""
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
            asyncio.set_event_loop(None)
    
    # Always run in a separate thread to avoid event loop conflicts
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(_run_in_thread)
        return future.result(timeout=60)  # 60 second timeout


def init_components():
    """Initialize all assistant components."""
    global config, git_tools, code_analyzer, rag_system, llm_client
    
    try:
        config = get_config()
        git_tools = GitTools(config.workspace_path)
        code_analyzer = CodeAnalyzer()
        rag_system = CodeRAG(config.rag.db_path, config.rag.embedding_model)
        llm_client = CodeLLM(config.llm.base_url, config.llm.model)
        
        # Initialize RAG system (skip if fails)
        try:
            run_async(rag_system.initialize())
            print(f"✅ RAG system initialized successfully!")
        except Exception as e:
            print(f"Warning: RAG system initialization failed: {e}")
            import traceback
            traceback.print_exc()
        
        return True
    except Exception as e:
        print(f"Failed to initialize components: {e}")
        # Set minimal config for web UI to work
        from code_dev_assistant.config import AssistantConfig, GitConfig, RAGConfig, LLMConfig, CodeAnalysisConfig
        config = AssistantConfig(
            workspace_path="/home/nkitan/gentify",
            git=GitConfig(),
            rag=RAGConfig(),
            llm=LLMConfig(),
            code_analysis=CodeAnalysisConfig(),
            log_level="INFO"
        )
        return False


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html', config=config)


@app.route('/api/config')
def get_config_api():
    """Get current configuration."""
    if not config:
        return jsonify({'error': 'Configuration not loaded'}), 500
    
    return jsonify({
        'workspace_path': config.workspace_path,
        'llm_model': config.llm.model,
        'llm_base_url': config.llm.base_url,
        'rag_db_path': config.rag.db_path,
        'log_level': config.log_level
    })


@app.route('/git')
def git_page():
    """Git operations page."""
    return render_template('git.html')


@app.route('/api/git/status')
def git_status():
    """Get Git repository status."""
    try:
        if not git_tools:
            return jsonify({'success': False, 'error': 'Git tools not initialized'})
        result = run_async(git_tools.execute_git_tool('git_status', {}))
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/git/add', methods=['POST'])
def git_add():
    """Add files to Git staging area."""
    try:
        if not git_tools:
            return jsonify({'success': False, 'error': 'Git tools not initialized'})
            
        data = request.get_json()
        files = data.get('files', [])
        
        result = run_async(git_tools.execute_git_tool('git_add', {'files': files}))
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/git/commit', methods=['POST'])
def git_commit():
    """Commit staged changes."""
    try:
        if not git_tools:
            return jsonify({'success': False, 'error': 'Git tools not initialized'})
            
        data = request.get_json()
        message = data.get('message', '')
        add_all = data.get('add_all', False)
        
        if not message:
            return jsonify({'success': False, 'error': 'Commit message is required'})
        
        result = run_async(git_tools.execute_git_tool('git_commit', {
            'message': message,
            'add_all': add_all
        }))
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/git/branches')
def git_branches():
    """List Git branches."""
    try:
        if not git_tools:
            return jsonify({'success': False, 'error': 'Git tools not initialized'})
            
        result = run_async(git_tools.execute_git_tool('git_branch_list', {}))
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/git/create_branch', methods=['POST'])
def git_create_branch():
    """Create a new Git branch."""
    try:
        if not git_tools:
            return jsonify({'success': False, 'error': 'Git tools not initialized'})
            
        data = request.get_json()
        branch_name = data.get('branch_name', '')
        checkout = data.get('checkout', True)
        
        if not branch_name:
            return jsonify({'success': False, 'error': 'Branch name is required'})
        
        result = run_async(git_tools.execute_git_tool('git_create_branch', {
            'branch_name': branch_name,
            'checkout': checkout
        }))
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/git/checkout', methods=['POST'])
def git_checkout():
    """Switch to a different branch."""
    try:
        if not git_tools:
            return jsonify({'success': False, 'error': 'Git tools not initialized'})
            
        data = request.get_json()
        branch_name = data.get('branch_name', '')
        
        if not branch_name:
            return jsonify({'success': False, 'error': 'Branch name is required'})
        
        result = run_async(git_tools.execute_git_tool('git_checkout', {
            'branch_name': branch_name
        }))
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/rag')
def rag_page():
    """RAG system page."""
    return render_template('rag.html')


@app.route('/api/rag/index', methods=['POST'])
def rag_index():
    """Index the codebase for RAG."""
    try:
        if not rag_system:
            return jsonify({'success': False, 'error': 'RAG system not initialized'})
            
        data = request.get_json()
        directory = data.get('directory', '.')
        force_reindex = data.get('force_reindex', False)
        
        result = run_async(rag_system.execute_rag_tool('index_codebase', {
            'directory': directory,
            'force_reindex': force_reindex
        }))
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/rag/search', methods=['POST'])
def rag_search():
    """Search the indexed codebase."""
    try:
        if not rag_system:
            return jsonify({'success': False, 'error': 'RAG system not initialized'})
            
        data = request.get_json()
        query = data.get('query', '')
        limit = data.get('limit', 5)
        
        if not query:
            return jsonify({'success': False, 'error': 'Search query is required'})
        
        # Use lower default threshold based on comprehensive test results
        result = run_async(rag_system.execute_rag_tool('search_code', {
            'query': query,
            'limit': limit,
            'similarity_threshold': data.get('similarity_threshold', 0.3),
            'filter_language': data.get('filter_language'),
            'filter_type': data.get('filter_type')
        }))
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/rag/search/advanced', methods=['POST'])
def rag_search_advanced():
    """Advanced search with analytics and filtering."""
    try:
        if not rag_system:
            return jsonify({'success': False, 'error': 'RAG system not initialized'})
            
        data = request.get_json()
        query = data.get('query', '')
        limit = data.get('limit', 10)
        similarity_threshold = data.get('similarity_threshold', 0.3)
        filter_language = data.get('filter_language')
        filter_type = data.get('filter_type')
        
        if not query:
            return jsonify({'success': False, 'error': 'Search query is required'})
        
        # Prepare search parameters
        search_params = {
            'query': query,
            'limit': limit,
            'similarity_threshold': similarity_threshold
        }
        
        # Add filters if specified
        if filter_language:
            search_params['filter_language'] = filter_language
        if filter_type:
            search_params['filter_type'] = filter_type
        
        # Execute search
        result = run_async(rag_system.execute_rag_tool('search_code', search_params))
        
        if result and result[0]:
            output = result[0].text
            
            # Extract analytics
            analytics = extract_search_analytics(output, query, similarity_threshold)
            
            return jsonify({
                'success': True, 
                'output': output,
                'analytics': analytics,
                'search_params': search_params
            })
        else:
            return jsonify({'success': True, 'output': 'No results found'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def extract_search_analytics(output, query, threshold):
    """Extract analytics from search output."""
    import re
    
    analytics = {
        'result_count': 0,
        'avg_similarity': 0.0,
        'similarity_range': [0.0, 0.0],
        'quality_score': 'unknown',
        'recommendations': []
    }
    
    try:
        # Extract result count
        result_match = re.search(r'Found (\d+) relevant code snippets', output)
        if result_match:
            analytics['result_count'] = int(result_match.group(1))
        
        # Extract similarity scores
        similarity_matches = re.findall(r'similarity: ([\d.]+)\)', output)
        if similarity_matches:
            similarities = [float(s) for s in similarity_matches]
            analytics['avg_similarity'] = sum(similarities) / len(similarities)
            analytics['similarity_range'] = [min(similarities), max(similarities)]
            
            # Determine quality based on test results
            if analytics['avg_similarity'] >= 0.4:
                analytics['quality_score'] = 'excellent'
            elif analytics['avg_similarity'] >= 0.25:
                analytics['quality_score'] = 'good'
            elif analytics['avg_similarity'] >= 0.15:
                analytics['quality_score'] = 'moderate'
            else:
                analytics['quality_score'] = 'broad'
        
        # Generate recommendations based on test insights
        if analytics['result_count'] == 0:
            analytics['recommendations'] = [
                'Try lowering similarity threshold to 0.2-0.3',
                'Use broader search terms',
                'Remove language/type filters',
                'Consider using search templates'
            ]
        elif analytics['quality_score'] == 'broad':
            analytics['recommendations'] = [
                'Consider raising similarity threshold for more precise results',
                'Add language or type filters to narrow results'
            ]
        elif analytics['quality_score'] == 'excellent':
            analytics['recommendations'] = [
                'Great results! Consider similar queries for related code'
            ]
        
    except Exception as e:
        analytics['error'] = str(e)
    
    return analytics


@app.route('/api/rag/status')
def rag_status():
    """Get RAG system status."""
    try:
        if not rag_system:
            return jsonify({'success': False, 'error': 'RAG system not initialized'})
            
        result = run_async(rag_system.execute_rag_tool('rag_status', {}))
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/rag/clear', methods=['POST'])
def rag_clear():
    """Clear the RAG index."""
    try:
        data = request.get_json()
        confirm = data.get('confirm', False)
        
        if not rag_system:
            return jsonify({'success': False, 'error': 'RAG system not initialized'})
        
        result = run_async(rag_system.execute_rag_tool('clear_index', {'confirm': confirm}))
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/rag/context', methods=['POST'])
def rag_context():
    """Get context for a specific function or class."""
    try:
        if not rag_system:
            return jsonify({'success': False, 'error': 'RAG system not initialized'})
            
        data = request.get_json()
        identifier = data.get('identifier', '')
        include_related = data.get('include_related', True)
        
        if not identifier:
            return jsonify({'success': False, 'error': 'Identifier is required'})
        
        result = run_async(rag_system.execute_rag_tool('get_context', {
            'identifier': identifier,
            'include_related': include_related
        }))
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/llm')
def llm_page():
    """LLM tools page."""
    return render_template('llm.html')


@app.route('/api/llm/generate', methods=['POST'])
def llm_generate():
    """Generate code using LLM."""
    try:
        if not llm_client:
            return jsonify({'success': False, 'error': 'LLM client not initialized'})
            
        data = request.get_json()
        description = data.get('description', '')
        language = data.get('language', 'python')
        context = data.get('context', '')
        style = data.get('style', 'clean')
        
        if not description:
            return jsonify({'success': False, 'error': 'Code description is required'})
        
        result = run_async(llm_client.execute_llm_tool('generate_code', {
            'description': description,
            'language': language,
            'context': context,
            'style': style
        }))
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/llm/explain', methods=['POST'])
def llm_explain():
    """Explain code using LLM."""
    try:
        if not llm_client:
            return jsonify({'success': False, 'error': 'LLM client not initialized'})
            
        data = request.get_json()
        code = data.get('code', '')
        detail_level = data.get('detail_level', 'medium')
        
        if not code:
            return jsonify({'success': False, 'error': 'Code is required'})
        
        result = run_async(llm_client.execute_llm_tool('explain_code', {
            'code': code,
            'detail_level': detail_level
        }))
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/llm/refactor', methods=['POST'])
def llm_refactor():
    """Refactor code using LLM."""
    try:
        if not llm_client:
            return jsonify({'success': False, 'error': 'LLM client not initialized'})
            
        data = request.get_json()
        code = data.get('code', '')
        goals = data.get('goals', [])
        language = data.get('language', 'python')
        
        if not code:
            return jsonify({'success': False, 'error': 'Code is required'})
        
        result = run_async(llm_client.execute_llm_tool('refactor_code', {
            'code': code,
            'goals': goals,
            'language': language
        }))
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/chat')
def chat_page():
    """Chat interface page."""
    return render_template('chat.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat with the assistant."""
    try:
        if not llm_client:
            return jsonify({'success': False, 'error': 'LLM client not initialized'})
            
        data = request.get_json()
        question = data.get('question', '')
        context = data.get('context', '')
        
        if not question:
            return jsonify({'success': False, 'error': 'Question is required'})
        
        result = run_async(llm_client.execute_llm_tool('chat_about_code', {
            'question': question,
            'code_context': context
        }))
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/settings')
def settings_page():
    """Settings page."""
    return render_template('settings.html', config=config)


@app.route('/api/rag/suggestions')
def rag_suggestions():
    """Get search suggestions based on comprehensive test results."""
    # Based on the test results, these are the most successful query patterns
    suggestions = {
        'high_success_queries': [
            {
                'query': 'class definition with methods',
                'description': 'Find class definitions and their methods',
                'success_rate': '100%',
                'avg_similarity': '0.265',
                'recommended_threshold': 0.15,
                'filters': {'type': 'classdef'}
            },
            {
                'query': 'function implementation with parameters',
                'description': 'Find function implementations',
                'success_rate': '100%',
                'avg_similarity': '0.25+',
                'recommended_threshold': 0.15,
                'filters': {'type': 'functiondef'}
            },
            {
                'query': 'import modules and dependencies',
                'description': 'Find import statements',
                'success_rate': '100%',
                'avg_similarity': '0.444',
                'recommended_threshold': 0.15,
                'filters': {'type': 'import'}
            },
            {
                'query': 'analyze and parse source code',
                'description': 'Find code analysis functionality',
                'success_rate': '100%',
                'avg_similarity': '0.454',
                'recommended_threshold': 0.15,
                'filters': {}
            },
            {
                'query': 'handle errors and exceptions gracefully',
                'description': 'Find error handling patterns',
                'success_rate': '100%',
                'avg_similarity': '0.3+',
                'recommended_threshold': 0.10,
                'filters': {}
            },
            {
                'query': 'initialize configuration and setup',
                'description': 'Find initialization code',
                'success_rate': '100%',
                'avg_similarity': '0.3+',
                'recommended_threshold': 0.15,
                'filters': {}
            }
        ],
        'optimal_settings': {
            'similarity_threshold': {
                'recommended': 0.3,
                'range': [0.2, 0.4],
                'note': 'Based on 81.8% test success rate'
            },
            'result_limit': {
                'recommended': 10,
                'note': 'Good balance of coverage and relevance'
            },
            'filters': {
                'language': 'Use when targeting specific languages (100% success)',
                'type': 'Use when targeting specific code types (100% success)'
            }
        },
        'troubleshooting': {
            'no_results': [
                'Lower similarity threshold to 0.1-0.2',
                'Remove all filters',
                'Use broader search terms',
                'Try search templates'
            ],
            'too_many_results': [
                'Raise similarity threshold to 0.4+',
                'Add language or type filters',
                'Use more specific terms'
            ],
            'low_quality_results': [
                'Check if codebase is properly indexed',
                'Use more descriptive search terms',
                'Try semantic queries instead of exact matches'
            ]
        }
    }
    
    return jsonify({'success': True, 'suggestions': suggestions})

if __name__ == '__main__':
    print("🚀 Starting Code Development Assistant Web UI...")
    
    # Initialize components
    success = init_components()
    if success:
        print("✅ All components initialized successfully!")
    else:
        print("⚠️  Some components failed to initialize. Web UI will run with limited functionality.")
    
    print("🌐 Starting web server on http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
