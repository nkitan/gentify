# Code Development Assistant Web UI

A modern, intuitive web interface for the Code Development Assistant that provides AI-powered coding tools, Git integration, and semantic code search.

## Features

### 🎯 Dashboard
- **System Status Overview**: Real-time status of Git repository, RAG index, LLM connection, and workspace
- **Quick Actions**: One-click access to all major features
- **Workspace Statistics**: File counts, lines of code, commits, and branches

### 🤖 AI-Powered Tools (`/llm`)
- **Code Generation**: Generate code from natural language descriptions
- **Code Explanation**: Get detailed explanations of existing code
- **Code Refactoring**: Improve code quality with AI suggestions
- **Multiple Languages**: Support for Python, JavaScript, TypeScript, Java, C++, Rust, Go

### 💬 Interactive Chat (`/chat`)
- **Conversational AI**: Ask questions about your code in natural language
- **Context-Aware**: Include code snippets for better assistance
- **Quick Templates**: Pre-built prompts for common tasks
- **Session Management**: Track conversation history

### 🔍 Semantic Code Search (`/rag`)
- **Intelligent Indexing**: Build searchable indexes of your codebase
- **Semantic Search**: Find code by meaning, not just keywords
- **Status Monitoring**: Track indexing progress and database status

### 🔧 Git Integration (`/git`)
- **Repository Management**: View status, branches, and commit history
- **Branch Operations**: Create, switch, and manage branches
- **Commit Operations**: Stage changes and create commits
- **Visual Interface**: User-friendly Git operations

### ⚙️ Settings & Configuration (`/settings`)
- **System Configuration**: View and manage assistant settings
- **Health Monitoring**: Check component status and connectivity
- **Troubleshooting**: Built-in diagnostics and logging
- **Configuration Guide**: Step-by-step setup instructions

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install flask
   ```

2. **Configure the Assistant**:
   Create a config file at `~/.config/code-dev-assistant/config.toml`:
   ```toml
   [workspace]
   path = "/path/to/your/project"
   
   [llm]
   model = "llama3.2:latest"
   base_url = "http://localhost:11434"
   
   [rag]
   db_path = "./code_rag.db"
   embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
   
   [logging]
   level = "INFO"
   ```

3. **Start the Web Server**:
   ```bash
   cd web_ui
   python app.py
   ```

4. **Open Your Browser**:
   Navigate to `http://localhost:5000`

## Architecture

### Frontend
- **Framework**: HTML5, CSS3 (Tailwind CSS), JavaScript (ES6+)
- **UI Components**: Modern, responsive design with mobile support
- **Icons**: Font Awesome for consistent iconography
- **Interactions**: Real-time updates and smooth animations

### Backend
- **Framework**: Flask (Python web framework)
- **API Design**: RESTful endpoints for all operations
- **Error Handling**: Comprehensive error reporting and recovery
- **Async Support**: Async/await for non-blocking operations

### Integration
- **Code Assistant**: Direct integration with all assistant components
- **Real-time Updates**: Live status monitoring and feedback
- **Cross-platform**: Works on Windows, macOS, and Linux

## API Endpoints

### Git Operations
- `GET /api/git/status` - Get repository status
- `POST /api/git/add` - Stage files
- `POST /api/git/commit` - Create commit
- `GET /api/git/branches` - List branches
- `POST /api/git/create_branch` - Create new branch
- `POST /api/git/checkout` - Switch branches

### RAG System
- `POST /api/rag/index` - Index codebase
- `POST /api/rag/search` - Search code
- `GET /api/rag/status` - Get RAG status

### LLM Tools
- `POST /api/llm/generate` - Generate code
- `POST /api/llm/explain` - Explain code
- `POST /api/llm/refactor` - Refactor code

### Chat Interface
- `POST /api/chat` - Send chat message

### System
- `GET /api/config` - Get configuration

## Customization

### Themes
The UI uses Tailwind CSS classes for easy customization. Modify the color scheme by updating the CSS classes in the templates.

### Adding Features
1. Add new API endpoints in `app.py`
2. Create corresponding frontend components
3. Update navigation in `base.html`

### Extending Functionality
The modular design allows easy extension:
- Add new tool categories
- Integrate additional AI models
- Extend Git operations
- Add new search capabilities

## Troubleshooting

### Common Issues
1. **LLM Connection Failed**: Ensure your LLM server is running and accessible
2. **Git Repository Not Found**: Check workspace path configuration
3. **RAG Index Issues**: Verify database permissions and embedding model availability

### Debug Mode
Run with debug mode for detailed error information:
```bash
export FLASK_DEBUG=1
python app.py
```

### Logs
Check browser console and server logs for detailed error information.

## Development

### Project Structure
```
web_ui/
├── app.py              # Main Flask application
├── templates/          # HTML templates
│   ├── base.html       # Base template with navigation
│   ├── index.html      # Dashboard
│   ├── git.html        # Git operations
│   ├── rag.html        # Code search
│   ├── llm.html        # AI tools
│   ├── chat.html       # Chat interface
│   └── settings.html   # Configuration
└── static/             # Static assets (if needed)
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the Code Development Assistant and follows the same license terms.
