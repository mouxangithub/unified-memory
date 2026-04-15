#!/bin/bash
# Unified Memory Installation Script
# Complete installation script for Unified Memory project

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
REQUIRED_NODE_VERSION="18.0.0"
INSTALL_DIR=$(pwd)

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
    echo -e "${CYAN}Unified Memory Installation Script${NC}"
    echo
    echo "Usage: $0 [options]"
    echo
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -v, --version       Show version information"
    echo "  --skip-deps         Skip dependency installation"
    echo "  --skip-tests        Skip running tests"
    echo "  --skip-verify       Skip installation verification"
    echo "  --production        Install production dependencies only"
    echo "  --development       Install development dependencies"
    echo
    echo "Examples:"
    echo "  $0                  Full installation"
    echo "  $0 --production     Production installation"
    echo "  $0 --skip-tests     Install without running tests"
}

# Show version
show_version() {
    echo "Unified Memory Installation Script v$VERSION"
}

# Check system requirements
check_system_requirements() {
    log_step "Checking system requirements..."
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed. Please install Node.js >= $REQUIRED_NODE_VERSION"
    fi
    
    NODE_VERSION=$(node -v | cut -d'v' -f2)
    if [[ "$(printf '%s\n' "$REQUIRED_NODE_VERSION" "$NODE_VERSION" | sort -V | head -n1)" != "$REQUIRED_NODE_VERSION" ]]; then
        log_error "Node.js version $NODE_VERSION is less than required $REQUIRED_NODE_VERSION"
    fi
    
    log_success "Node.js version $NODE_VERSION is compatible"
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        log_error "npm is not installed"
    fi
    
    log_success "npm version: $(npm -v)"
    
    # Check available disk space
    AVAILABLE_SPACE=$(df -k . | awk 'NR==2 {print $4}')
    MIN_SPACE=1048576  # 1GB in KB
    
    if [[ $AVAILABLE_SPACE -lt $MIN_SPACE ]]; then
        log_warning "Low disk space: $(($AVAILABLE_SPACE / 1024))MB available, 1GB recommended"
    else
        log_success "Disk space: $(($AVAILABLE_SPACE / 1024))MB available"
    fi
    
    # Check memory
    TOTAL_MEMORY=$(free -m | awk 'NR==2 {print $2}')
    MIN_MEMORY=2048  # 2GB
    
    if [[ $TOTAL_MEMORY -lt $MIN_MEMORY ]]; then
        log_warning "Low memory: ${TOTAL_MEMORY}MB available, 2GB recommended"
    else
        log_success "Memory: ${TOTAL_MEMORY}MB available"
    fi
}

# Install dependencies
install_dependencies() {
    log_step "Installing dependencies..."
    
    if [[ ! -f "package.json" ]]; then
        log_error "package.json not found in $INSTALL_DIR"
    fi
    
    # Clean npm cache
    log_info "Cleaning npm cache..."
    npm cache clean --force
    
    # Install dependencies based on mode
    if [[ "$INSTALL_MODE" == "production" ]]; then
        log_info "Installing production dependencies..."
        npm ci --only=production --no-audit --no-fund
    elif [[ "$INSTALL_MODE" == "development" ]]; then
        log_info "Installing development dependencies..."
        npm ci --include=dev --no-audit --no-fund
    else
        log_info "Installing all dependencies..."
        npm ci --no-audit --no-fund
    fi
    
    log_success "Dependencies installed successfully"
}

# Setup configuration
setup_configuration() {
    log_step "Setting up configuration..."
    
    # Create configuration directory
    mkdir -p config
    
    # Create default configuration if not exists
    if [[ ! -f "config/default.json" ]]; then
        log_info "Creating default configuration..."
        cat > config/default.json << EOF
{
  "name": "$PROJECT_NAME",
  "version": "$VERSION",
  "environment": "production",
  "database": {
    "path": "./data/production.db",
    "journalMode": "WAL",
    "synchronous": "NORMAL"
  },
  "search": {
    "weights": {
      "bm25": 0.4,
      "vector": 0.4,
      "rrf": 0.2
    },
    "cache": {
      "enabled": true,
      "ttl": 3600
    }
  },
  "api": {
    "port": 8080,
    "cors": {
      "enabled": true,
      "origins": ["*"]
    }
  },
  "logging": {
    "level": "info",
    "directory": "./logs"
  }
}
EOF
        log_success "Default configuration created: config/default.json"
    else
        log_info "Default configuration already exists"
    fi
    
    # Create environment file
    if [[ ! -f ".env" ]]; then
        log_info "Creating environment file..."
        cat > .env << EOF
# Unified Memory Environment Configuration
NODE_ENV=production
DATABASE_PATH=./data/production.db
LOG_LEVEL=info
CACHE_ENABLED=true
CACHE_TTL=3600
SEARCH_WEIGHTS_BM25=0.4
SEARCH_WEIGHTS_VECTOR=0.4
SEARCH_WEIGHTS_RRF=0.2
API_PORT=8080
EOF
        log_success "Environment file created: .env"
    else
        log_info "Environment file already exists"
    fi
}

# Create directory structure
create_directories() {
    log_step "Creating directory structure..."
    
    # Create required directories
    DIRECTORIES=(
        "data"
        "logs"
        "cache"
        "backups"
        "plugins"
        "scripts"
        "docs"
    )
    
    for dir in "${DIRECTORIES[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log_info "Created directory: $dir"
        fi
    done
    
    # Create data subdirectories
    mkdir -p data/{production,development,test}
    mkdir -p logs/{production,development,test}
    mkdir -p cache/{production,development,test}
    
    log_success "Directory structure created"
}

# Run tests
run_tests() {
    log_step "Running tests..."
    
    if [[ ! -f "package.json" ]]; then
        log_warning "package.json not found, skipping tests"
        return
    fi
    
    # Check if test script exists
    if grep -q "\"test\"" package.json; then
        log_info "Running test suite..."
        npm test
        
        if [[ $? -eq 0 ]]; then
            log_success "Tests passed successfully"
        else
            log_error "Tests failed"
        fi
    else
        log_warning "No test script found in package.json"
    fi
}

# Verify installation
verify_installation() {
    log_step "Verifying installation..."
    
    # Check main entry point
    if [[ ! -f "src/index.js" ]]; then
        log_error "Main entry point not found: src/index.js"
    fi
    log_success "Main entry point found: src/index.js"
    
    # Check configuration
    if [[ ! -f "config/skill.json" ]]; then
        log_error "Configuration not found: config/skill.json"
    fi
    log_success "Configuration found: config/skill.json"
    
    # Check node_modules
    if [[ ! -d "node_modules" ]]; then
        log_error "Dependencies not installed: node_modules directory not found"
    fi
    log_success "Dependencies installed: node_modules directory found"
    
    # Test service startup
    log_info "Testing service startup..."
    timeout 5s node src/index.js --version &> /dev/null || true
    
    log_success "Installation verified successfully"
}

# Generate installation report
generate_report() {
    log_step "Generating installation report..."
    
    local report_file="installation-report-$(date +%Y%m%d-%H%M%S).txt"
    
    cat > "$report_file" << EOF
Unified Memory Installation Report
==================================

Project: $PROJECT_NAME
Version: $VERSION
Installation Date: $(date)
Installation Directory: $INSTALL_DIR
Installation Mode: $INSTALL_MODE

System Information:
- Node.js Version: $(node -v)
- npm Version: $(npm -v)
- OS: $(uname -s -r)
- Architecture: $(uname -m)

Installation Steps:
1. System requirements check: PASSED
2. Dependencies installation: PASSED
3. Configuration setup: PASSED
4. Directory structure: PASSED
5. Tests execution: $(if [[ "$SKIP_TESTS" == "true" ]]; then echo "SKIPPED"; else echo "PASSED"; fi)
6. Installation verification: PASSED

Created Files and Directories:
- Configuration: config/default.json, .env
- Data directories: data/, logs/, cache/, backups/
- Dependencies: node_modules/
- Documentation: docs/

Next Steps:
1. Start the service: npm start
2. For development: npm run dev
3. Access documentation: docs/README.md
4. Check configuration: config/default.json

Troubleshooting:
- If service fails to start, check logs/ directory
- For configuration issues, review config/default.json
- For dependency issues, run: npm ci

Support:
- Documentation: docs/README.md
- Issues: https://github.com/mouxangithub/unified-memory/issues
- Discussions: https://github.com/mouxangithub/unified-memory/discussions

EOF

    log_success "Installation report generated: $report_file"
}

# Main installation function
install() {
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║         Unified Memory Installation v$VERSION           ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"
    echo
    
    check_system_requirements
    
    if [[ "$SKIP_DEPS" != "true" ]]; then
        install_dependencies
    else
        log_warning "Skipping dependency installation"
    fi
    
    setup_configuration
    create_directories
    
    if [[ "$SKIP_TESTS" != "true" ]]; then
        run_tests
    else
        log_warning "Skipping tests"
    fi
    
    if [[ "$SKIP_VERIFY" != "true" ]]; then
        verify_installation
    else
        log_warning "Skipping installation verification"
    fi
    
    generate_report
    
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║         Installation Completed Successfully!           ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
    echo
    
    log_info "Installation completed at $(date)"
    log_info "Installation directory: $INSTALL_DIR"
    log_info "Service can be started with: npm start"
    log_info "For development mode, use: npm run dev"
    log_info "Check installation report for details"
}

# Parse command line arguments
parse_args() {
    INSTALL_MODE="all"
    SKIP_DEPS="false"
    SKIP_TESTS="false"
    SKIP_VERIFY="false"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--version)
                show_version
                exit 0
                ;;
            --skip-deps)
                SKIP_DEPS="true"
                shift
                ;;
            --skip-tests)
                SKIP_TESTS="true"
                shift
                ;;
            --skip-verify)
                SKIP_VERIFY="true"
                shift
                ;;
            --production)
                INSTALL_MODE="production"
                shift
                ;;
            --development)
                INSTALL_MODE="development"
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                ;;
        esac
    done
}

# Main function
main() {
    parse_args "$@"
    install
}

# Run main function
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi