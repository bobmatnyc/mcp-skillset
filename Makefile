# ============================================================================
# MCP Skills - Main Makefile
# ============================================================================
# Enhanced with python-project-template modular structure
# https://github.com/bobmatnyc/mcp-skills
# ============================================================================

.DEFAULT_GOAL := help

# Include modular Makefile components from template
-include .makefiles/common.mk
-include .makefiles/quality.mk
-include .makefiles/testing.mk
-include .makefiles/deps.mk
-include .makefiles/release.mk

# ============================================================================
# Project Configuration
# ============================================================================
PROJECT_NAME := mcp-skills
PYTHON_VERSION := 3.11
SRC_DIR := src/mcp_skills
TEST_DIR := tests

# ============================================================================
# Project-Specific Targets
# ============================================================================

.PHONY: mcp-server
mcp-server: ## Run the MCP Skills server
	@echo "$(BLUE)Starting MCP Skills server...$(NC)"
	python -m mcp_skills.mcp.server

.PHONY: index
index: ## Build/rebuild the skills index
	@echo "$(BLUE)Indexing skills...$(NC)"
	mcp-skills index

.PHONY: search
search: ## Search skills (usage: make search QUERY="your query")
	@echo "$(BLUE)Searching for: $(QUERY)$(NC)"
	mcp-skills search "$(QUERY)"

# ============================================================================
# Legacy Targets (preserved for compatibility)
# ============================================================================

.PHONY: install
install: ## Install package in development mode
	pip install -e .

.PHONY: dev-install
dev-install: ## Install with dev dependencies
	pip install -e ".[dev]"

.PHONY: lint-fix
lint-fix: ## Auto-fix linting issues (ruff + black)
	@echo "$(BLUE)🔧 Running ruff check with auto-fix...$(NC)"
	ruff check --fix $(SRC_DIR) $(TEST_DIR)
	@echo "$(BLUE)🎨 Running black formatter...$(NC)"
	black $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)✅ Linting and formatting complete$(NC)"

.PHONY: test
test: ## Run tests with coverage
	@echo "$(BLUE)🧪 Running tests with coverage...$(NC)"
	pytest $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)✅ Tests complete$(NC)"

.PHONY: quality
quality: ## Run comprehensive quality checks
	@echo "$(BLUE)📊 Running comprehensive quality checks...$(NC)"
	@echo ""
	@echo "$(YELLOW)1️⃣  Checking code formatting...$(NC)"
	ruff check $(SRC_DIR) $(TEST_DIR)
	black --check $(SRC_DIR) $(TEST_DIR)
	@echo ""
	@echo "$(YELLOW)2️⃣  Running type checks...$(NC)"
	mypy $(SRC_DIR)
	@echo ""
	@echo "$(YELLOW)3️⃣  Running tests with coverage...$(NC)"
	pytest $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=term-missing --cov-fail-under=85
	@echo ""
	@echo "$(GREEN)✅ All quality checks passed$(NC)"

.PHONY: pre-publish
pre-publish: quality ## Quality checks + secret detection
	@echo "$(BLUE)🔐 Running secret detection...$(NC)"
	detect-secrets scan
	@echo "$(GREEN)✅ Pre-publish checks complete$(NC)"

.PHONY: safe-release-build
safe-release-build: pre-publish ## Full quality gate + build
	@echo "$(BLUE)📦 Building distribution packages...$(NC)"
	python -m build
	@echo "$(GREEN)✅ Release build complete$(NC)"
	@echo ""
	@echo "$(BLUE)📦 Distribution files created in dist/$(NC)"
	@ls -lh dist/

.PHONY: clean
clean: ## Remove build artifacts
	@echo "$(BLUE)🧹 Cleaning build artifacts...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✅ Clean complete$(NC)"

# ============================================================================
# Help Target
# ============================================================================

.PHONY: help
help: ## Show this help message
	@echo "$(BLUE)╔════════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║           MCP Skills - Development Commands                   ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Environment:$(NC) ENV=$(ENV) (use: make ENV=production <target>)$(NC)"
	@echo ""
