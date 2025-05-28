#!/usr/bin/env python3
"""
Code Development Assistant Web UI Validator
==========================================

This script validates the complete setup of the Web UI, including:
- File structure and templates
- Dependencies and imports
- Configuration and environment
- Basic functionality tests

Usage:
    python web_ui_validator.py [--verbose] [--fix]

Options:
    --verbose    Show detailed output
    --fix        Attempt to fix simple issues automatically
"""
import os
import sys
import argparse
import json
from pathlib import Path

def validate_project_structure(verbose=False):
    """Validate the overall project structure."""
    print("🔍 Validating Project Structure...")
    
    base_path = Path(__file__).parent
    required_structure = {
        'directories': [
            'src/code_dev_assistant',
            'web_ui',
            'web_ui/templates'
        ],
        'files': {
            'src/code_dev_assistant/__init__.py': 'Package init',
            'src/code_dev_assistant/config.py': 'Configuration module',
            'src/code_dev_assistant/git_tools.py': 'Git tools',
            'src/code_dev_assistant/rag_system.py': 'RAG system',
            'src/code_dev_assistant/llm_client.py': 'LLM client',
            'web_ui/app.py': 'Flask application',
            'web_ui/templates/base.html': 'Base template',
            'web_ui/templates/index.html': 'Dashboard template',
            'web_ui/templates/git.html': 'Git interface template',
            'web_ui/templates/rag.html': 'RAG search template',
            'web_ui/templates/llm.html': 'AI tools template',
            'web_ui/templates/chat.html': 'Chat interface template',
            'web_ui/templates/settings.html': 'Settings template',
            '.env': 'Environment configuration',
            'pyproject.toml': 'Project configuration'
        }
    }
    
    all_good = True
    
    # Check directories
    for directory in required_structure['directories']:
        dir_path = base_path / directory
        if dir_path.exists() and dir_path.is_dir():
            if verbose:
                print(f"✅ Directory: {directory}")
        else:
            print(f"❌ Missing directory: {directory}")
            all_good = False
    
    # Check files
    for file_path, description in required_structure['files'].items():
        full_path = base_path / file_path
        if full_path.exists() and full_path.is_file():
            size = full_path.stat().st_size
            if verbose:
                print(f"✅ {file_path:<35} ({size:,} bytes) - {description}")
            elif size < 50:  # Warn about very small files
                print(f"⚠️  {file_path:<35} ({size:,} bytes) - {description} (very small)")
        else:
            print(f"❌ Missing file: {file_path} - {description}")
            all_good = False
    
    return all_good

def validate_dependencies(verbose=False):
    """Validate required Python dependencies."""
    print("\n🔍 Validating Dependencies...")
    
    core_dependencies = {
        'flask': 'Web framework',
        'pathlib': 'Path handling (built-in)',
        'json': 'JSON processing (built-in)',
        'os': 'OS interface (built-in)',
        'sys': 'System interface (built-in)'
    }
    
    optional_dependencies = {
        'gitpython': 'Git operations',
        'langchain': 'LLM framework',
        'sentence_transformers': 'Embeddings'
    }
    
    all_good = True
    
    # Check core dependencies
    for package, description in core_dependencies.items():
        try:
            __import__(package)
            if verbose:
                print(f"✅ {package:<20} - {description}")
        except ImportError:
            print(f"❌ {package:<20} - {description} (REQUIRED)")
            all_good = False
    
    # Check optional dependencies
    for package, description in optional_dependencies.items():
        try:
            __import__(package)
            if verbose:
                print(f"✅ {package:<20} - {description}")
        except ImportError:
            if verbose:
                print(f"⚠️  {package:<20} - {description} (optional, limited functionality)")
    
    return all_good

def validate_configuration(verbose=False):
    """Validate configuration files and environment."""
    print("\n🔍 Validating Configuration...")
    
    base_path = Path(__file__).parent
    all_good = True
    
    # Check .env file
    env_file = base_path / '.env'
    if env_file.exists():
        if verbose:
            print("✅ .env file exists")
        
        # Check key environment variables
        env_content = env_file.read_text()
        required_vars = ['WORKSPACE_PATH', 'LLM_BASE_URL', 'LLM_MODEL']
        
        for var in required_vars:
            if var in env_content:
                if verbose:
                    print(f"✅ Environment variable: {var}")
            else:
                print(f"⚠️  Missing environment variable: {var}")
    else:
        print("⚠️  .env file not found (will use defaults)")
    
    # Check pyproject.toml
    pyproject_file = base_path / 'pyproject.toml'
    if pyproject_file.exists():
        if verbose:
            print("✅ pyproject.toml exists")
        
        content = pyproject_file.read_text()
        if 'flask' in content:
            if verbose:
                print("✅ Flask listed in dependencies")
        else:
            print("⚠️  Flask not found in pyproject.toml dependencies")
    
    return all_good

def validate_templates(verbose=False):
    """Validate HTML template files."""
    print("\n🔍 Validating Templates...")
    
    base_path = Path(__file__).parent / 'web_ui' / 'templates'
    template_requirements = {
        'base.html': ['<!DOCTYPE html>', '<html', '</html>'],
        'index.html': ['{% extends "base.html" %}', '{% block content %}'],
        'git.html': ['{% extends "base.html" %}', 'git'],
        'rag.html': ['{% extends "base.html" %}', 'rag'],
        'llm.html': ['{% extends "base.html" %}', 'llm'],
        'chat.html': ['{% extends "base.html" %}', 'chat'],
        'settings.html': ['{% extends "base.html" %}', 'settings']
    }
    
    all_good = True
    
    for template, required_content in template_requirements.items():
        template_path = base_path / template
        
        if not template_path.exists():
            print(f"❌ Missing template: {template}")
            all_good = False
            continue
        
        content = template_path.read_text()
        missing_content = []
        
        for requirement in required_content:
            if requirement not in content:
                missing_content.append(requirement)
        
        if missing_content:
            print(f"⚠️  {template}: missing {', '.join(missing_content)}")
        elif verbose:
            print(f"✅ {template}: valid template")
    
    return all_good

def test_import_capability():
    """Test if the web UI components can be imported."""
    print("\n🔍 Testing Import Capability...")
    
    # Add src to path
    src_path = Path(__file__).parent / 'src'
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    import_tests = [
        ('code_dev_assistant.config', 'Configuration module'),
        ('flask', 'Flask framework')
    ]
    
    all_good = True
    
    for module, description in import_tests:
        try:
            __import__(module)
            print(f"✅ Import test: {module} - {description}")
        except ImportError as e:
            print(f"❌ Import test failed: {module} - {e}")
            all_good = False
    
    return all_good

def generate_status_report(results, base_path):
    """Generate a status report."""
    print("\n📋 Generating Status Report...")
    
    report = {
        'timestamp': str(Path(__file__).stat().st_mtime),
        'validation_results': results,
        'recommendations': []
    }
    
    # Add recommendations based on results
    if not results['structure']:
        report['recommendations'].append("Fix missing files and directories")
    
    if not results['dependencies']:
        report['recommendations'].append("Install missing dependencies with: uv pip install flask")
    
    if not results['templates']:
        report['recommendations'].append("Check template files for required content")
    
    if not results['imports']:
        report['recommendations'].append("Verify Python path and module structure")
    
    # Write report
    report_file = base_path / 'web_ui_validation_report.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"📄 Report saved to: {report_file}")

def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(
        description='Code Development Assistant Web UI Validator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Show detailed output')
    parser.add_argument('--fix', action='store_true',
                      help='Attempt to fix simple issues')
    
    args = parser.parse_args()
    
    print("Code Development Assistant Web UI Validator")
    print("=" * 45)
    
    base_path = Path(__file__).parent
    
    # Run all validation tests
    results = {
        'structure': validate_project_structure(args.verbose),
        'dependencies': validate_dependencies(args.verbose),
        'configuration': validate_configuration(args.verbose),
        'templates': validate_templates(args.verbose),
        'imports': test_import_capability()
    }
    
    # Generate status report
    generate_status_report(results, base_path)
    
    # Summary
    print("\n" + "=" * 45)
    passed = sum(results.values())
    total = len(results)
    
    if passed == total:
        print(f"🎉 All validation tests passed! ({passed}/{total})")
        print("\n🚀 Your Web UI is ready to run!")
        print("   Use: python web_ui_runner.py")
    else:
        print(f"⚠️  {passed}/{total} validation tests passed")
        print("\n🔧 Issues found that need attention:")
        
        for test_name, result in results.items():
            if not result:
                print(f"   - {test_name.title()} validation failed")
        
        print("\n📋 See web_ui_validation_report.json for details")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
