#!/usr/bin/env python3
"""
Web UI for the Code Development Assistant.
A Flask-based web interface that provides easy access to all assistant features.
"""
import os
import sys
import asyncio
import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename
import subprocess

# Add the parent directory to the Python path to import the assistant modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from code_dev_assistant.config import get_config, AssistantConfig
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
            asyncio.run(rag_system.initialize())
        except Exception as e:
            print(f"Warning: RAG system initialization failed: {e}")
        
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
        result = asyncio.run(git_tools.execute_git_tool('git_status', {}))
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/git/add', methods=['POST'])
def git_add():
    """Add files to Git staging area."""
    try:
        data = request.get_json()
        files = data.get('files', [])
        
        result = asyncio.run(git_tools.execute_git_tool('git_add', {'files': files}))
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/git/commit', methods=['POST'])
def git_commit():
    """Commit staged changes."""
    try:
        data = request.get_json()
        message = data.get('message', '')
        add_all = data.get('add_all', False)
        
        if not message:
            return jsonify({'success': False, 'error': 'Commit message is required'})
        
        result = asyncio.run(git_tools.execute_git_tool('git_commit', {
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
        result = asyncio.run(git_tools.execute_git_tool('git_branch_list', {}))
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/git/create_branch', methods=['POST'])
def git_create_branch():
    """Create a new Git branch."""
    try:
        data = request.get_json()
        branch_name = data.get('branch_name', '')
        checkout = data.get('checkout', True)
        
        if not branch_name:
            return jsonify({'success': False, 'error': 'Branch name is required'})
        
        result = asyncio.run(git_tools.execute_git_tool('git_create_branch', {
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
        data = request.get_json()
        branch_name = data.get('branch_name', '')
        
        if not branch_name:
            return jsonify({'success': False, 'error': 'Branch name is required'})
        
        result = asyncio.run(git_tools.execute_git_tool('git_checkout', {
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
        data = request.get_json()
        directory = data.get('directory', '.')
        force_reindex = data.get('force_reindex', False)
        
        result = asyncio.run(rag_system.execute_rag_tool('index_codebase', {
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
        data = request.get_json()
        query = data.get('query', '')
        limit = data.get('limit', 5)
        
        if not query:
            return jsonify({'success': False, 'error': 'Search query is required'})
        
        result = asyncio.run(rag_system.execute_rag_tool('search_code', {
            'query': query,
            'limit': limit
        }))
        return jsonify({'success': True, 'output': result[0].text if result else 'No output'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/rag/status')
def rag_status():
    """Get RAG system status."""
    try:
        result = asyncio.run(rag_system.execute_rag_tool('rag_status', {}))
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
        data = request.get_json()
        description = data.get('description', '')
        language = data.get('language', 'python')
        context = data.get('context', '')
        style = data.get('style', 'clean')
        
        if not description:
            return jsonify({'success': False, 'error': 'Code description is required'})
        
        result = asyncio.run(llm_client.execute_llm_tool('generate_code', {
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
        data = request.get_json()
        code = data.get('code', '')
        detail_level = data.get('detail_level', 'medium')
        
        if not code:
            return jsonify({'success': False, 'error': 'Code is required'})
        
        result = asyncio.run(llm_client.execute_llm_tool('explain_code', {
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
        data = request.get_json()
        code = data.get('code', '')
        goals = data.get('goals', [])
        language = data.get('language', 'python')
        
        if not code:
            return jsonify({'success': False, 'error': 'Code is required'})
        
        result = asyncio.run(llm_client.execute_llm_tool('refactor_code', {
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
        data = request.get_json()
        question = data.get('question', '')
        context = data.get('context', '')
        
        if not question:
            return jsonify({'success': False, 'error': 'Question is required'})
        
        result = asyncio.run(llm_client.execute_llm_tool('chat_about_code', {
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
