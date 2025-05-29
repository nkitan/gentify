# Code Development Assistant Docker Deployment

This directory contains Docker deployment configuration for the Code Development Assistant.

## Quick Start

1. **Copy environment file:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Create required directories:**
   ```bash
   mkdir -p logs/{web,mcp,ollama} data/ollama workspace config
   ```

3. **Start the services:**
   ```bash
   # Start main services (Web UI + Ollama)
   docker-compose up -d

   # Or start with all optional services
   docker-compose --profile logging --profile monitoring up -d
   ```

4. **Initialize Ollama model:**
   ```bash
   # Pull the model after Ollama starts
   docker-compose exec ollama ollama pull codellama:7b-instruct
   ```

5. **Access the application:**
   - Web UI: http://localhost:5000
   - Ollama API: http://localhost:11434

## Services

### Core Services

- **code-dev-assistant-web**: Flask web interface on port 5000
- **ollama**: LLM service on port 11434

### Optional Services (use profiles)

- **code-dev-assistant-mcp**: Standalone MCP server (`--profile mcp-standalone`)
- **log-collector**: Centralized logging with Fluentd (`--profile logging`)
- **monitoring**: System monitoring with Node Exporter (`--profile monitoring`)

## Profiles

```bash
# Start only core services
docker-compose up -d

# Start with MCP server
docker-compose --profile mcp-standalone up -d

# Start with logging
docker-compose --profile logging up -d

# Start with monitoring
docker-compose --profile monitoring up -d

# Start everything
docker-compose --profile mcp-standalone --profile logging --profile monitoring up -d
```

## Health Checks

All services include health checks:

```bash
# Check service health
docker-compose ps

# View health check logs
docker-compose logs code-dev-assistant-web
```

## Logging

Logs are configured with rotation:
- **Location**: `./logs/` directory
- **Rotation**: 10MB max size, 5 files retained
- **Format**: JSON structured logs

View logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f code-dev-assistant-web

# Tail recent logs
docker-compose logs --tail=100 -f ollama
```

## Volumes and Data

- **ollama_data**: Ollama models and cache
- **./workspace**: Your code workspace (mounted read-write)
- **./code_rag_db**: RAG database storage
- **./logs**: Application logs
- **./config**: Configuration files

## Resource Management

Default resource limits:
- **Ollama**: 4GB memory limit, 2GB reserved
- **Web UI**: 2GB memory limit, 512MB reserved
- **MCP Server**: 1GB memory limit, 256MB reserved

Modify in `docker-compose.yml` or via environment variables.

## Networking

Services communicate via the `code-dev-network` bridge network:
- Subnet: 172.20.0.0/16
- Internal DNS resolution between services

## Security

- Services run as non-root user
- Network isolation via Docker networks
- Secret management via environment variables
- Read-only configuration mounts where possible

## Troubleshooting

### Service Won't Start
```bash
# Check service status
docker-compose ps

# View service logs
docker-compose logs [service-name]

# Restart specific service
docker-compose restart [service-name]
```

### Ollama Model Issues
```bash
# Check available models
docker-compose exec ollama ollama list

# Pull required model
docker-compose exec ollama ollama pull codellama:7b-instruct

# Test model
docker-compose exec ollama ollama run codellama:7b-instruct "test"
```

### Health Check Failures
```bash
# Run manual health check
docker-compose exec code-dev-assistant-web python healthcheck.py

# Check service connectivity
docker-compose exec code-dev-assistant-web curl -f http://ollama:11434/api/tags
```

### Database Issues
```bash
# Check RAG database
docker-compose exec code-dev-assistant-web ls -la /app/code_rag_db/

# Reset database (removes all indexed data)
docker-compose down
sudo rm -rf ./code_rag_db/*
docker-compose up -d
```

## Development

For development with hot reloading:

```bash
# Override command for development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

Create `docker-compose.dev.yml`:
```yaml
version: '3.8'
services:
  code-dev-assistant-web:
    environment:
      - FLASK_ENV=development
    volumes:
      - .:/app:ro
    command: ["python", "web_ui_runner.py", "--host", "0.0.0.0", "--port", "5000", "--debug"]
```

## Maintenance

### Backup
```bash
# Backup RAG database
tar -czf rag-backup-$(date +%Y%m%d).tar.gz ./code_rag_db/

# Backup Ollama models
tar -czf ollama-backup-$(date +%Y%m%d).tar.gz ./data/ollama/
```

### Updates
```bash
# Update images
docker-compose pull

# Rebuild application
docker-compose build --no-cache

# Restart with updates
docker-compose down && docker-compose up -d
```

### Cleanup
```bash
# Remove containers and networks
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Clean unused images
docker image prune -f
```
