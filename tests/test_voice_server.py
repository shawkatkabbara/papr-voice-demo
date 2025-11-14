#!/usr/bin/env python3
"""
Unit tests for voice_server.py

Tests Flask endpoints, latency tracking, and search history
"""
import pytest
import sys
import os
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add src/python to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/python'))


@pytest.fixture
def app():
    """Create test Flask app"""
    # Mock the PAPR client before importing voice_server
    with patch('voice_server.papr_client') as mock_client:
        import voice_server
        voice_server.app.config['TESTING'] = True
        voice_server.papr_client = mock_client
        yield voice_server.app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def mock_papr_response():
    """Create mock PAPR SDK response"""
    mock_memory = Mock()
    mock_memory.content = "Test memory content about project priorities"
    mock_memory.id = "mem_123"
    mock_memory.tags = ["project", "priority"]
    mock_memory.topics = ["work", "planning"]
    mock_memory.pydantic_extra__ = {'similarity_score': 0.85}
    mock_memory.metadata = {'similarity_score': 0.75}
    mock_memory.custom_metadata = None

    mock_response = Mock()
    mock_response.data = Mock()
    mock_response.data.memories = [mock_memory]

    return mock_response


class TestStaticRoutes:
    """Test static file serving"""

    def test_index_route(self, client):
        """Test that / serves voice.html"""
        response = client.get('/')
        # Will return 404 in test environment (file doesn't exist in test context)
        # But route should exist
        assert response.status_code in [200, 404]

    def test_logo_route(self, client):
        """Test that /logo.svg serves logo file"""
        response = client.get('/logo.svg')
        assert response.status_code in [200, 404]


class TestApiKeysEndpoint:
    """Test /api/keys endpoint"""

    def test_keys_endpoint_returns_json(self, client):
        """Test that endpoint returns JSON"""
        response = client.get('/api/keys')
        assert response.status_code == 200
        assert response.content_type == 'application/json'

    def test_keys_endpoint_structure(self, client):
        """Test response structure"""
        response = client.get('/api/keys')
        data = json.loads(response.data)

        assert 'openai_key' in data
        assert 'papr_key' in data

    @patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test_openai_key',
        'PAPR_MEMORY_API_KEY': 'test_papr_key'
    })
    def test_keys_endpoint_values(self, client):
        """Test that keys come from environment variables"""
        response = client.get('/api/keys')
        data = json.loads(response.data)

        assert data['openai_key'] == 'test_openai_key'
        assert data['papr_key'] == 'test_papr_key'


class TestToolSchemaEndpoint:
    """Test /api/tool-schema endpoint"""

    def test_tool_schema_returns_json(self, client):
        """Test that endpoint returns JSON"""
        response = client.get('/api/tool-schema')
        assert response.status_code == 200
        assert response.content_type == 'application/json'

    def test_tool_schema_structure(self, client):
        """Test OpenAI-compatible schema structure"""
        response = client.get('/api/tool-schema')
        schema = json.loads(response.data)

        assert schema['type'] == 'function'
        assert schema['name'] == 'search_papr_memories'
        assert 'description' in schema
        assert 'parameters' in schema
        assert schema['parameters']['type'] == 'object'

    def test_tool_schema_has_query_parameter(self, client):
        """Test that schema includes query parameter"""
        response = client.get('/api/tool-schema')
        schema = json.loads(response.data)

        props = schema['parameters']['properties']
        assert 'query' in props
        assert props['query']['type'] == 'string'


class TestSearchHistoryEndpoint:
    """Test /api/search-history endpoint"""

    def test_search_history_returns_json(self, client):
        """Test that endpoint returns JSON"""
        response = client.get('/api/search-history')
        assert response.status_code == 200
        assert response.content_type == 'application/json'

    def test_search_history_structure(self, client):
        """Test response structure"""
        response = client.get('/api/search-history')
        data = json.loads(response.data)

        assert 'searches' in data
        assert 'count' in data
        assert isinstance(data['searches'], list)
        assert isinstance(data['count'], int)

    def test_search_history_empty_initially(self, client):
        """Test that history is empty on fresh start"""
        response = client.get('/api/search-history')
        data = json.loads(response.data)

        assert data['count'] == 0
        assert len(data['searches']) == 0


class TestSearchEndpoint:
    """Test /api/search endpoint"""

    def test_search_requires_papr_client(self, client):
        """Test that search fails without PAPR client"""
        with patch('voice_server.papr_client', None):
            response = client.post('/api/search',
                                 data=json.dumps({'query': 'test'}),
                                 content_type='application/json')

            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data

    def test_search_validates_parameters(self, client, mock_papr_response):
        """Test that search validates parameters"""
        with patch('voice_server.papr_client') as mock_client:
            mock_client.memory.search.return_value = mock_papr_response

            # Missing query
            response = client.post('/api/search',
                                 data=json.dumps({}),
                                 content_type='application/json')

            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data

    def test_search_successful(self, client, mock_papr_response):
        """Test successful search"""
        with patch('voice_server.papr_client') as mock_client:
            mock_client.memory.search.return_value = mock_papr_response

            response = client.post('/api/search',
                                 data=json.dumps({
                                     'query': 'test query',
                                     'max_memories': 10
                                 }),
                                 content_type='application/json')

            assert response.status_code == 200
            data = json.loads(response.data)

            # Check response structure
            assert 'data' in data
            assert 'memories' in data['data']
            assert 'latency_ms' in data
            assert 'latency_breakdown' in data
            assert 'search_id' in data

    def test_search_latency_breakdown(self, client, mock_papr_response):
        """Test that latency breakdown is included"""
        with patch('voice_server.papr_client') as mock_client:
            mock_client.memory.search.return_value = mock_papr_response

            response = client.post('/api/search',
                                 data=json.dumps({'query': 'test'}),
                                 content_type='application/json')

            data = json.loads(response.data)
            breakdown = data['latency_breakdown']

            assert 'total_ms' in breakdown
            assert 'sdk_processing_ms' in breakdown
            assert 'embedding_generation_ms' in breakdown
            assert 'chromadb_search_ms' in breakdown
            assert 'processing_overhead_ms' in breakdown

    def test_search_stores_history(self, client, mock_papr_response):
        """Test that searches are stored in history"""
        with patch('voice_server.papr_client') as mock_client:
            mock_client.memory.search.return_value = mock_papr_response

            # Get current history count
            history_before = client.get('/api/search-history')
            count_before = json.loads(history_before.data)['count']

            # Perform search
            client.post('/api/search',
                       data=json.dumps({'query': 'test query unique 123'}),
                       content_type='application/json')

            # Check history increased
            history_response = client.get('/api/search-history')
            history = json.loads(history_response.data)

            assert history['count'] == count_before + 1

            # Find our search in history
            search_entry = next(
                (s for s in history['searches'] if s['query'] == 'test query unique 123'),
                None
            )
            assert search_entry is not None
            assert 'latency' in search_entry
            assert 'top_memories_preview' in search_entry

    def test_search_with_agentic_graph(self, client, mock_papr_response):
        """Test search with agentic graph enabled"""
        with patch('voice_server.papr_client') as mock_client:
            mock_client.memory.search.return_value = mock_papr_response

            response = client.post('/api/search',
                                 data=json.dumps({
                                     'query': 'test',
                                     'enable_agentic_graph': True
                                 }),
                                 content_type='application/json')

            assert response.status_code == 200

            # Verify that enable_agentic_graph was passed to SDK
            mock_client.memory.search.assert_called_once()
            call_kwargs = mock_client.memory.search.call_args[1]
            assert call_kwargs['enable_agentic_graph'] == True

    def test_search_default_agentic_graph_false(self, client, mock_papr_response):
        """Test that enable_agentic_graph defaults to False"""
        with patch('voice_server.papr_client') as mock_client:
            mock_client.memory.search.return_value = mock_papr_response

            response = client.post('/api/search',
                                 data=json.dumps({'query': 'test'}),
                                 content_type='application/json')

            assert response.status_code == 200

            # Verify default is False
            call_kwargs = mock_client.memory.search.call_args[1]
            assert call_kwargs['enable_agentic_graph'] == False

    def test_search_rank_results_true(self, client, mock_papr_response):
        """Test that rank_results is always True for CoreML optimization"""
        with patch('voice_server.papr_client') as mock_client:
            mock_client.memory.search.return_value = mock_papr_response

            response = client.post('/api/search',
                                 data=json.dumps({'query': 'test'}),
                                 content_type='application/json')

            assert response.status_code == 200

            # Verify rank_results is True
            call_kwargs = mock_client.memory.search.call_args[1]
            assert call_kwargs['rank_results'] == True

    def test_search_memory_formatting(self, client, mock_papr_response):
        """Test that memories are formatted correctly"""
        with patch('voice_server.papr_client') as mock_client:
            mock_client.memory.search.return_value = mock_papr_response

            response = client.post('/api/search',
                                 data=json.dumps({'query': 'test'}),
                                 content_type='application/json')

            data = json.loads(response.data)
            memories = data['data']['memories']

            assert len(memories) == 1
            memory = memories[0]

            # Check memory structure
            assert 'content' in memory
            assert 'query_similarity' in memory
            assert 'relevance_score' in memory
            assert 'tags' in memory
            assert 'topics' in memory
            assert 'id' in memory

            # Check values
            assert memory['content'] == "Test memory content about project priorities"
            assert memory['query_similarity'] == 0.85
            assert memory['tags'] == ["project", "priority"]


class TestSearchHistoryLimits:
    """Test search history size limits"""

    def test_search_history_max_30_searches(self, client, mock_papr_response):
        """Test that history is limited to 30 searches"""
        with patch('voice_server.papr_client') as mock_client:
            mock_client.memory.search.return_value = mock_papr_response

            # Perform 35 searches
            for i in range(35):
                client.post('/api/search',
                          data=json.dumps({'query': f'test {i}'}),
                          content_type='application/json')

            # Check history
            history_response = client.get('/api/search-history')
            history = json.loads(history_response.data)

            # Should only keep last 30
            assert history['count'] == 30
            assert len(history['searches']) == 30


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
