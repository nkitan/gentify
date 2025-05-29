# Docker Deployment Guide

## Overview

This docker-compose setup provides a complete deployment of the Code Development Assistant with:

- **Web UI Service**: Flask-based web interface on port 5000
- **Ollama Service**: LLM backend for code analysis and generation
- **Health Checks**: Comprehensive health monitoring for all services  
- **Logging**: Structured logging with rotation and aggregation
- **Monitoring**: Optional system monitoring with Node Exporter
- **MCP Server**: Optional standalone MCP server for external clients

## Quick Start

1. **Run the deployment script:**
   ```bash
   ./deploy.sh
   ```

2. **Or manually:**
   ```bash
   # Copy environment file
   cp .env.example .env
   
   # Create required directories  
   mkdir -p logs/{web,mcp,ollama} data/ollama workspace config
   
   # Start services
   docker-compose up -d
   
   # Setup Ollama model
   docker-compose exec ollama ollama pull codellama:7b-instruct
   ```

3. **Access the application:**
   - Web UI: http://localhost:5000
   - Ollama API: http://localhost:11434

## Services Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web UI        │    │   MCP Server    │    │   Ollama LLM    │
│   (Port 5000)   │◄──►│   (Internal)    │◄──►│   (Port 11434)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   RAG Database  │
                    │   (LanceDB)     │
                    └─────────────────┘
```

## Health Checks

All services include comprehensive health checks:

### Web UI Health Check
- **Endpoint**: HTTP GET `/`
- **Interval**: 30s
- **Timeout**: 15s
- **Retries**: 3

### Ollama Health Check  
- **Endpoint**: HTTP GET `/api/tags`
- **Interval**: 30s
- **Timeout**: 10s
- **Retries**: 3

### MCP Server Health Check
- **Script**: Custom Python health check
- **Interval**: 30s
- **Tests**: Configuration validation, database access

## Logging Configuration

### Log Structure
```
logs/
├── web/           # Web UI logs
├── mcp/           # MCP server logs  
├── ollama/        # Ollama service logs
└── general/       # Aggregated logs (with fluentd profile)
```

### Log Rotation
- **Max Size**: 10MB per file
- **Max Files**: 5 files retained
- **Format**: JSON structured logging

### Viewing Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f code-dev-assistant-web

# Tail recent logs
docker-compose logs --tail=100 -f ollama

# Search logs
docker-compose logs | grep ERROR
```

## Profiles

Use profiles to enable optional services:

```bash
# Basic deployment (Web UI + Ollama)
docker-compose up -d

# With logging aggregation
docker-compose --profile logging up -d

# With monitoring
docker-compose --profile monitoring up -d

# With standalone MCP server
docker-compose --profile mcp-standalone up -d

# Everything enabled
docker-compose --profile logging --profile monitoring --profile mcp-standalone up -d
```

## Environment Variables

Configure via `.env` file:

```bash
# Application
SECRET_KEY=your-production-secret-key
LOG_LEVEL=INFO

# Ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=codellama:7b-instruct

# Resources
OLLAMA_MEMORY_LIMIT=4G
WEB_MEMORY_LIMIT=2G
```

## Resource Management

### Default Limits
- **Ollama**: 4GB memory limit, 2GB reserved
- **Web UI**: 2GB memory limit, 512MB reserved  
- **MCP Server**: 1GB memory limit, 256MB reserved

### Monitoring Resource Usage
```bash
# Check resource usage
docker stats

# Service-specific stats
docker stats code-dev-assistant-web
```

## Data Persistence

### Volumes
- **ollama_data**: Ollama models and cache
- **./workspace**: Your code workspace (bind mount)
- **./code_rag_db**: RAG database storage (bind mount)
- **./logs**: Application logs (bind mount)

### Backup Strategy
```bash
# Backup RAG database
tar -czf rag-backup-$(date +%Y%m%d).tar.gz ./code_rag_db/

# Backup Ollama models  
tar -czf ollama-backup-$(date +%Y%m%d).tar.gz ./data/ollama/

# Backup configuration
tar -czf config-backup-$(date +%Y%m%d).tar.gz ./config/ .env
```

## Security Features

- **Non-root execution**: All services run as non-root users
- **Network isolation**: Services communicate via private Docker network
- **Secret management**: Secrets via environment variables
- **Resource limits**: Prevent resource exhaustion attacks
- **Health monitoring**: Automatic restart on failures

## Troubleshooting

### Service Won't Start
```bash
# Check service status
docker-compose ps

# View startup logs
docker-compose logs code-dev-assistant-web

# Check health status
docker inspect code-dev-assistant-web | grep Health -A 10
```

### Ollama Issues
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# List available models
docker-compose exec ollama ollama list

# Pull required model
docker-compose exec ollama ollama pull codellama:7b-instruct

# Test model
docker-compose exec ollama ollama run codellama:7b-instruct "Hello"
```

### Health Check Failures
```bash
# Manual health check
docker-compose exec code-dev-assistant-web python healthcheck.py

# Check service connectivity
docker-compose exec code-dev-assistant-web curl -f http://ollama:11434/api/tags

# Restart unhealthy service
docker-compose restart code-dev-assistant-web
```

### Database Issues
```bash
# Check RAG database
ls -la ./code_rag_db/

# Reset database (WARNING: deletes all indexed data)
docker-compose down
rm -rf ./code_rag_db/*
docker-compose up -d
```

### Network Issues
```bash
# Check network connectivity
docker network ls
docker network inspect gentify_code-dev-network

# Test internal DNS
docker-compose exec code-dev-assistant-web nslookup ollama
```

## Development Mode

For development with hot reloading:

```bash
# Start in development mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Or use the development profile
docker-compose --profile development up -d
```

Development features:
- **Hot reloading**: Source code mounted as volumes
- **Debug mode**: Flask debug mode enabled
- **Enhanced logging**: Debug level logging
- **Development database**: Optional PostgreSQL for testing

## Production Considerations

### Performance Tuning
1. **Ollama Model Size**: Choose appropriate model size for your hardware
2. **Memory Limits**: Adjust based on available system resources
3. **Concurrency**: Configure worker processes for web UI
4. **Database**: Consider external database for high load

### Security Hardening
1. **Change default secrets**: Update SECRET_KEY and other sensitive values
2. **Network security**: Use reverse proxy with SSL termination
3. **Access control**: Implement authentication for web UI
4. **Resource monitoring**: Set up monitoring and alerting

### Scaling
```bash
# Scale web UI instances
docker-compose up -d --scale code-dev-assistant-web=3

# Use external load balancer for distribution
```

## Maintenance

### Updates
```bash
# Update images
docker-compose pull

# Rebuild services
docker-compose build --no-cache

# Rolling restart
docker-compose restart
```

### Cleanup
```bash
# Stop services
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Clean unused images
docker image prune -f
```

### Monitoring
```bash
# Service health
watch 'docker-compose ps'

# Resource usage
watch 'docker stats --no-stream'

# Log monitoring
tail -f logs/web/*.log
```

## Support

For issues and questions:
1. Check health check status: `docker-compose ps`
2. Review service logs: `docker-compose logs [service]`
3. Run manual health checks: `docker-compose exec [service] python healthcheck.py`
4. Check resource usage: `docker stats`
