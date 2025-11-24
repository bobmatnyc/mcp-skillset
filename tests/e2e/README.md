# End-to-End (E2E) Tests for mcp-skills

This directory contains comprehensive end-to-end tests for the mcp-skills project, covering all CLI commands, MCP tools, and complete workflows.

## Test Organization

### Test Files

1. **test_cli_commands.py** (20+ tests)
   - Tests all 11 CLI commands with real invocations
   - Uses Click's CliRunner for command execution
   - Verifies exit codes, output formatting, and error handling
   - Commands tested:
     - `mcp-skills setup` (auto and interactive modes)
     - `mcp-skills mcp` (serve)
     - `mcp-skills search`
     - `mcp-skills list`
     - `mcp-skills info`
     - `mcp-skills recommend`
     - `mcp-skills repo add/list/update`
     - `mcp-skills index`
     - `mcp-skills health`
     - `mcp-skills stats`
     - `mcp-skills config`

2. **test_mcp_tools.py** (25+ tests)
   - Tests all 5 MCP tools via direct function calls
   - Verifies JSON response structures and error handling
   - Tools tested:
     - `search_skills` (hybrid RAG search)
     - `get_skill` (retrieve skill details)
     - `recommend_skills` (project and skill-based)
     - `list_categories` (list skill categories)
     - `reindex_skills` (rebuild indices)

3. **test_skill_autodetect.py** (15+ tests)
   - Tests skill auto-detection workflows
   - Covers Python, TypeScript, and multi-language projects
   - Verifies toolchain detection accuracy
   - Tests recommendation relevance

4. **test_repository_workflows.py** (20+ tests)
   - Tests complete repository management lifecycle
   - Real git operations and file I/O
   - Workflows tested:
     - Add repository
     - List repositories
     - Index skills from repository
     - Search skills by repository
     - Update repository
     - Remove repository

## Test Fixtures

Located in `conftest.py`:

- **e2e_base_dir**: Temporary base directory mimicking ~/.mcp-skills
- **e2e_repos_dir**: E2E repositories directory
- **e2e_storage_dir**: E2E storage directory (ChromaDB, etc.)
- **cli_runner**: Click CliRunner for CLI testing
- **real_skill_repo**: Realistic git repository with 5 skills
- **e2e_configured_services**: Fully configured services (RepositoryManager, SkillManager, IndexingEngine)
- **e2e_services_with_repo**: Services with a real repository pre-loaded and indexed
- **sample_python_project_e2e**: Complete Python project with Flask and pytest
- **sample_typescript_project_e2e**: Complete TypeScript project with Jest

## Running E2E Tests

### Run All E2E Tests
```bash
pytest tests/e2e/ -v
```

### Run Specific Test File
```bash
pytest tests/e2e/test_cli_commands.py -v
pytest tests/e2e/test_mcp_tools.py -v
pytest tests/e2e/test_skill_autodetect.py -v
pytest tests/e2e/test_repository_workflows.py -v
```

### Run Specific Test Class
```bash
pytest tests/e2e/test_cli_commands.py::TestCLISearchCommand -v
pytest tests/e2e/test_mcp_tools.py::TestMCPSearchSkills -v
```

### Run Specific Test
```bash
pytest tests/e2e/test_cli_commands.py::TestCLISearchCommand::test_search_with_results -v
```

### Run E2E Tests Only (using marker)
```bash
pytest -m e2e -v
```

### Run with Coverage
```bash
pytest tests/e2e/ --cov=src/mcp_skills --cov-report=html
```

### Run Async Tests Only
```bash
pytest tests/e2e/ -m asyncio -v
```

## Test Characteristics

### Real Operations
- **Real file I/O**: Creates actual files, directories, and git repositories
- **Real CLI invocations**: Uses Click's CliRunner for authentic command execution
- **Real indexing**: Builds actual ChromaDB vector stores and NetworkX graphs
- **Real search**: Performs genuine hybrid RAG searches

### No Mocking
- E2E tests avoid mocking to ensure production readiness
- Services are configured with real instances
- File operations use actual file system
- Git operations use real git library

### Performance
- Most tests complete in <1 second
- Full E2E suite runs in <30 seconds
- Uses temporary directories for isolation
- Parallel test execution safe (isolated fixtures)

## Test Coverage

### CLI Commands
- ✅ All 11 CLI commands tested
- ✅ Help output verification
- ✅ Error handling
- ✅ Exit codes
- ✅ Output formatting

### MCP Tools
- ✅ All 5 MCP tools tested
- ✅ Response structure validation
- ✅ Error responses
- ✅ Edge cases (empty queries, invalid IDs)
- ✅ Filter functionality (toolchain, category, tags)

### Workflows
- ✅ Auto-detection (Python, TypeScript, multi-language)
- ✅ Repository lifecycle (add, list, index, search, update, remove)
- ✅ Search workflows (basic, filtered, ranked)
- ✅ Recommendation workflows (project-based, skill-based)

## Debugging Tests

### View Test Output
```bash
pytest tests/e2e/ -v -s
```

### Stop on First Failure
```bash
pytest tests/e2e/ -x
```

### Run Failed Tests Only
```bash
pytest tests/e2e/ --lf
```

### Detailed Traceback
```bash
pytest tests/e2e/ --tb=long
```

### Show Captured Logs
```bash
pytest tests/e2e/ -v --log-cli-level=DEBUG
```

## Continuous Integration

E2E tests are designed to run in CI environments:
- No external network dependencies (uses local git repos)
- No authentication required
- Isolated temporary directories
- Deterministic results
- Fast execution (<30s total)

## Contributing

When adding new E2E tests:

1. **Use descriptive names**: Test name should describe the scenario
2. **Document workflows**: Add workflow steps in docstrings
3. **Verify end-to-end**: Test complete flows, not just happy paths
4. **Use real operations**: Avoid mocking unless absolutely necessary
5. **Keep tests fast**: Optimize fixture usage
6. **Add markers**: Use `@pytest.mark.e2e` and `@pytest.mark.asyncio` as needed
7. **Test error cases**: Include negative test cases
8. **Verify output**: Check exit codes, response structures, and data

## Related Documentation

- [Integration Tests](../integration/README.md) - Component integration tests
- [Unit Tests](../) - Individual component tests
- [Linear Ticket 1M-137](https://linear.app/project/1M-137) - Original requirements
