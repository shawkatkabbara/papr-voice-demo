#!/usr/bin/env python3
"""
Unit tests for tool_schemas.py

Tests Pydantic validation and OpenAI schema generation
"""
import pytest
import sys
import os
from pydantic import ValidationError

# Add src/python to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/python'))

from tool_schemas import (
    SearchMemoryToolParams,
    get_search_memory_tool_schema,
    validate_search_params
)


class TestSearchMemoryToolParams:
    """Test Pydantic model for search parameters"""

    def test_valid_minimal_params(self):
        """Test with only required parameter (query)"""
        params = SearchMemoryToolParams(query="test query")

        assert params.query == "test query"
        assert params.enable_agentic_graph == False  # Default value

    def test_valid_full_params(self):
        """Test with all parameters"""
        params = SearchMemoryToolParams(
            query="What are my project priorities?",
            enable_agentic_graph=True
        )

        assert params.query == "What are my project priorities?"
        assert params.enable_agentic_graph == True

    def test_missing_required_query(self):
        """Test that query is required"""
        with pytest.raises(ValidationError) as exc_info:
            SearchMemoryToolParams()

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]['loc'] == ('query',)
        assert errors[0]['type'] == 'missing'

    def test_empty_query_string(self):
        """Test that empty query string is rejected"""
        # Pydantic enforces min_length=1 constraint
        with pytest.raises(ValidationError) as exc_info:
            SearchMemoryToolParams(query="")

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]['type'] == 'string_too_short'

    def test_boolean_coercion(self):
        """Test that enable_agentic_graph coerces to boolean"""
        params = SearchMemoryToolParams(
            query="test",
            enable_agentic_graph=1  # Should coerce to True
        )
        assert params.enable_agentic_graph == True

    def test_default_values(self):
        """Test default values are applied correctly"""
        params = SearchMemoryToolParams(query="test")

        # Check default
        assert params.enable_agentic_graph == False


class TestGetSearchMemoryToolSchema:
    """Test OpenAI-compatible schema generation"""

    def test_schema_structure(self):
        """Test that schema has correct structure"""
        schema = get_search_memory_tool_schema()

        # Check top-level structure
        assert schema['type'] == 'function'
        assert schema['name'] == 'search_papr_memories'
        assert 'description' in schema
        assert 'parameters' in schema

        # Check parameters structure
        params = schema['parameters']
        assert params['type'] == 'object'
        assert 'properties' in params
        assert 'required' in params

    def test_schema_properties(self):
        """Test that schema properties match Pydantic model"""
        schema = get_search_memory_tool_schema()
        props = schema['parameters']['properties']

        # Check query property
        assert 'query' in props
        assert props['query']['type'] == 'string'
        assert 'description' in props['query']

        # Check enable_agentic_graph property
        assert 'enable_agentic_graph' in props
        # Pydantic v2 may use anyOf for optional booleans
        if 'type' in props['enable_agentic_graph']:
            assert props['enable_agentic_graph']['type'] == 'boolean'
        assert 'description' in props['enable_agentic_graph']
        assert props['enable_agentic_graph']['default'] == False

    def test_schema_required_fields(self):
        """Test that required fields are correctly marked"""
        schema = get_search_memory_tool_schema()
        required = schema['parameters']['required']

        assert 'query' in required
        assert 'enable_agentic_graph' not in required  # Optional

    def test_schema_descriptions(self):
        """Test that descriptions are informative"""
        schema = get_search_memory_tool_schema()

        # Check function description
        assert 'semantic search' in schema['description'].lower()

        # Check query description
        query_desc = schema['parameters']['properties']['query']['description']
        assert len(query_desc) > 50  # Should be detailed
        assert '2-3 sentences' in query_desc.lower()


class TestValidateSearchParams:
    """Test parameter validation function"""

    def test_validate_valid_params(self):
        """Test validation of valid parameters"""
        params = {
            'query': 'What are my current tasks?',
            'enable_agentic_graph': True
        }

        validated = validate_search_params(params)

        assert isinstance(validated, SearchMemoryToolParams)
        assert validated.query == 'What are my current tasks?'
        assert validated.enable_agentic_graph == True

    def test_validate_minimal_params(self):
        """Test validation with only required params"""
        params = {'query': 'test'}

        validated = validate_search_params(params)

        assert validated.query == 'test'
        assert validated.enable_agentic_graph == False

    def test_validate_missing_query(self):
        """Test validation fails without query"""
        params = {'enable_agentic_graph': True}

        with pytest.raises(ValidationError):
            validate_search_params(params)

    def test_validate_extra_fields_ignored(self):
        """Test that extra fields are ignored"""
        params = {
            'query': 'test',
            'extra_field': 'should be ignored'
        }

        # Should not raise error, extra fields ignored by Pydantic
        validated = validate_search_params(params)
        assert validated.query == 'test'

    def test_validate_type_coercion(self):
        """Test that Pydantic coerces string 'true' to boolean True"""
        params = {
            'query': 'test',
            'enable_agentic_graph': 'true'  # String "true"
        }

        # Pydantic v2 coerces 'true' string to True boolean
        validated = validate_search_params(params)
        assert validated.enable_agentic_graph == True


class TestSchemaConsistency:
    """Test consistency between Pydantic model and OpenAI schema"""

    def test_model_and_schema_field_alignment(self):
        """Test that Pydantic model fields match schema properties"""
        schema = get_search_memory_tool_schema()

        # Create instance to get model fields
        params = SearchMemoryToolParams(query="test")
        model_fields = set(params.model_dump().keys())
        schema_props = set(schema['parameters']['properties'].keys())

        assert model_fields == schema_props

    def test_defaults_match(self):
        """Test that default values match between model and schema"""
        schema = get_search_memory_tool_schema()
        params = SearchMemoryToolParams(query="test")

        # Check enable_agentic_graph default
        assert (
            params.enable_agentic_graph ==
            schema['parameters']['properties']['enable_agentic_graph']['default']
        )


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
