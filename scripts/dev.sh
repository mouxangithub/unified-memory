#!/bin/bash
# Unified Memory Development Script
# Development environment setup and management



set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="unified-memory"
VERSION="5.2.0"
DEVELOPMENT_PORT=3000
API_PORT=8080

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

log_step() {
    echo -e "${CYAN}▶${NC} $1"
}

# Show help
show_help() {
    echo -e "${CYAN}Unified Memory Development Script${NC}"
    echo
    echo "Usage: $0 [command]"
    echo
    echo "Commands:"
    echo "  setup          Setup development environment"
    echo "  start          Start development server"
    echo "  test           Run tests"
    echo "  lint           Run code linting"
    echo "  format         Format code"
    echo "  clean          Clean build artifacts"
    echo "  all            Run all development tasks"
    echo
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -v, --version  Show version information"
    echo "  --port <port>  Specify development port"
    echo
    echo "Examples:"
    echo "  $0 setup        Setup development environment"
    echo "  $0 start        Start development server"
    echo "  $0 all          Run all development tasks"
}

# Show version
show_version() {
    echo "Unified Memory Development Script v$VERSION"
}

# Setup development environment
setup_environment() {
    log_step "Setting up development environment..."
    
    # Check Node.js version
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed. Please install Node.js >= 18.0.0"
    fi
    
    NODE_VERSION=$(node -v | cut -d'v' -f2)
    log_info "Node.js version: $NODE_VERSION"
    
    # Check npm version
    if ! command -v npm &> /dev/null; then
        log_error "npm is not installed"
    fi
    
    log_info "npm version: $(npm -v)"
    
    # Install development dependencies
    log_info "Installing development dependencies..."
    npm ci --include=dev --no-audit --no-fund
    
    # Setup environment variables
    log_info "Setting up environment variables..."
    if [[ ! -f ".env.development" ]]; then
        cat > .env.development << EOF
# Unified Memory Development Environment
NODE_ENV=development
PORT=$DEVELOPMENT_PORT
API_PORT=$API_PORT
DATABASE_PATH=./data/development.db
LOG_LEVEL=debug
CACHE_ENABLED=true
CACHE_TTL=3600
SEARCH_WEIGHTS_BM25=0.4
SEARCH_WEIGHTS_VECTOR=0.4
SEARCH_WEIGHTS_RRF=0.2
EOF
        log_success "Development environment file created: .env.development"
    else
        log_info "Development environment file already exists"
    fi
    
    # Create data directory
    log_info "Creating data directories..."
    mkdir -p data/{development,test,production}
    mkdir -p logs/{development,test,production}
    
    # Initialize development database
    log_info "Initializing development database..."
    if [[ -f "scripts/init-dev-db.js" ]]; then
        node scripts/init-dev-db.js
    else

        log_info "No database initialization script found"
    fi
    
    log_success "Development environment setup completed"
}

# Start development server
start_development() {
    log_step "Starting development server..."
    
    # Check if dependencies are installed
    if [[ ! -d "node_modules" ]]; then

        log_warning "Dependencies not found, running setup first..."
        setup_environment
    fi
    
    # Set environment variables
    export NODE_ENV=development
    export PORT=$DEVELOPMENT_PORT
    
    # Start development server
    log_info "Starting development server on port $DEVELOPMENT_PORT..."
    log_info "Press Ctrl+C to stop"
    echo
    
    # Use nodemon for development
    if command -v nodemon &> /dev/null; then

        log_info "Using nodemon for hot reload..."
        npx nodemon src/index.js --watch src --ext js,json
    else

        log_info "Using node for development..."
        node src/index.js
    fi
}

# Run tests
run_tests() {
    log_step "Running tests..."
    
    # Run unit tests
    log_info "Running unit tests..."
    npm run test:unit
    
    # Run integration tests
    log_info "Running integration tests..."
    npm run test:integration
    
    # Run coverage report
    log_info "Generating coverage report..."
    npm run test:coverage
    
    log_success "All tests passed"
}

# Run linting
run_linting() {
    log_step "Running code linting..."
    
    # Run ESLint
    log_info "Running ESLint..."
    npm run lint
    
    # Check for formatting issues
    log_info "Checking code formatting..."
    npx prettier --check "src/**/*.{js,jsx,ts,tsx,json,md}" "test/**/*.{js,jsx,ts,tsx,json,md}"
    
    log_success "Code linting completed"
}

# Format code
format_code() {
    log_step "Formatting code..."
    
    # Run Prettier
    log_info "Running Prettier..."
    npx prettier --write "src/**/*.{js,jsx,ts,tsx,json,md}" "test/**/*.{js,jsx,ts,ts,json,md}"
    
    log_success "Code formatting completed"
}

# Clean build artifacts
clean_artifacts() {
    log_step "Cleaning build artifacts..."
    
    # Remove build directories
    rm -rf dist/ build/ coverage/ .nyc_output/
    
    # Remove temporary files
    find . -name "*.log" -type f -delete
    find . -name "*.tmp" -type f -delete
    find . -name "*.bak" -type f -delete
    
    log_success "Build artifacts cleaned"
}

# Run all development tasks
run_all_tasks() {
    log_step "Running all development tasks..."
    
    clean_artifacts
    setup_environment
    run_linting
    format_code
    run_tests
    
    log_success "All development tasks completed"
    log_info "You can now start the development server with: $0 start"
}

# Parse command line arguments
parse_args() {
    COMMAND=""
    CUSTOM_PORT=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            setup|start|test|lint|format|clean|all)
                COMMAND="$1"
                shift
                ;;
            --port)
                CUSTOM_PORT="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--version)
                show_version
                exit 0
                ;;
            *)
                log_error "Unknown argument: $1"
                ;;
        esac
    done
    
    # Set custom port if provided
    if [[ -n "$CUSTOM_PORT" ]]; then

        DEVELOPMENT_PORT="$CUSTOM_PORT"
        log_info "Using custom port: $DEVELOPMENT_PORT"
    fi
}

# Main function
main() {
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║         Unified Memory Development v$VERSION           ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"
    echo
    
    parse_args "$@"
    
    if [[ -z "$COMMAND" ]]; then

        show_help
        exit 0
    fi
    
    case "$COMMAND" in
        "setup")
            setup_environment
            ;;
        "start")
            start_development
            ;;
        "test")
            run_tests
            ;;
        "lint")
            run_linting
            ;;
        "format")
            format_code
            ;;
        "clean")
            clean_artifacts
            ;;
        "all")
            run_all_tasks
            ;;
    esac
}

# Run main function
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then

    main "$@"
fi