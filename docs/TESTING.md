# Testing Strategy for PAPR Voice Demo

## Overview

Comprehensive unit testing for both Python and TypeScript components, ensuring reliability and maintainability throughout the migration to Pipecat.

---

## 🐍 Python Testing Stack

### Tools & Dependencies

**Test Framework:** pytest 8.0+
**Coverage:** pytest-cov
**Mocking:** pytest-mock
**Async Testing:** pytest-asyncio

**Code Quality:**
- black (formatting)
- isort (import sorting)
- flake8 (linting)
- mypy (type checking)

### Test Files

#### 1. `tests/test_tool_schemas.py`

**Purpose:** Test Pydantic validation and OpenAI schema generation

**Test Coverage:**
- ✅ Valid parameter validation (minimal & full)
- ✅ Required field enforcement
- ✅ Default value application
- ✅ Boolean coercion
- ✅ OpenAI schema structure
- ✅ Schema property alignment
- ✅ Required field marking
- ✅ Description quality
- ✅ Pydantic-to-OpenAI consistency

**Key Tests:**
```python
def test_valid_minimal_params():
    """Test with only required parameter (query)"""
    params = SearchMemoryToolParams(query="test query")
    assert params.query == "test query"
    assert params.enable_agentic_graph == False

def test_schema_structure():
    """Test that schema has correct OpenAI structure"""
    schema = get_search_memory_tool_schema()
    assert schema['type'] == 'function'
    assert schema['name'] == 'search_papr_memories'
```

#### 2. `tests/test_voice_server.py`

**Purpose:** Test Flask endpoints, latency tracking, and search history

**Test Coverage:**
- ✅ Static file serving (/, /logo.svg)
- ✅ API keys endpoint structure and values
- ✅ Tool schema endpoint validation
- ✅ Search history structure and limits
- ✅ Search endpoint validation
- ✅ Pydantic parameter validation
- ✅ Latency breakdown calculation
- ✅ Search history storage (max 30)
- ✅ Agentic graph parameter passing
- ✅ rank_results=true enforcement
- ✅ Memory formatting

**Key Tests:**
```python
def test_search_successful(client, mock_papr_response):
    """Test successful search with latency tracking"""
    response = client.post('/api/search',
        data=json.dumps({'query': 'test query'}),
        content_type='application/json')

    data = json.loads(response.data)
    assert 'latency_breakdown' in data
    assert data['latency_breakdown']['total_ms'] > 0

def test_search_history_max_30_searches(client):
    """Test that history is limited to 30 searches"""
    # Perform 35 searches
    for i in range(35):
        client.post('/api/search', ...)

    history = client.get('/api/search-history')
    assert len(history['searches']) == 30
```

---

## 📘 TypeScript Testing Stack

### Tools & Dependencies

**Test Framework:** Jest 29.7+
**TypeScript Support:** ts-jest
**HTTP Mocking:** nock
**Coverage:** Built-in Jest coverage

### Test Files

#### 1. `src/server/src/services/PaprMemoryService.test.ts`

**Purpose:** Test TypeScript service layer communicating with Python microservice

**Test Coverage:**
- ✅ Constructor configuration (default & custom)
- ✅ Search functionality with all parameters
- ✅ enable_agentic_graph parameter handling
- ✅ rank_results=true enforcement for CoreML
- ✅ Timeout handling
- ✅ Error handling (HTTP errors, network errors)
- ✅ Message storage with API key validation
- ✅ Search history retrieval
- ✅ API keys fetching
- ✅ Tool schema fetching
- ✅ Health check functionality

**Key Tests:**
```typescript
it('should always set rank_results to true for CoreML optimization', async () => {
  nock(pythonServiceUrl)
    .post('/api/search', (body) => {
      return body.rank_results === true;
    })
    .reply(200, mockSearchResponse);

  await service.search({ query: 'test' });
  expect(nock.isDone()).toBe(true);
});

it('should handle timeout', async () => {
  const slowService = new PaprMemoryService({ timeout: 100 });

  nock(pythonServiceUrl)
    .post('/api/search')
    .delay(200)
    .reply(200, mockSearchResponse);

  await expect(slowService.search({ query: 'test' }))
    .rejects.toThrow(/timeout/);
});
```

---

## 🚀 Running Tests

### Python Tests

```bash
# Using Poetry (recommended)
poetry run pytest tests/ -v --cov=src/python --cov-report=term-missing

# With coverage HTML report
poetry run pytest tests/ --cov=src/python --cov-report=html

# Run specific test file
poetry run pytest tests/test_tool_schemas.py -v

# Run specific test
poetry run pytest tests/test_tool_schemas.py::TestSearchMemoryToolParams::test_valid_minimal_params
```

### TypeScript Tests

```bash
# Run all tests
cd src/server
npm test

# With coverage
npm run test:coverage

# Watch mode
npm test -- --watch

# Run specific test file
npm test -- PaprMemoryService.test.ts
```

### All Tests

```bash
# Run everything with one script
./scripts/test.sh
```

---

## 📊 Coverage Targets

### Python
- **Minimum:** 80% line coverage
- **Target:** 90%+ line coverage
- **Critical paths:** 100% (search, validation, schema generation)

### TypeScript
- **Minimum:** 75% line coverage
- **Target:** 85%+ line coverage
- **Critical paths:** 100% (PaprMemoryService methods)

---

## 🎯 Test Categories

### Unit Tests (Current)
- **Python:** Tool schemas, Flask endpoints, latency tracking
- **TypeScript:** Service layer, HTTP communication, error handling

### Integration Tests (Phase 6)
- End-to-end search flow (browser → TypeScript → Python → CoreML)
- Message storage and retrieval
- Constellation visualization data flow
- Pipecat audio pipeline

### Performance Tests (Phase 6)
- Latency benchmarks (<100ms target)
- CoreML ANE vs CPU fallback
- Memory usage under load
- Concurrent request handling

---

## 🔧 Configuration Files

### Python: `pyproject.toml`

```toml
[tool.pytest.ini_options]
minversion = "8.0"
addopts = "-ra -q --strict-markers --cov=src/python --cov-report=term-missing --cov-report=html"
testpaths = ["tests"]
```

### TypeScript: `jest.config.js`

```javascript
export default {
  preset: 'ts-jest/presets/default-esm',
  testEnvironment: 'node',
  collectCoverageFrom: ['src/**/*.ts'],
  coverageDirectory: 'coverage',
};
```

---

## 📝 Testing Best Practices

### 1. **Test Organization**
- One test file per source file
- Group related tests in classes (Python) or describe blocks (TypeScript)
- Clear, descriptive test names

### 2. **Mocking Strategy**
- **Python:** Mock PAPR SDK client, environment variables
- **TypeScript:** Use nock for HTTP requests, mock external services
- Never mock internal logic being tested

### 3. **Assertions**
- Test both success and failure cases
- Verify error messages
- Check data structure and types
- Validate latency metrics

### 4. **Coverage Focus**
- Prioritize critical paths (search, validation, storage)
- Test edge cases (empty strings, null values, timeouts)
- Ensure type safety catches errors

---

## 🐛 Testing Gotchas

### Python
1. **Import Path Issues:** Tests must add `src/python` to sys.path
2. **Async Tests:** Use pytest-asyncio for async/await
3. **Flask Testing:** Use test client, not production server
4. **Pydantic Validation:** Some type coercion behavior varies by version

### TypeScript
1. **ESM Modules:** Use jest with ESM preset for .ts files
2. **HTTP Mocking:** nock must be cleaned up after each test
3. **Async Expectations:** Use `await expect(...).rejects.toThrow()`
4. **Type Safety:** Tests also benefit from TypeScript checking

---

## 🎉 Testing Achievements

✅ **Comprehensive Coverage:** Both Python and TypeScript components
✅ **Pydantic Validation:** All tool schema types tested
✅ **API Endpoints:** Every Flask route covered
✅ **Service Layer:** Full HTTP communication testing
✅ **Error Handling:** Timeout, network, and validation errors
✅ **CoreML Optimization:** rank_results=true enforcement verified
✅ **Search History:** Deque size limits tested
✅ **Type Safety:** TypeScript + Pydantic consistency

---

## 📈 Next Steps

### Phase 4-5 Testing
- [ ] Fastify server endpoint tests
- [ ] WebSocket communication tests
- [ ] Pipecat pipeline integration tests
- [ ] End-to-end voice flow tests

### Phase 6 Testing
- [ ] Performance benchmarks
- [ ] Load testing
- [ ] Cross-browser testing
- [ ] CI/CD integration

---

## 🔗 Resources

- [pytest documentation](https://docs.pytest.org/)
- [Jest documentation](https://jestjs.io/)
- [nock HTTP mocking](https://github.com/nock/nock)
- [Poetry documentation](https://python-poetry.org/docs/)
- [Pydantic validation testing](https://docs.pydantic.dev/latest/concepts/validation/)

**Test with confidence! 🚀**
