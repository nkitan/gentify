#!/bin/bash
# Docker deployment script for Code Development Assistant

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEFAULT_PROFILES="logging"
REQUIRED_DIRS=("logs/web" "logs/mcp" "logs/ollama" "data/ollama" "workspace" "config")

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE} Code Development Assistant${NC}"
    echo -e "${BLUE} Docker Deployment Script${NC}"
    echo -e "${BLUE}================================${NC}"
    echo
}

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    print_status "Checking requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    print_status "✅ Requirements satisfied"
}

setup_directories() {
    print_status "Setting up directories..."
    
    for dir in "${REQUIRED_DIRS[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_status "Created directory: $dir"
        fi
    done
    
    print_status "✅ Directories ready"
}

setup_environment() {
    print_status "Setting up environment..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_warning "Created .env from .env.example - please review and update"
        else
            print_error ".env.example not found"
            exit 1
        fi
    else
        print_status "✅ .env file exists"
    fi
}

pull_images() {
    print_status "Pulling Docker images..."
    docker-compose pull
    print_status "✅ Images pulled"
}

build_services() {
    print_status "Building application services..."
    docker-compose build
    print_status "✅ Services built"
}

start_services() {
    local profiles="$1"
    print_status "Starting services with profiles: $profiles"
    
    if [ -n "$profiles" ]; then
        docker-compose --profile "$profiles" up -d
    else
        docker-compose up -d
    fi
    
    print_status "✅ Services started"
}

wait_for_services() {
    print_status "Waiting for services to be healthy..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps | grep -q "healthy"; then
            print_status "✅ Services are healthy"
            return 0
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    print_warning "Services may not be fully healthy yet"
    return 1
}

setup_ollama() {
    print_status "Setting up Ollama..."
    
    # Wait for Ollama to be ready
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose exec -T ollama ollama list &> /dev/null; then
            break
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    # Pull the default model
    print_status "Pulling codellama model..."
    if docker-compose exec -T ollama ollama pull codellama:7b-instruct; then
        print_status "✅ Ollama model ready"
    else
        print_warning "Failed to pull model - you can do this manually later"
    fi
}

show_status() {
    print_status "Service status:"
    docker-compose ps
    echo
    
    print_status "Service URLs:"
    echo "🌐 Web UI:        http://localhost:5000"
    echo "🤖 Ollama API:    http://localhost:11434"
    echo "📊 Monitoring:    http://localhost:9100 (if enabled)"
    echo
    
    print_status "Useful commands:"
    echo "📋 View logs:     docker-compose logs -f"
    echo "🔍 Service status: docker-compose ps"
    echo "🛑 Stop services: docker-compose down"
    echo "🔄 Restart:       docker-compose restart [service]"
}

show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -p, --profiles PROFILES  Docker Compose profiles to enable (comma-separated)"
    echo "  -s, --skip-ollama       Skip Ollama model setup"
    echo "  -h, --help              Show this help message"
    echo
    echo "Available profiles:"
    echo "  logging              Enable centralized logging"
    echo "  monitoring           Enable system monitoring"
    echo "  mcp-standalone       Enable standalone MCP server"
    echo "  development          Enable development mode"
    echo
    echo "Examples:"
    echo "  $0                                    # Basic deployment"
    echo "  $0 --profiles logging,monitoring      # With logging and monitoring"
    echo "  $0 --profiles development             # Development mode"
}

main() {
    local profiles=""
    local skip_ollama=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--profiles)
                profiles="$2"
                shift 2
                ;;
            -s|--skip-ollama)
                skip_ollama=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    print_header
    
    # Pre-flight checks
    check_requirements
    setup_directories
    setup_environment
    
    # Deployment
    pull_images
    build_services
    start_services "$profiles"
    
    # Wait for services to be ready
    if wait_for_services; then
        if [ "$skip_ollama" = false ]; then
            setup_ollama
        fi
    fi
    
    # Show final status
    echo
    show_status
    
    print_status "🚀 Deployment complete!"
    echo
    print_status "Next steps:"
    echo "1. Open http://localhost:5000 in your browser"
    echo "2. Upload your code to the workspace directory"
    echo "3. Use the RAG system to index your codebase"
    echo "4. Start developing with AI assistance!"
}

# Run main function
main "$@"
