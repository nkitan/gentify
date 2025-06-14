#!/usr/bin/env python3
#!/usr/bin/env python3
"""
Web UI for the Code Development Assistant.
A Flask-based web interface that provides easy access to all assistant features.
"""
import os
import sys
import asyncio
import threading
import concurrent.futures
import traceback
import json
import re
from pathlib import Path
from flask import Flask, render_template, request, jsonify

# Add the parent directory to the Python path to import the assistant modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import logging system first
from code_dev_assistant.logger import get_logger, setup_application_logging, log_function_calls

# Configure comprehensive logging for all components
# Use centralized logs directory
import os
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")

app_loggers = setup_application_logging(
    log_level="DEBUG",
    log_directory=log_dir,
    enable_structured_logging=True,
    enable_performance_tracking=True
)

# Get specific loggers for different components
web_ui_logger = app_loggers["web_ui"]
git_logger = app_loggers["git"]
rag_logger = app_loggers["rag"]
llm_logger = app_loggers["llm"]
agent_logger = app_loggers["coder_agent"]
main_logger = app_loggers["main"]

# Import the config first
from code_dev_assistant.config import get_config

# Delay heavy imports to runtime to avoid startup hanging
# from code_dev_assistant.git_tools import GitTools
# from code_dev_assistant.code_analyzer import CodeAnalyzer
# from code_dev_assistant.rag_system import CodeRAG
# from code_dev_assistant.llm_client import CodeLLM
# from code_dev_assistant.coder_agent import CoderAgent

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Global instances
config = None
git_tools = None
code_analyzer = None
rag_system = None
llm_client = None
coder_agent = None

# Store the current workspace path
current_workspace_path = None


@log_function_calls(web_ui_logger)
def run_async(coro):
    """Run async function in a thread-safe way for Flask."""
    web_ui_logger.debug(f"Starting async operation: {type(coro).__name__}")
    import concurrent.futures
    
    def _run_in_thread():
        """Run the coroutine in a separate thread with its own event loop."""
        thread_id = threading.get_ident()
        web_ui_logger.debug(f"Running coroutine in thread {thread_id}")
        
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(coro)
            web_ui_logger.debug(f"Async operation completed successfully in thread {thread_id}")
            return result
        except Exception as e:
            web_ui_logger.exception(f"Async operation failed in thread {thread_id}")
            raise
        finally:
            loop.close()
            asyncio.set_event_loop(None)
            web_ui_logger.debug(f"Event loop closed for thread {thread_id}")
    
    # Always run in a separate thread to avoid event loop conflicts
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(_run_in_thread)
        try:
            result = future.result(timeout=300)  # 5 minute timeout for complex operations
            web_ui_logger.debug("Async operation completed within timeout")
            return result
        except concurrent.futures.TimeoutError:
            web_ui_logger.error("Async operation timed out after 300 seconds")
            raise
        except Exception as e:
            web_ui_logger.exception("Async operation failed with exception")
            raise


@log_function_calls(web_ui_logger)
def init_components():
    """Initialize all assistant components only if workspace is already configured."""
    global config, git_tools, code_analyzer, rag_system, llm_client, coder_agent
    
    web_ui_logger.info("Starting component initialization")
    
    try:
        config = get_config()
        web_ui_logger.debug(f"Configuration loaded: workspace_path={config.workspace_path}")
        
        # Only initialize if workspace is configured
        if config.workspace_path and os.path.exists(config.workspace_path):
            web_ui_logger.info(f"Initializing components for workspace: {config.workspace_path}")
            return reinitialize_components(config.workspace_path)
        else:
            web_ui_logger.warning("No workspace configured. Skipping component initialization.")
            return True
            
    except Exception as e:
        web_ui_logger.exception(f"Failed to initialize components: {e}")
        # Set minimal config for web UI to work
        from code_dev_assistant.config import (
            AssistantConfig, GitConfig, RAGConfig, LLMConfig, CodeAnalysisConfig,
            CoderAgentConfig, WorkflowConfig, AgentUIConfig
        )
        config = AssistantConfig(
            workspace_path=None,  # No workspace by default
            git=GitConfig(),
            rag=RAGConfig(),
            llm=LLMConfig(),
            code_analysis=CodeAnalysisConfig(),
            coder_agent=CoderAgentConfig(),
            workflow=WorkflowConfig(),
            ui=AgentUIConfig(),
            log_level="INFO"
        )
        web_ui_logger.debug("Minimal configuration created for web UI")
        return False


@app.route('/')
@log_function_calls(web_ui_logger)
def index():
    """Main dashboard page."""
    web_ui_logger.debug("Accessing main dashboard page")
    return render_template('index.html', config=config)


@app.route('/api/config')
@log_function_calls(web_ui_logger)
def get_config_api():
    """Get current configuration."""
    web_ui_logger.debug("Getting configuration via API")
    if not config:
        web_ui_logger.error("Configuration not loaded")
        return jsonify({'error': 'Configuration not loaded'}), 500
    
    config_data = {
        'workspace_path': config.workspace_path,
        'llm_model': config.llm.model,
        'llm_base_url': config.llm.base_url,
        'rag_db_path': config.rag.db_path,
        'log_level': config.log_level
    }
    web_ui_logger.debug(f"Returning configuration: {config_data}")
    return jsonify(config_data)


@app.route('/git')
@log_function_calls(web_ui_logger)
def git_page():
    """Git operations page."""
    web_ui_logger.debug("Accessing git operations page")
    return render_template('git.html')


@app.route('/api/git/status')
@log_function_calls(web_ui_logger)
def git_status():
    """Get Git repository status."""
    web_ui_logger.debug("Getting git status")
    try:
        if not git_tools:
            web_ui_logger.warning("Git tools not initialized")
            return jsonify({'success': False, 'error': 'Git tools not initialized'})
        result = run_async(git_tools.execute_git_tool('git_status', {}))
        web_ui_logger.debug(f"Git status result: {len(result[0].text) if result else 0} chars")
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        web_ui_logger.exception(f"Git status failed: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/git/add', methods=['POST'])
@log_function_calls(git_logger)
def git_add():
    """Add files to Git staging area."""
    try:
        data = request.get_json()
        files = data.get('files', [])
        git_logger.debug(f"Adding files to Git: {files}")
        
        if not git_tools:
            git_logger.error("Git tools not initialized")
            return jsonify({'success': False, 'error': 'Git tools not initialized'})
            
        result = run_async(git_tools.execute_git_tool('git_add', {'files': files}))
        git_logger.info(f"Git add completed for {len(files)} files")
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        git_logger.exception(f"Git add failed: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/git/commit', methods=['POST'])
@log_function_calls(git_logger)
def git_commit():
    """Commit staged changes."""
    try:
        if not git_tools:
            git_logger.error("Git tools not initialized")
            return jsonify({'success': False, 'error': 'Git tools not initialized'})
            
        data = request.get_json()
        message = data.get('message', '')
        add_all = data.get('add_all', False)
        
        git_logger.debug(f"Git commit requested: message='{message}', add_all={add_all}")
        
        if not message:
            git_logger.warning("Commit attempted without message")
            return jsonify({'success': False, 'error': 'Commit message is required'})
        
        result = run_async(git_tools.execute_git_tool('git_commit', {
            'message': message,
            'add_all': add_all
        }))
        git_logger.info(f"Git commit completed: '{message}'")
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        git_logger.exception(f"Git commit failed: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/git/branches')
@log_function_calls(git_logger)
def git_branches():
    """List Git branches."""
    try:
        if not git_tools:
            git_logger.error("Git tools not initialized")
            return jsonify({'success': False, 'error': 'Git tools not initialized'})
            
        result = run_async(git_tools.execute_git_tool('git_branch_list', {}))
        git_logger.debug(f"Listed Git branches: {len(result[0].text) if result else 0} chars")
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        git_logger.exception(f"Git branches listing failed: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/git/create_branch', methods=['POST'])
@log_function_calls(git_logger)
def git_create_branch():
    """Create a new Git branch."""
    try:
        if not git_tools:
            git_logger.error("Git tools not initialized")
            return jsonify({'success': False, 'error': 'Git tools not initialized'})
            
        data = request.get_json()
        branch_name = data.get('branch_name', '')
        checkout = data.get('checkout', True)
        
        git_logger.debug(f"Creating Git branch: {branch_name}, checkout={checkout}")
        
        if not branch_name:
            git_logger.warning("Branch creation attempted without name")
            return jsonify({'success': False, 'error': 'Branch name is required'})
        
        result = run_async(git_tools.execute_git_tool('git_create_branch', {
            'branch_name': branch_name,
            'checkout': checkout
        }))
        git_logger.info(f"Git branch created: {branch_name}")
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        git_logger.exception(f"Git branch creation failed: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/git/checkout', methods=['POST'])
@log_function_calls(git_logger)
def git_checkout():
    """Switch to a different branch."""
    try:
        if not git_tools:
            git_logger.error("Git tools not initialized")
            return jsonify({'success': False, 'error': 'Git tools not initialized'})
            
        data = request.get_json()
        branch_name = data.get('branch_name', '')
        
        git_logger.debug(f"Checking out Git branch: {branch_name}")
        
        if not branch_name:
            git_logger.warning("Branch checkout attempted without name")
            return jsonify({'success': False, 'error': 'Branch name is required'})
        
        result = run_async(git_tools.execute_git_tool('git_checkout', {
            'branch_name': branch_name
        }))
        git_logger.info(f"Git branch checked out: {branch_name}")
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        git_logger.exception(f"Git checkout failed: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/rag')
@log_function_calls(web_ui_logger)
def rag_page():
    """RAG system page."""
    web_ui_logger.debug("Accessing RAG operations page")
    return render_template('rag.html')


@app.route('/api/rag/index', methods=['POST'])
@log_function_calls(rag_logger)
def rag_index():
    """Index the codebase for RAG."""
    try:
        if not rag_system:
            rag_logger.error("RAG system not initialized")
            return jsonify({'success': False, 'error': 'RAG system not initialized'})
            
        data = request.get_json()
        directory = data.get('directory', '.')
        force_reindex = data.get('force_reindex', False)
        
        rag_logger.debug(f"RAG indexing requested: directory={directory}, force_reindex={force_reindex}")
        
        result = run_async(rag_system.execute_rag_tool('index_codebase', {
            'directory': directory,
            'force_reindex': force_reindex
        }))
        rag_logger.info(f"RAG indexing completed for directory: {directory}")
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        rag_logger.exception(f"RAG indexing failed: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/rag/search', methods=['POST'])
@log_function_calls(rag_logger)
def rag_search():
    """Search the indexed codebase."""
    try:
        if not rag_system:
            rag_logger.error("RAG system not initialized")
            return jsonify({'success': False, 'error': 'RAG system not initialized'})
            
        data = request.get_json()
        query = data.get('query', '')
        limit = data.get('limit', 5)
        
        rag_logger.debug(f"RAG search requested: query='{query}', limit={limit}")
        
        if not query:
            rag_logger.warning("RAG search attempted without query")
            return jsonify({'success': False, 'error': 'Search query is required'})
        
        # Use lower default threshold based on comprehensive test results
        result = run_async(rag_system.execute_rag_tool('search_code', {
            'query': query,
            'limit': limit,
            'similarity_threshold': data.get('similarity_threshold', 0.3),
            'filter_language': data.get('filter_language'),
            'filter_type': data.get('filter_type')
        }))
        
        rag_logger.info(f"RAG search completed for query: '{query[:50]}...'")
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        rag_logger.exception(f"RAG search failed: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/rag/search/advanced', methods=['POST'])
@log_function_calls(rag_logger)
def rag_search_advanced():
    """Advanced search with analytics and filtering."""
    try:
        if not rag_system:
            rag_logger.error("RAG system not initialized")
            return jsonify({'success': False, 'error': 'RAG system not initialized'})
            
        data = request.get_json()
        query = data.get('query', '')
        limit = data.get('limit', 10)
        similarity_threshold = data.get('similarity_threshold', 0.3)
        filter_language = data.get('filter_language')
        filter_type = data.get('filter_type')
        
        rag_logger.debug(f"Advanced RAG search: query='{query}', limit={limit}, threshold={similarity_threshold}")
        
        if not query:
            rag_logger.warning("Advanced RAG search attempted without query")
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
            rag_logger.debug(f"Language filter applied: {filter_language}")
        if filter_type:
            search_params['filter_type'] = filter_type
            rag_logger.debug(f"Type filter applied: {filter_type}")
        
        # Execute search
        result = run_async(rag_system.execute_rag_tool('search_code', search_params))
        
        if result and result[0]:
            output = result[0].text
            
            # Extract analytics
            analytics = extract_search_analytics(output, query, similarity_threshold)
            rag_logger.info(f"Advanced RAG search completed: {analytics.get('result_count', 0)} results")
            
            return jsonify({
                'success': True, 
                'output': output,
                'analytics': analytics,
                'search_params': search_params
            })
        else:
            rag_logger.warning("Advanced RAG search returned no results")
            return jsonify({'success': True, 'output': 'No results found'})
            
    except Exception as e:
        rag_logger.exception(f"Advanced RAG search failed: {e}")
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
@log_function_calls(rag_logger)
def rag_status():
    """Get RAG system status."""
    try:
        if not rag_system:
            rag_logger.error("RAG system not initialized")
            return jsonify({'success': False, 'error': 'RAG system not initialized'})
            
        result = run_async(rag_system.execute_rag_tool('rag_status', {}))
        rag_logger.debug("RAG status retrieved successfully")
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        rag_logger.exception(f"RAG status check failed: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/rag/clear', methods=['POST'])
@log_function_calls(rag_logger)
def rag_clear():
    """Clear the RAG index."""
    try:
        data = request.get_json()
        confirm = data.get('confirm', False)
        
        rag_logger.debug(f"RAG clear requested: confirm={confirm}")
        
        if not rag_system:
            rag_logger.error("RAG system not initialized")
            return jsonify({'success': False, 'error': 'RAG system not initialized'})
        
        result = run_async(rag_system.execute_rag_tool('clear_index', {'confirm': confirm}))
        rag_logger.info(f"RAG index cleared: confirm={confirm}")
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        rag_logger.exception(f"RAG clear failed: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/rag/context', methods=['POST'])
@log_function_calls(rag_logger)
def rag_context():
    """Get context for a specific function or class."""
    try:
        if not rag_system:
            rag_logger.error("RAG system not initialized")
            return jsonify({'success': False, 'error': 'RAG system not initialized'})
            
        data = request.get_json()
        identifier = data.get('identifier', '')
        include_related = data.get('include_related', True)
        
        rag_logger.debug(f"RAG context requested: identifier='{identifier}', include_related={include_related}")
        
        if not identifier:
            rag_logger.warning("RAG context attempted without identifier")
            return jsonify({'success': False, 'error': 'Identifier is required'})
        
        result = run_async(rag_system.execute_rag_tool('get_context', {
            'identifier': identifier,
            'include_related': include_related
        }))
        rag_logger.info(f"RAG context retrieved for: '{identifier}'")
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        rag_logger.exception(f"RAG context retrieval failed: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/llm')
@log_function_calls(web_ui_logger)
def llm_page():
    """LLM tools page."""
    web_ui_logger.debug("Accessing LLM tools page")
    return render_template('llm.html')


@app.route('/api/llm/generate', methods=['POST'])
@log_function_calls(llm_logger)
def llm_generate():
    """Generate code using LLM."""
    try:
        if not llm_client:
            llm_logger.error("LLM client not initialized")
            return jsonify({'success': False, 'error': 'LLM client not initialized'})
            
        data = request.get_json()
        description = data.get('description', '')
        language = data.get('language', 'python')
        context = data.get('context', '')
        style = data.get('style', 'clean')
        
        llm_logger.debug(f"LLM code generation requested: description='{description[:50]}...', language={language}, style={style}")
        
        if not description:
            llm_logger.warning("LLM code generation attempted without description")
            return jsonify({'success': False, 'error': 'Code description is required'})
        
        result = run_async(llm_client.execute_llm_tool('generate_code', {
            'description': description,
            'language': language,
            'context': context,
            'style': style
        }))
        llm_logger.info(f"LLM code generation completed for: '{description[:50]}...'")
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        llm_logger.exception(f"LLM code generation failed: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/llm/explain', methods=['POST'])
@log_function_calls(llm_logger)
def llm_explain():
    """Explain code using LLM."""
    try:
        if not llm_client:
            llm_logger.error("LLM client not initialized")
            return jsonify({'success': False, 'error': 'LLM client not initialized'})
            
        data = request.get_json()
        code = data.get('code', '')
        detail_level = data.get('detail_level', 'medium')
        
        llm_logger.debug(f"LLM code explanation requested: code_length={len(code)}, detail_level={detail_level}")
        
        if not code:
            llm_logger.warning("LLM code explanation attempted without code")
            return jsonify({'success': False, 'error': 'Code is required'})
        
        result = run_async(llm_client.execute_llm_tool('explain_code', {
            'code': code,
            'detail_level': detail_level
        }))
        llm_logger.info(f"LLM code explanation completed for {len(code)} chars of code")
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        llm_logger.exception(f"LLM code explanation failed: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/llm/refactor', methods=['POST'])
@log_function_calls(llm_logger)
def llm_refactor():
    """Refactor code using LLM."""
    try:
        if not llm_client:
            llm_logger.error("LLM client not initialized")
            return jsonify({'success': False, 'error': 'LLM client not initialized'})
            
        data = request.get_json()
        code = data.get('code', '')
        goals = data.get('goals', [])
        language = data.get('language', 'python')
        
        llm_logger.debug(f"LLM code refactoring requested: code_length={len(code)}, goals={goals}, language={language}")
        
        if not code:
            llm_logger.warning("LLM code refactoring attempted without code")
            return jsonify({'success': False, 'error': 'Code is required'})
        
        result = run_async(llm_client.execute_llm_tool('refactor_code', {
            'code': code,
            'goals': goals,
            'language': language
        }))
        llm_logger.info(f"LLM code refactoring completed for {len(code)} chars of code with goals: {goals}")
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        llm_logger.exception(f"LLM code refactoring failed: {e}")
        return jsonify({'success': False, 'error': str(e)})


# Helper functions for enhanced chat context collection
@log_function_calls(agent_logger)
async def _get_workspace_context():
    """Get current workspace information."""
    try:
        agent_logger.debug("Starting workspace context collection")
        
        if not config or not config.workspace_path:
            agent_logger.warning("No workspace configuration available")
            return None
        
        workspace_path = config.workspace_path
        agent_logger.debug(f"Analyzing workspace at: {workspace_path}")
        
        workspace_info = {
            'path': workspace_path,
            'name': os.path.basename(workspace_path),
            'exists': os.path.exists(workspace_path)
        }
        
        agent_logger.debug(f"Workspace info: name={workspace_info['name']}, exists={workspace_info['exists']}")
        
        # Get basic project info
        if os.path.exists(workspace_path):
            try:
                agent_logger.debug("Starting file analysis in workspace")
                # Count files by type
                file_counts = {}
                total_dirs = 0
                
                for root, dirs, files in os.walk(workspace_path):
                    # Skip hidden and common build directories
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'build', 'dist']]
                    total_dirs += len(dirs)
                    
                    for file in files:
                        if not file.startswith('.'):
                            ext = os.path.splitext(file)[1].lower()
                            file_counts[ext] = file_counts.get(ext, 0) + 1
                
                workspace_info['file_counts'] = file_counts
                workspace_info['total_files'] = sum(file_counts.values())
                workspace_info['total_directories'] = total_dirs
                
                agent_logger.info(f"Workspace analysis complete: {workspace_info['total_files']} files, {total_dirs} directories")
                agent_logger.debug(f"File types found: {list(file_counts.keys())[:10]}")  # Log first 10 extensions
                
            except Exception as e:
                agent_logger.error(f"Failed to analyze workspace files: {e}")
                workspace_info['error'] = f"Failed to analyze workspace: {e}"
        else:
            agent_logger.warning(f"Workspace path does not exist: {workspace_path}")
        
        return workspace_info
    except Exception as e:
        agent_logger.exception(f"Error collecting workspace context: {e}")
        return {'error': str(e)}

@log_function_calls(git_logger)
async def _get_git_context():
    """Get Git repository status."""
    try:
        git_logger.debug("Starting Git context collection")
        
        if not git_tools:
            git_logger.warning("Git tools not available")
            return None
        
        git_info = {}
        
        # Get status
        try:
            git_logger.debug("Fetching Git status")
            status_result = await git_tools.execute_git_tool('git_status', {})
            if status_result and status_result[0]:
                git_info['status'] = status_result[0].text
                # Count lines in status for logging
                status_lines = len(status_result[0].text.splitlines()) if status_result[0].text else 0
                git_logger.debug(f"Git status retrieved: {status_lines} lines")
            else:
                git_logger.warning("Git status returned empty result")
        except Exception as e:
            git_logger.error(f"Failed to get Git status: {e}")
            git_info['status_error'] = str(e)
        
        # Get current branch
        try:
            git_logger.debug("Fetching Git branch information")
            branch_result = await git_tools.execute_git_tool('git_branch_list', {})
            if branch_result and branch_result[0]:
                git_info['branches'] = branch_result[0].text
                # Extract current branch for logging
                branches_text = branch_result[0].text
                current_branch = "unknown"
                for line in branches_text.splitlines():
                    if line.startswith('*'):
                        current_branch = line.strip('* ').strip()
                        break
                git_logger.debug(f"Git branches retrieved, current branch: {current_branch}")
            else:
                git_logger.warning("Git branch list returned empty result")
        except Exception as e:
            git_logger.error(f"Failed to get Git branches: {e}")
            git_info['branch_error'] = str(e)
        
        if git_info:
            git_logger.info(f"Git context collected: {len(git_info)} elements")
        else:
            git_logger.info("No Git context collected")
            
        return git_info if git_info else None
    except Exception as e:
        git_logger.exception(f"Error collecting Git context: {e}")
        return {'error': str(e)}

@log_function_calls(rag_logger)
async def _get_rag_context(question):
    """Get relevant code context using RAG search."""
    try:
        rag_logger.debug(f"Starting RAG context search for question: '{question[:50]}...'")
        
        if not rag_system:
            rag_logger.warning("RAG system not available")
            return None
        
        # Search for relevant code based on the question
        search_params = {
            'query': question,
            'limit': 5,
            'similarity_threshold': 0.3
        }
        
        rag_logger.debug(f"RAG search parameters: limit={search_params['limit']}, threshold={search_params['similarity_threshold']}")
        
        search_result = await rag_system.execute_rag_tool('search_code', search_params)
        
        if search_result and search_result[0]:
            result_text = search_result[0].text
            result_length = len(result_text) if result_text else 0
            
            rag_logger.info(f"RAG search completed: {result_length} chars of relevant code found")
            rag_logger.debug(f"RAG result preview: '{result_text[:100]}...' " if result_text else "Empty result")
            
            return result_text
        else:
            rag_logger.info("RAG search completed but no relevant code found")
            return None
            
    except Exception as e:
        rag_logger.exception(f"Error in RAG context search: {e}")
        return {'error': str(e)}

@log_function_calls(web_ui_logger)
async def _get_project_structure():
    """Get project structure overview."""
    try:
        web_ui_logger.debug("Starting project structure analysis")
        
        if not config or not config.workspace_path or not os.path.exists(config.workspace_path):
            web_ui_logger.warning("No valid workspace path for project structure analysis")
            return None
        
        workspace_path = config.workspace_path
        web_ui_logger.debug(f"Analyzing project structure at: {workspace_path}")
        
        # Get top-level directories and important files
        try:
            items = os.listdir(workspace_path)
            dirs = []
            files = []
            
            important_files = ['readme.md', 'requirements.txt', 'package.json', 'pyproject.toml', 
                             'setup.py', 'dockerfile', 'docker-compose.yml', 'makefile', 
                             '.gitignore', 'license']
            
            web_ui_logger.debug(f"Found {len(items)} items in workspace root")
            
            for item in sorted(items):
                if item.startswith('.'):
                    continue
                item_path = os.path.join(workspace_path, item)
                if os.path.isdir(item_path):
                    dirs.append(item)
                else:
                    # Only include important files
                    if item.lower() in important_files:
                        files.append(item)
            
            structure_info = {
                'directories': dirs[:10],  # Limit to top 10
                'important_files': files,
                'total_dirs': len(dirs),
                'workspace_path': workspace_path
            }
            
            web_ui_logger.info(f"Project structure analyzed: {len(dirs)} directories, {len(files)} important files")
            web_ui_logger.debug(f"Top directories: {dirs[:5]}")  # Log first 5 directories
            web_ui_logger.debug(f"Important files found: {files}")
            
            return structure_info
            
        except Exception as e:
            web_ui_logger.error(f"Failed to analyze project structure: {e}")
            return {'error': str(e)}
            
    except Exception as e:
        web_ui_logger.exception(f"Error in project structure analysis: {e}")
        return {'error': str(e)}

@log_function_calls(git_logger)
async def _get_recent_changes():
    """Get recent file changes if Git is available."""
    try:
        git_logger.debug("Starting recent changes analysis")
        
        if not git_tools:
            git_logger.warning("Git tools not available for recent changes")
            return None
        
        # Try to get recent commits or changes
        try:
            git_logger.debug("Attempting to get recent Git changes")
            # For now, this functionality is not implemented in git_tools
            # We'll return None gracefully and log that it's not available
            git_logger.info("Recent changes feature not yet implemented")
            return None
        except Exception as e:
            git_logger.warning(f"Could not retrieve recent changes: {e}")
            return None
            
    except Exception as e:
        git_logger.error(f"Error in recent changes analysis: {e}")
        return None

@log_function_calls(web_ui_logger)
def _format_context_summary(enhanced_context):
    """Format context summary for display."""
    web_ui_logger.debug(f"Formatting context summary for {len(enhanced_context)} context elements")
    
    summary = []
    
    if 'workspace' in enhanced_context:
        workspace = enhanced_context['workspace']
        if 'name' in workspace:
            summary.append(f"Workspace: {workspace['name']}")
        if 'total_files' in workspace:
            summary.append(f"Files: {workspace['total_files']}")
        web_ui_logger.debug("Added workspace info to summary")
    
    if 'git' in enhanced_context:
        summary.append("Git status included")
        web_ui_logger.debug("Added Git info to summary")
    
    if 'relevant_code' in enhanced_context:
        summary.append("Relevant code snippets found")
        web_ui_logger.debug("Added RAG code snippets to summary")
    
    if 'project_structure' in enhanced_context:
        summary.append("Project structure analyzed")
        web_ui_logger.debug("Added project structure to summary")
    
    if 'user_context' in enhanced_context:
        summary.append("User context provided")
        web_ui_logger.debug("Added user context to summary")
    
    web_ui_logger.info(f"Context summary formatted: {len(summary)} items")
    return summary


@app.route('/chat')
@log_function_calls(web_ui_logger)
def chat_page():
    """Chat interface page."""
    web_ui_logger.debug("Accessing chat interface page")
    return render_template('chat.html')


@app.route('/api/chat', methods=['POST'])
@log_function_calls(agent_logger)
def chat():
    """Enhanced chat with automatic context collection and MCP integration."""
    try:
        if not coder_agent:
            agent_logger.error("Coder agent not initialized")
            return jsonify({'success': False, 'error': 'Coder agent not initialized'})
            
        data = request.get_json()
        question = data.get('question', '')
        user_context = data.get('context', '')
        auto_context = data.get('auto_context', True)  # Enable by default
        
        agent_logger.debug(f"Chat request: question='{question[:100]}...', auto_context={auto_context}")
        
        if not question:
            agent_logger.warning("Chat request without question")
            return jsonify({'success': False, 'error': 'Question is required'})
        
        # Automatically collect comprehensive project context
        enhanced_context = {}
        
        if auto_context:
            agent_logger.debug("Collecting automatic context")
            try:
                # 1. Get current workspace information
                workspace_info = run_async(_get_workspace_context())
                if workspace_info:
                    enhanced_context['workspace'] = workspace_info
                    agent_logger.debug("Workspace context collected")
                
                # 2. Get Git status and recent changes
                git_context = run_async(_get_git_context())
                if git_context:
                    enhanced_context['git'] = git_context
                    agent_logger.debug("Git context collected")
                
                # 3. Search RAG for relevant code based on the question
                rag_context = run_async(_get_rag_context(question))
                if rag_context:
                    enhanced_context['relevant_code'] = rag_context
                    agent_logger.debug("RAG context collected")
                
                # 4. Get project structure overview
                project_structure = run_async(_get_project_structure())
                if project_structure:
                    enhanced_context['project_structure'] = project_structure
                    agent_logger.debug("Project structure context collected")
                
                # 5. Get recent file changes if any
                recent_changes = run_async(_get_recent_changes())
                if recent_changes:
                    enhanced_context['recent_changes'] = recent_changes
                    agent_logger.debug("Recent changes context collected")
                    
            except Exception as e:
                agent_logger.warning(f"Failed to collect auto context: {e}")
        
        # Combine user-provided context with auto-collected context
        if user_context and user_context.strip():
            enhanced_context['user_context'] = user_context
            agent_logger.debug("User context added")
        
        agent_logger.info(f"Processing chat request with {len(enhanced_context)} context elements")
        
        # Use the coder agent to process the request with enhanced context
        try:
            response = run_async(coder_agent.process_natural_language_request(question, enhanced_context))
        except concurrent.futures.TimeoutError:
            agent_logger.error("Chat request timed out")
            return jsonify({
                'success': False, 
                'error': 'Request timed out. The operation is taking longer than expected. Please try a simpler question or check the agent status.'
            })
        
        if response.success:
            # Format the response for the UI
            output = response.message
            if response.data and 'response' in response.data:
                output = response.data['response']
            elif response.data:
                # Include other relevant data in the output
                data_parts = []
                for key, value in response.data.items():
                    if isinstance(value, str) and value.strip():
                        data_parts.append(f"**{key.replace('_', ' ').title()}:**\n{value}")
                if data_parts:
                    output = "\n\n".join(data_parts)
            
            # Add suggestions if available
            if response.suggestions:
                output += "\n\n**Suggestions:**\n" + "\n".join(f"• {s}" for s in response.suggestions)
            
            # Add next actions if available
            if response.next_actions:
                output += "\n\n**Next Actions:**\n" + "\n".join(f"→ {a}" for a in response.next_actions)
            
            # Include context summary in the response
            context_summary = _format_context_summary(enhanced_context)
            
            agent_logger.info(f"Chat request completed successfully: {len(output)} chars response")
            
            return jsonify({
                'success': True, 
                'output': output,
                'context_used': context_summary,
                'mcp_tools_available': True
            })
        else:
            agent_logger.error(f"Chat request failed: {response.message}")
            return jsonify({'success': False, 'error': response.message})
            
    except Exception as e:
        agent_logger.exception(f"Chat request failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/chat/context/auto', methods=['POST'])
@log_function_calls(agent_logger)
def chat_context_auto():
    """Get auto context preview for a question without sending to LLM."""
    try:
        agent_logger.debug("Auto context preview requested")
        
        data = request.get_json()
        question = data.get('question', '')
        
        agent_logger.debug(f"Context preview for question: '{question[:50]}...'")
        
        if not question:
            agent_logger.warning("Context preview requested without question")
            return jsonify({'success': False, 'error': 'Question is required'})
        
        # Collect context preview
        enhanced_context = {}
        summary = []
        
        agent_logger.debug("Collecting context preview")
        
        # Get workspace context
        workspace_context = run_async(_get_workspace_context())
        if workspace_context:
            enhanced_context['workspace'] = workspace_context
            if 'name' in workspace_context:
                summary.append(f"Workspace: {workspace_context['name']}")
            agent_logger.debug("Workspace context collected for preview")
        
        # Get git context
        git_context = run_async(_get_git_context())
        if git_context:
            enhanced_context['git'] = git_context
            summary.append("Git status available")
            agent_logger.debug("Git context collected for preview")
        
        # Get relevant code context via RAG
        rag_context = run_async(_get_rag_context(question))
        if rag_context:
            enhanced_context['relevant_code'] = rag_context
            summary.append("Relevant code found")
            agent_logger.debug("RAG context collected for preview")
        
        # Get project structure
        structure_context = run_async(_get_project_structure())
        if structure_context:
            enhanced_context['project_structure'] = structure_context
            summary.append("Project structure analyzed")
            agent_logger.debug("Project structure collected for preview")
        
        agent_logger.info(f"Context preview completed: {len(summary)} context elements")
        
        return jsonify({
            'success': True,
            'summary': summary,
            'context_preview': enhanced_context
        })
    except Exception as e:
        agent_logger.exception(f"Context preview failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'summary': ['Error collecting context'],
            'context_preview': {}
        })


@app.route('/api/mcp/tools')
@log_function_calls(web_ui_logger)
def get_mcp_tools():
    """Get available MCP tools and capabilities."""
    try:
        web_ui_logger.debug("MCP tools inventory requested")
        
        tools = []
        
        # Add available MCP tools from different components
        if git_tools:
            git_tool_count = 4
            tools.extend([
                {
                    'name': 'git_status',
                    'description': 'Get current git repository status',
                    'category': 'git',
                    'available': True
                },
                {
                    'name': 'git_diff',
                    'description': 'Show file differences',
                    'category': 'git',
                    'available': True
                },
                {
                    'name': 'git_log',
                    'description': 'View commit history',
                    'category': 'git',
                    'available': True
                },
                {
                    'name': 'git_branch',
                    'description': 'Manage git branches',
                    'category': 'git',
                    'available': True
                }
            ])
            web_ui_logger.debug(f"Added {git_tool_count} Git tools to MCP inventory")
        else:
            web_ui_logger.warning("Git tools not available for MCP inventory")
        
        if rag_system:
            rag_tool_count = 3
            tools.extend([
                {
                    'name': 'rag_search',
                    'description': 'Search codebase with semantic similarity',
                    'category': 'rag',
                    'available': True
                },
                {
                    'name': 'rag_index',
                    'description': 'Index codebase for semantic search',
                    'category': 'rag',
                    'available': True
                },
                {
                    'name': 'rag_context',
                    'description': 'Get contextual code information',
                    'category': 'rag',
                    'available': True
                }
            ])
            web_ui_logger.debug(f"Added {rag_tool_count} RAG tools to MCP inventory")
        else:
            web_ui_logger.warning("RAG system not available for MCP inventory")
        
        if code_analyzer:
            analyzer_tool_count = 1
            tools.extend([
                {
                    'name': 'code_analyze',
                    'description': 'Analyze code structure and patterns',
                    'category': 'analysis',
                    'available': True
                },
                {
                    'name': 'code_explain',
                    'description': 'Explain code functionality',
                    'category': 'analysis',
                    'available': True
                },
                {
                    'name': 'code_refactor',
                    'description': 'Suggest code improvements',
                    'category': 'analysis',
                    'available': True
                }
            ])
            web_ui_logger.debug(f"Added {analyzer_tool_count} analysis tools to MCP inventory")
        else:
            web_ui_logger.warning("Code analyzer not available for MCP inventory")
        
        # Add file operations tools
        file_tool_count = 3
        tools.extend([
            {
                'name': 'file_read',
                'description': 'Read file contents',
                'category': 'files',
                'available': True
            },
            {
                'name': 'file_write',
                'description': 'Write file contents',
                'category': 'files',
                'available': True
            },
            {
                'name': 'file_list',
                'description': 'List directory contents',
                'category': 'files',
                'available': True
            }
        ])
        web_ui_logger.debug(f"Added {file_tool_count} file operation tools to MCP inventory")
        
        # Add project context tools
        context_tool_count = 3
        tools.extend([
            {
                'name': 'project_structure',
                'description': 'Get project structure overview',
                'category': 'context',
                'available': True
            },
            {
                'name': 'workspace_info',
                'description': 'Get current workspace information',
                'category': 'context',
                'available': True
            },
            {
                'name': 'auto_context',
                'description': 'Automatically collect project context',
                'category': 'context',
                'available': True
            }
        ])
        web_ui_logger.debug(f"Added {context_tool_count} context tools to MCP inventory")
        
        total_tools = len(tools)
        categories = list(set(tool['category'] for tool in tools))
        
        web_ui_logger.info(f"MCP tools inventory completed: {total_tools} tools across {len(categories)} categories")
        web_ui_logger.debug(f"Available categories: {categories}")
        
        return jsonify({
            'success': True,
            'tools': tools,
            'total_tools': total_tools,
            'categories': categories,
            'mcp_status': {
                'git_tools': git_tools is not None,
                'rag_system': rag_system is not None,
                'code_analyzer': code_analyzer is not None,
                'coder_agent': coder_agent is not None
            }
        })
        
    except Exception as e:
        web_ui_logger.exception(f"MCP tools inventory failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'tools': [],
            'total_tools': 0,
            'categories': []
        })
        return jsonify({
            'success': False,
            'error': str(e),
            'tools': [],
            'mcp_status': {
                'git_tools': False,
                'rag_system': False,
                'code_analyzer': False,
                'coder_agent': False
            }
        })


@app.route('/settings')
@log_function_calls(web_ui_logger)
def settings_page():
    """Settings page."""
    web_ui_logger.debug("Accessing settings page")
    web_ui_logger.debug(f"Current config available: {config is not None}")
    return render_template('settings.html', config=config)


@app.route('/api/rag/suggestions')
@log_function_calls(rag_logger)
def rag_suggestions():
    """Get search suggestions based on comprehensive test results."""
    rag_logger.debug("RAG search suggestions requested")
    
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
    
    rag_logger.info(f"RAG suggestions returned: {len(suggestions['high_success_queries'])} high-success queries")
    rag_logger.debug("RAG suggestions included optimal settings and troubleshooting tips")
    
    return jsonify({'success': True, 'suggestions': suggestions})


@app.route('/api/agent/status')
@log_function_calls(agent_logger)
def agent_status():
    """Get coder agent status and capabilities."""
    try:
        agent_logger.debug("Agent status requested")
        
        if not coder_agent:
            agent_logger.error("Agent status requested but coder agent not initialized")
            return jsonify({'success': False, 'error': 'Coder agent not initialized'})
        
        # Get agent status
        try:
            agent_logger.debug("Fetching agent status from coder agent")
            result = run_async(coder_agent.execute_agent_tool('get_agent_status', {}))
            agent_info = result[0].text if result else '{}'
            
            agent_logger.debug(f"Agent status raw result: {len(agent_info)} chars")
            
            try:
                import json
                status_data = json.loads(agent_info)
                agent_logger.info("Agent status successfully parsed from JSON")
            except Exception as parse_error:
                agent_logger.warning(f"Failed to parse agent status JSON: {parse_error}")
                status_data = {'error': 'Could not parse agent status', 'raw_info': agent_info[:200]}
            
            return jsonify({'success': True, 'status': status_data})
            
        except Exception as e:
            agent_logger.error(f"Failed to execute agent status tool: {e}")
            return jsonify({'success': False, 'error': f'Agent status tool failed: {str(e)}'})
            
    except Exception as e:
        agent_logger.exception(f"Agent status endpoint failed: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/agent/initialize', methods=['POST'])
@log_function_calls(agent_logger)
def agent_initialize():
    """Initialize agent project context."""
    try:
        agent_logger.debug("Agent initialization requested")
        
        if not coder_agent:
            agent_logger.error("Agent initialization requested but coder agent not available")
            return jsonify({'success': False, 'error': 'Coder agent not initialized'})
        
        data = request.get_json()
        project_path = data.get('project_path', '.')
        
        agent_logger.debug(f"Initializing agent project context for path: {project_path}")
        
        # Validate project path
        if not os.path.exists(project_path):
            agent_logger.error(f"Project path does not exist: {project_path}")
            return jsonify({'success': False, 'error': 'Project path does not exist'})
        
        try:
            response = run_async(coder_agent.initialize_project_context(project_path))
            
            agent_logger.info(f"Agent initialization completed: success={response.success}")
            if response.suggestions:
                agent_logger.debug(f"Agent provided {len(response.suggestions)} suggestions")
            
            return jsonify({
                'success': response.success,
                'message': response.message,
                'suggestions': response.suggestions or []
            })
            
        except Exception as e:
            agent_logger.error(f"Agent initialization failed during execution: {e}")
            return jsonify({'success': False, 'error': f'Initialization failed: {str(e)}'})
            
    except Exception as e:
        agent_logger.exception(f"Agent initialization endpoint failed: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/initialization_status')
@log_function_calls(web_ui_logger)
def get_initialization_status():
    """Check if the system needs initial setup (codebase selection)."""
    try:
        needs_setup = False
        workspace_configured = False
        components_initialized = False
        
        web_ui_logger.debug("Checking initialization status")
        
        # Check if workspace is configured
        if config and config.workspace_path and os.path.exists(config.workspace_path):
            workspace_configured = True
            web_ui_logger.debug(f"Workspace configured: {config.workspace_path}")
        elif current_workspace_path and os.path.exists(current_workspace_path):
            workspace_configured = True
            web_ui_logger.debug(f"Current workspace: {current_workspace_path}")
            
        # Check if core components are initialized
        if coder_agent and git_tools and rag_system:
            components_initialized = True
            web_ui_logger.debug("Core components initialized")
            
        # Determine if setup is needed
        needs_setup = not (workspace_configured and components_initialized)
        
        web_ui_logger.info(f"Initialization status: needs_setup={needs_setup}, workspace_configured={workspace_configured}, components_initialized={components_initialized}")
        
        return jsonify({
            'success': True,
            'needs_setup': needs_setup,
            'workspace_configured': workspace_configured,
            'components_initialized': components_initialized,
            'current_workspace': current_workspace_path or (config.workspace_path if config else None),
            'message': 'Select a codebase to get started' if needs_setup else 'System ready'
        })
    except Exception as e:
        web_ui_logger.exception(f"Failed to check initialization status: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'needs_setup': True,
            'message': 'System needs initialization'
        })


@app.route('/api/workspace/select', methods=['POST'])
@log_function_calls(web_ui_logger)
def select_workspace():
    """Select a workspace directory."""
    global current_workspace_path
    
    try:
        data = request.get_json()
        workspace_path = data.get('workspace_path', '').strip()
        
        web_ui_logger.debug(f"Workspace selection requested: {workspace_path}")
        
        if not workspace_path:
            web_ui_logger.warning("Workspace selection attempted without path")
            return jsonify({'success': False, 'error': 'Workspace path is required'})
        
        # Validate the directory
        if not os.path.isdir(workspace_path):
            web_ui_logger.error(f"Invalid workspace directory: {workspace_path}")
            return jsonify({'success': False, 'error': 'Invalid directory'})
        
        # Update the current workspace path
        current_workspace_path = workspace_path
        web_ui_logger.info(f"Workspace path updated: {workspace_path}")
        
        # Update the config and reinitialize components
        if config:
            config.workspace_path = workspace_path
            web_ui_logger.debug("Configuration updated with new workspace path")
        
        success = reinitialize_components(workspace_path)
        
        if success:
            web_ui_logger.info(f"Components successfully reinitialized for workspace: {workspace_path}")
        else:
            web_ui_logger.warning(f"Components reinitialization failed for workspace: {workspace_path}")
        
        return jsonify({
            'success': success,
            'message': 'Workspace selected and components reinitialized' if success else 'Workspace selected, but components initialization failed',
            'workspace_path': current_workspace_path
        })
    except Exception as e:
        web_ui_logger.exception(f"Workspace selection failed: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/workspace/current')
@log_function_calls(web_ui_logger)
def get_current_workspace():
    """Get the currently selected workspace directory."""
    web_ui_logger.debug(f"Current workspace requested: {current_workspace_path}")
    return jsonify({
        'success': True,
        'workspace_path': current_workspace_path
    })


@app.route('/api/directory/browse', methods=['POST'])
@log_function_calls(web_ui_logger)
def browse_directory():
    """Browse a directory and list its contents."""
    try:
        data = request.get_json()
        directory = data.get('directory', current_workspace_path)
        
        web_ui_logger.debug(f"Directory browse requested: {directory}")
        
        if not os.path.isdir(directory):
            web_ui_logger.error(f"Invalid directory for browsing: {directory}")
            return jsonify({'success': False, 'error': 'Invalid directory'})
        
        # List directory contents
        contents = os.listdir(directory)
        files = [f for f in contents if os.path.isfile(os.path.join(directory, f))]
        subdirs = [d for d in contents if os.path.isdir(os.path.join(directory, d))]
        
        web_ui_logger.debug(f"Directory browse completed: {len(files)} files, {len(subdirs)} subdirs")
        
        return jsonify({
            'success': True,
            'directory': directory,
            'files': files,
            'subdirs': subdirs
        })
    except Exception as e:
        web_ui_logger.exception(f"Directory browse failed: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/browse_directories', methods=['POST'])
@log_function_calls(web_ui_logger)
def browse_directories():
    """Browse directories for codebase selection."""
    try:
        data = request.get_json()
        path = data.get('path', os.path.expanduser('~'))
        
        web_ui_logger.debug(f"Directory browsing requested: {path}")
        
        # Expand user path first, then normalize
        path = os.path.expanduser(path)
        path = os.path.abspath(path)
        if not os.path.exists(path) or not os.path.isdir(path):
            web_ui_logger.error(f"Invalid directory path for browsing: {path}")
            return jsonify({'success': False, 'error': 'Invalid directory path'})
        
        # Get directory contents
        directories = []
        files = []
        
        try:
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                
                # Skip hidden files/directories except important ones
                if item.startswith('.') and item not in ['.git', '.github', '.vscode']:
                    continue
                
                if os.path.isdir(item_path):
                    # Check if it's a potential code project
                    is_project = any(os.path.exists(os.path.join(item_path, indicator)) 
                                   for indicator in ['.git', 'package.json', 'pyproject.toml', 'setup.py', 'Cargo.toml', 'go.mod'])
                    
                    directories.append({
                        'name': item,
                        'path': item_path,
                        'is_project': is_project
                    })
                else:
                    # Only include important files
                    if item in ['README.md', 'package.json', 'pyproject.toml', 'setup.py', 'Cargo.toml', 'go.mod']:
                        files.append({
                            'name': item,
                            'path': item_path
                        })
        except PermissionError:
            web_ui_logger.error(f"Permission denied accessing directory: {path}")
            return jsonify({'success': False, 'error': 'Permission denied to access directory'})
        
        # Get parent directory
        parent = os.path.dirname(path) if path != os.path.dirname(path) else None
        
        web_ui_logger.debug(f"Directory browsing completed: {len(directories)} dirs, {len(files)} files")
        
        return jsonify({
            'success': True,
            'current_path': path,
            'parent_path': parent,
            'directories': directories,
            'files': files
        })
        
    except Exception as e:
        web_ui_logger.exception(f"Directory browsing failed: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/select_codebase', methods=['POST'])
@log_function_calls(web_ui_logger)
def select_codebase():
    """Select a new codebase and reinitialize components."""
    global current_workspace_path, config, git_tools, code_analyzer, rag_system, llm_client, coder_agent
    
    try:
        data = request.get_json()
        workspace_path = data.get('workspace_path')
        
        web_ui_logger.debug(f"Codebase selection requested: {workspace_path}")
        
        if not workspace_path:
            web_ui_logger.warning("Codebase selection attempted without path")
            return jsonify({'success': False, 'error': 'Workspace path is required'})
        
        # Validate the path
        workspace_path = os.path.abspath(workspace_path)
        if not os.path.exists(workspace_path) or not os.path.isdir(workspace_path):
            web_ui_logger.error(f"Invalid workspace path: {workspace_path}")
            return jsonify({'success': False, 'error': 'Invalid workspace path'})
        
        # Update the current workspace path
        current_workspace_path = workspace_path
        web_ui_logger.info(f"Codebase path updated: {workspace_path}")
        
        # Update config if it exists
        if config:
            config.workspace_path = workspace_path
            web_ui_logger.debug("Configuration updated with new codebase path")
        
        # Reinitialize components with new workspace path
        success = reinitialize_components(workspace_path)
        
        if success:
            web_ui_logger.info(f"Components successfully reinitialized for codebase: {workspace_path}")
            return jsonify({
                'success': True,
                'message': f'Successfully initialized codebase: {workspace_path}',
                'workspace_path': workspace_path
            })
        else:
            web_ui_logger.error(f"Failed to reinitialize components for codebase: {workspace_path}")
            return jsonify({
                'success': False,
                'error': 'Failed to initialize some components. Check logs for details.'
            })
            
    except Exception as e:
        web_ui_logger.exception(f"Codebase selection failed: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/current_codebase')
@log_function_calls(web_ui_logger)
def get_current_codebase():
    """Get the current selected codebase."""
    workspace_path = current_workspace_path or (config.workspace_path if config else None)
    is_initialized = bool(coder_agent)
    
    web_ui_logger.debug(f"Current codebase requested: path={workspace_path}, initialized={is_initialized}")
    
    return jsonify({
        'success': True,
        'workspace_path': workspace_path,
        'is_initialized': is_initialized
    })


@log_function_calls(web_ui_logger)
def reinitialize_components(workspace_path):
    """Reinitialize all components with a new workspace path."""
    global config, git_tools, code_analyzer, rag_system, llm_client, coder_agent
    
    web_ui_logger.info(f"Starting component reinitialization for workspace: {workspace_path}")
    
    try:
        # Lazy import heavy dependencies
        from code_dev_assistant.git_tools import GitTools
        from code_dev_assistant.code_analyzer import CodeAnalyzer
        from code_dev_assistant.rag_system import CodeRAG
        from code_dev_assistant.llm_client import CodeLLM
        from code_dev_assistant.coder_agent import CoderAgent
        
        web_ui_logger.debug("Heavy dependencies imported successfully")
        
        # Update or create config
        if not config:
            web_ui_logger.debug("Creating new configuration")
            config = get_config()
        
        config.workspace_path = workspace_path
        web_ui_logger.debug(f"Configuration updated with workspace path: {workspace_path}")
        
        # Reinitialize components
        web_ui_logger.debug("Initializing Git tools")
        git_tools = GitTools(workspace_path)
        
        web_ui_logger.debug("Initializing code analyzer")
        code_analyzer = CodeAnalyzer()
        
        # Create new RAG system with centralized database directory
        # Use workspace name as subdirectory to keep databases organized
        workspace_name = os.path.basename(workspace_path.rstrip('/'))
        rag_db_path = os.path.join(os.path.dirname(__file__), '..', 'databases', 'rag', workspace_name)
        os.makedirs(rag_db_path, exist_ok=True)
        
        web_ui_logger.debug(f"Initializing RAG system with database path: {rag_db_path}")
        rag_system = CodeRAG(rag_db_path, config.rag.embedding_model if config else "sentence-transformers/all-MiniLM-L6-v2")
        
        web_ui_logger.debug(f"Initializing LLM client with URL: {config.llm.base_url if config else 'http://localhost:11434'}")
        llm_client = CodeLLM(
            config.llm.base_url if config else "http://localhost:11434",
            config.llm.model if config else "codellama:7b-instruct"
        )
        
        # Initialize RAG system
        try:
            web_ui_logger.debug("Initializing RAG system database")
            run_async(rag_system.initialize())
            web_ui_logger.info(f"✅ RAG system initialized for workspace: {workspace_path}")
        except Exception as e:
            web_ui_logger.warning(f"RAG system initialization failed: {e}")
        
        # Initialize the coder agent
        web_ui_logger.debug("Initializing coder agent")
        coder_agent = CoderAgent(
            llm_client=llm_client,
            rag_system=rag_system,
            code_analyzer=code_analyzer,
            git_tools=git_tools
        )
        
        # Initialize project context
        try:
            web_ui_logger.debug("Initializing project context")
            run_async(coder_agent.initialize_project_context(workspace_path))
            web_ui_logger.info(f"✅ Coder agent initialized for workspace: {workspace_path}")
        except Exception as e:
            web_ui_logger.warning(f"Coder agent initialization failed: {e}")
        
        web_ui_logger.info(f"Component reinitialization completed successfully for: {workspace_path}")
        return True
        
    except Exception as e:
        web_ui_logger.exception(f"Failed to reinitialize components: {e}")
        return False

if __name__ == '__main__':
    # Initialize components
    init_success = init_components()
    if init_success:
        print("✅ All components initialized successfully")
    else:
        print("⚠️ Some components failed to initialize - check configuration")
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)